import os
import pwd
import shutil
import subprocess
from tempfile import TemporaryDirectory
from jupyterhub_singleuser_inithooks import InitHooks
from pathlib import Path

HERE = Path(__file__).parent


def test_hook_discovery():
    app = InitHooks()

    assert app.get_executable_files(HERE / "test-dirs/non-executable") == [
        Path(HERE / "test-dirs/non-executable/an-executable.sh")
    ]


def test_hook_ordering():
    app = InitHooks()

    assert app.get_executable_files(HERE / "test-dirs/hook-ordering") == [
        Path(HERE / "test-dirs/hook-ordering/01-first.sh"),
        Path(HERE / "test-dirs/hook-ordering/02-second.sh")
    ]


def test_hook_exec():
    """
    Test the command gets executed properly with correct uid

    This test *must* be run as root.
    """
    with TemporaryDirectory() as d:
        cur_uid = os.environ['SUDO_UID']
        cur_gid = os.environ['SUDO_GID']

        os.chown(d, int(cur_uid), int(cur_gid))

        cmd = [
            shutil.which('jupyterhub-singleuser-inithooks'),
            '--hooks-dir',str(HERE / 'test-dirs/simple-hooks'),
            '--uid', str(cur_uid), '--gid', str(cur_gid),
            '--',
             '/bin/bash', '-c', 'id -u > ${TEST_HARNESS_DIR}/uid && id -g > ${TEST_HARNESS_DIR}/gid'
        ]
        env = os.environ.copy()
        env['TEST_HARNESS_DIR'] = d
        assert subprocess.check_call(cmd, env=env) == 0

        # 01-first.sh writes out 'hi'
        # 02-second.py writes out 'hello'
        hi_path = Path(d) / 'hi'
        hello_path = Path(d) / 'hello'

        assert hi_path.owner() == pwd.getpwuid(os.getuid()).pw_name
        assert hello_path.owner() == pwd.getpwuid(os.geteuid()).pw_name
        with open(hi_path) as hi, open(hello_path) as hello, open(Path(d) / 'hello') as hello, open(Path(d) / 'uid') as uid, open(Path(d) / 'gid') as gid:
            assert hi.read() == 'hi'
            assert hello.read() == 'hello'
            assert uid.read().strip() == str(cur_uid)
            assert gid.read().strip() == str(cur_gid)

def test_hook_exec_stub(mocker):
    """
    Version of test_hook_exec that mocks the privilege dropping
    """
    with TemporaryDirectory() as d:
        app = InitHooks()
        app.hooks_dir = str(HERE / 'test-dirs/simple-hooks')
        app.uid = 1000
        app.gid = 1000

        cmd = [
             '/bin/bash', '-c', 'id -u > ${TEST_HARNESS_DIR}/uid && id -g > ${TEST_HARNESS_DIR}/gid'
        ]

        mocker.patch('os.setuid')
        mocker.patch('os.setgid')
        mocker.patch('os.setgroups')
        mocker.patch('os.execvp')

        os.environ['TEST_HARNESS_DIR'] = d
        try:
            app.start(['--'] + cmd)
        finally:
            del os.environ['TEST_HARNESS_DIR']

        os.setuid.assert_called_once_with(1000)
        os.setgid.assert_called_once_with(1000)
        os.setgroups.assert_called_once_with([])
        os.execvp.assert_called_once_with(cmd[0], cmd)

        # 01-first.sh writes out 'hi'
        # 02-second.py writes out 'hello'
        hi_path = Path(d) / 'hi'
        hello_path = Path(d) / 'hello'

        assert hi_path.owner() == pwd.getpwuid(os.getuid()).pw_name
        assert hello_path.owner() == pwd.getpwuid(os.geteuid()).pw_name
        with open(hi_path) as hi, open(hello_path) as hello, open(Path(d) / 'hello') as hello:
            assert hi.read() == 'hi'
            assert hello.read() == 'hello'