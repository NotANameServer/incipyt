import filecmp
import os
import pathlib
import shutil
import sys

from tests.test_tools import testing

from incipyt import __main__
from incipyt.tools.setuptools import LINUX_MIN_PYTHON_VERSION


def make_archive():
    runner = testing.IncipytRunner()
    root_dir = pathlib.Path(__file__).parent
    with runner.isolated_filesystem() as td:
        runner.invoke(__main__.main, ["--vcs=", "--check-build", "my_project"])
        os.chdir(root_dir)
        os.remove("setuptools.tar.gz")
        shutil.make_archive("setuptools", "gztar", root_dir=td, base_dir="my_project")


def test_integration(tmp_path):
    runner = testing.IncipytRunner(
        default_mapping={
            r"Audience python version": "{0[0]}.{0[1]}".format(  # noqa: FS002
                min(sys.version_info, LINUX_MIN_PYTHON_VERSION)
            ),
        }
    )
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(__main__.main, ["--vcs=", "--check-build", "my_project"])
        shutil.unpack_archive(
            pathlib.Path(__file__).parent / "setuptools.tar.gz", "archive"
        )
        diff = testing.diff_files(
            filecmp.dircmp("my_project", pathlib.Path("archive/my_project"))
        )

    assert diff == set()
    assert not result.exception
    assert result.exit_code == 0
