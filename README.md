# jupyterhub-roothooks

![Tests passing](https://github.com/yuvipanda/jupyterhub-roothooks/actions/workflows/unit-test.yaml/badge.svg)
[![codecov](https://codecov.io/gh/yuvipanda/jupyterhub-roothooks/branch/main/graph/badge.svg?token=DFIJ7NAR0W)](https://codecov.io/gh/yuvipanda/jupyterhub-roothooks)
[![PyPI version](https://badge.fury.io/py/jupyterhub-roothooks.svg)](https://badge.fury.io/py/jupyterhub-roothooks)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/yuvipanda/jupyterhub-roothooks/main.svg)](https://results.pre-commit.ci/latest/github/yuvipanda/jupyterhub-roothooks/main)

Run hooks as root before starting user server.

## Why?

When running [JupyterHub on Kubernetes](https://z2jh.jupyter.org), you want user pods to
run as non-root users. This is good security practice, and can seriously reduce blast
radius in case of compromised. For example, if you run your containers with `privileged: True`,
a compromise of a user server will likely be able to take control of your entire kubernetes
cluster, and depending on how it's configured, your cloud account! Nobody wants that.

However, what people *do* want is to be able to run some commands as root *before* the
user server starts. Often, this is to do some [mounting](https://github.com/pangeo-data/pangeo/issues/190)
stuff, although there are other use cases too.

So the goal would be to:

1. Run some commands as root *before* the user server starts
2. These commands failing should *not* cause the server to not start. This mostly shows
   the user a useless 'your server has failed to start' error. In most cases, it is
   better to start the server and provide some logging so the user can investigate what
   went wrong.

`jupyterhub-roothooks` is designed to solve this very specific problem.

## How?

### Prepare the image: With repo2docker

[repo2docker](https://repo2docker.readthedocs.io) is a common way to build images for
use with JupyterHub, so `jupyterhub-roothooks` specifies some defaults that make it
easy to integrate with repo2docker.

1. Install `jupyterhub-roothooks` into your container, by adding it to your `requirements.txt`
   file or under `pip:` in your `environment.yml` file.
2. Add a `roothooks.d` directory to your repo.
3. Add scripts you want executed as root inside the `roothooks.d` directory. These will
   be executed in *sorted order*, so you can clarify the ordering by prefixing them with
   numbers like `01-first-script.sh`, `02-second-script.sh`.
4. Make sure these scripts are marked as executable (with `chmod +x <script-name>`), and
   have an appropriate [shebang](https://en.wikipedia.org/wiki/Shebang_(Unix)).
5. Add a `start` script that looks like this:

   ```bash
   #!/bin/bash -l
   exec jupyterhub-roothooks --uid 1000 --gid 1000 -- "$@"
   ```

   This will start `jupyterhub-roothooks`, which will execute any executable scripts it
   finds in `roothooks.d`, and then run the appropriate command to start the user server
   (passed in via `$@`) with the non-root uid 1000 and gid 1000.

### z2jh configuration

Now that the image is prepared, you can grant elevated root capabilities to the user pod
via z2jh config. Note that while the container will have these capabilities, the user
server itself will not. `jupyterhub-roothooks` will drop these capabilities before starting
the user server.

```yaml
hub:
    config:
        KubeSpawner:
            container_security_context:
                # Run the container *truly* as privileged. This can be very dangerous,
                # but is required for doing most filesystem mounts
                privileged: true
                runAsUser: 0
                allowPrivilegeEscalation: true
                capabilities:
                    add:
                    - SYS_ADMIN
```
