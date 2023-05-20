import os
import sys
from datetime import date

from pytest import fixture, mark, raises

from incipyt import commands, project
from incipyt.__main__ import feed_environ
from incipyt._internal.dumpers import TextFile, Toml
from incipyt._internal.templates import StringTemplate
from incipyt.project.meta_variables import Variable
from tests.utils import mock_stdin

YEAR = date.today().year


class TestEnviron:
    @fixture(scope="function")
    def patch_variables(self):
        try:
            variables = project.variables.copy()

            Variable("ONE")
            Variable("TWO")

            feed_environ()

            yield

        finally:
            project.variables.update(variables)

    @fixture
    def empty_environ(self, fake_process, patch_variables):
        fake_process.register_subprocess(["cmd", "arg"], stdout=["lineA", "lineB"])

    @fixture
    def simple_environ(self, fake_process, patch_variables):
        fake_process.register_subprocess(["cmd", "arg"], stdout=["lineA", "lineB"])
        project.environ["ONE"] = "1"

    @mark.parametrize("env, input_values", (("empty_environ", ["1"]), ("simple_environ", [""])))
    def test_pull(self, env, input_values, monkeypatch, request):
        request.getfixturevalue(env)
        mock_stdin(monkeypatch, input_values)
        assert project.environ["ONE"] == "1"

    @mark.parametrize("env", ("simple_environ",))
    def test_push(self, env, request):
        request.getfixturevalue(env)
        with raises(ValueError):
            project.environ["ONE"] = "11"

    @mark.parametrize("env, input_values", (("simple_environ", [""]),))
    def test_del_and_push(self, env, input_values, monkeypatch, request):
        request.getfixturevalue(env)
        del project.environ["ONE"]
        project.environ["ONE"] = "11"
        mock_stdin(monkeypatch, input_values)
        assert project.environ["ONE"] == "11"

    @mark.parametrize("env", ("empty_environ", "simple_environ"))
    def test_python_cmd(self, env, request):
        request.getfixturevalue(env)
        assert project.environ["PYTHON_CMD"] == sys.executable

    @mark.parametrize("env", ("empty_environ",))
    def test_iter(self, env, request):
        request.getfixturevalue(env)
        project.environ["TWO"] = "2"
        result = {key: project.environ[key] for key in project.environ}
        assert result == {"TWO": "2"}

    @mark.parametrize("env", ("empty_environ", "simple_environ"))
    def test_run(self, env, request):
        request.getfixturevalue(env)
        result = commands.run(["cmd", "arg"])
        assert result.stdout.decode() == f"lineA{os.linesep}lineB{os.linesep}"


class TestStructure:
    @fixture
    def reset_environ(self, fake_process):
        fake_process.register_subprocess(["cmd", "arg"], stdout=["lineA", "lineB"])
        feed_environ()
        project.environ["FOLDER_A"] = "folderA"
        project.environ["FOLDER_B"] = "folderB"
        project.environ["NAME_A"] = "testA"
        project.environ["NAME_B"] = "testB"
        project.environ["VALUE"] = "1"
        project.environ["CONTENT"] = "text"

    @fixture
    def reset_structure(self):
        project.structure.clear()
        project.structure.get_config_dict(Toml("{FOLDER_A}/{NAME_A}.toml"))["section"] = {
            "first": "{VALUE}"
        }
        project.structure.get_config_list(TextFile("{FOLDER_B}/{NAME_B}", sep="\n\n")).append(
            "{CONTENT}"
        )

    def test_get_new_configuration(self, reset_structure):
        configuration = project.structure.get_config_dict(Toml("testC.toml"))
        assert configuration == {}

    def test_get_old_configuration(self, reset_structure):
        configuration = project.structure.get_config_dict(Toml("{FOLDER_A}/{NAME_A}.toml"))
        assert configuration == {"section": {"first": StringTemplate("{VALUE}")}}

    def test_mkdir(self, reset_structure, reset_environ, tmp_path):
        project.structure.mkdir(tmp_path)
        assert (tmp_path / "folderA").is_dir()
        assert (tmp_path / "folderB").is_dir()

    def test_commit(self, reset_structure, reset_environ, tmp_path):
        project.structure.mkdir(tmp_path)
        project.structure.commit()
        assert (tmp_path / "folderA" / "testA.toml").read_text() == '[section]\nfirst = "1"\n'
        assert (tmp_path / "folderB" / "testB").read_text() == "text\n\n"
