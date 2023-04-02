import filecmp
import os
import pathlib
import shutil

from tests.test_tools import testing

from incipyt import __main__


def make_archive():
    runner = testing.IncipytRunner()
    root_dir = pathlib.Path(__file__).parent
    with runner.isolated_filesystem() as td:
        runner.invoke(__main__.main, ["--vcs=git", "--force-vcs-config", "my_project"])
        os.chdir(root_dir)
        os.remove("git.tar.gz")
        shutil.make_archive("git", "gztar", root_dir=td, base_dir="my_project")


def test_integration(tmp_path):
    runner = testing.IncipytRunner(input_mapping={r"Repository": ""})
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            __main__.main, ["--vcs=git", "--force-vcs-config", "my_project"]
        )
        shutil.unpack_archive(pathlib.Path(__file__).parent / "git.tar.gz", "archive")
        diff = testing.diff_files(
            filecmp.dircmp("my_project", pathlib.Path("archive/my_project"))
        )

    assert diff == set()
    assert not result.exception
    assert result.exit_code == 0
