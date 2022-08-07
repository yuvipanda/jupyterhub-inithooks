import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from jupyterhub_singleuser_inithooks import InitHooks

def test_simple():
    app = InitHooks()
    with TemporaryDirectory() as d:
        retcode = app.exec_process([
            '/bin/bash', '-c',
            f'echo -n hi > {d}/hi'
        ], timeout=1)
        assert retcode == 0
        with open(Path(d) / 'hi') as f:
            assert f.read() == 'hi'


def test_sigterm():
    app = InitHooks()
    retcode = app.exec_process([
        '/bin/bash', '-c',
        'sleep 5'
    ], timeout=1)
    # This should just be SIGTERM'd, and so retcode should be -15
    # As SIGTERM is 15
    assert retcode == -15


def test_sigkill():
    app = InitHooks()
    retcode = app.exec_process([
        '/bin/bash', '-c',
        # This traps SIGTERM and does nothing, so this process would need to be killed by SIGKILL
        "trap 'echo do-nothing' SIGTERM; sleep 5"
    ], timeout=1)

    assert retcode == -9

def test_exec_command():
    app = InitHooks()

    assert app.get_exec_command(['--SomeConfig', 'Something', '--', 'some-command', 'some-args']) == [
        'some-command', 'some-args'
    ]


def test_exec_command_missing():
    app = InitHooks()

    with pytest.raises(ValueError):
        app.get_exec_command(['--SomeConfig', 'Something'])