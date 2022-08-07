import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import List

from traitlets import Integer, Unicode, default
from traitlets.config import Application


class InitHooks(Application):
    aliases = {
        "hooks-dir": "InitHooks.hooks_dir",
        "uid": "InitHooks.uid",
        "gid": "InitHooks.gid",
    }

    log_level = logging.INFO
    hooks_dir = Unicode(
        "",
        config=True,
        help="""
        Directory with hooks to be executed.

        Files marked executable within this directory will be
        executed sequentially in sorted order.
        """,
    )

    @default("hooks_dir")
    def _hooks_dir_default(self):
        if "REPO_DIR" in os.environ:
            return f"{os.environ['REPO_DIR']}/inithooks.d"

    hook_timeout = Integer(
        5,
        config=True,
        help="""
        Time each hook is allowed to execute before it's killed.
        """,
    )

    uid = Integer(
        os.environ.get("NB_UID", 1000),
        config=True,
        help="""
        Uid to switch to before executing command.
        """,
    )

    gid = Integer(
        os.environ.get("NB_UID", 1000),
        config=True,
        help="""
        Gid to switch to before executing command.
        """,
    )

    def get_executable_files(self, path: Path):
        """
        Return sorted list of files marked executable in given path
        """
        return sorted(
            f for f in path.iterdir() if f.is_file() and os.access(f, os.X_OK)
        )

    def exec_process(self, cmd: List, timeout: int):
        """
        Run given process with given timeout
        """
        proc = subprocess.Popen(cmd)
        try:
            proc.wait(timeout)
            return proc.returncode
        except subprocess.TimeoutExpired:
            # Process didn't complete within timeout
            # So send it SIGTERM, and wait for 1s to terminate
            # If it isn't done by then, SIGKILL it
            proc.terminate()
            try:
                proc.wait(timeout=1)
                return proc.returncode
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
                return proc.returncode

    def get_exec_command(self, argv):
        """
        Parse the command to be executed out of argv.

        The command is required to be after '--'
        """
        if "--" not in argv:
            raise ValueError("Must specify command to execute after --")
        return argv[argv.index("--") + 1 :]

    def start(self, argv=None):
        self.parse_command_line(argv)

        hooks = self.get_executable_files(Path(self.hooks_dir))

        for h in hooks:
            print(f"executing {h}")
            ret = self.exec_process([h], self.hook_timeout)
            self.log.info(f"Hook {h} finished with exit code {ret}")

        if argv is None:
            argv = sys.argv
        command = self.get_exec_command(argv)

        # Drop all privileges
        os.setgroups([])
        os.setgid(self.gid)
        # Drop uid last, because if we drop it first we can no longer drop gid or groups lol
        os.setuid(self.uid)

        os.execvp(command[0], command)


def main():
    app = InitHooks()
    app.start()


if __name__ == "__main__":
    main()
