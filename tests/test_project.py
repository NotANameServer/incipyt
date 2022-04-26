import os
import sys

from pytest import fixture, mark, raises

from incipyt import project, commands
from incipyt._internal.dumpers import TextFile, Toml
from incipyt._internal.templates import StringTemplate

from tests.utils import mock_stdin


class TestEnviron:
    @fixture
    def empty_environ(self, fake_process):
        fake_process.register_subprocess(["cmd", "arg"], stdout=["lineA", "lineB"])
        project.environ.clear()

    @fixture
    def simple_environ(self, fake_process):
        fake_process.register_subprocess(["cmd", "arg"], stdout=["lineA", "lineB"])
        project.environ.clear()
        project.environ["ONE"] = project.EnvValue("1", confirmed=True)

    @fixture
    def empty_auto_env(self, fake_process):
        fake_process.register_subprocess(["cmd", "arg"], stdout=["lineA", "lineB"])
        project.environ.clear()

    @fixture
    def simple_auto_env(self, fake_process):
        fake_process.register_subprocess(["cmd", "arg"], stdout=["lineA", "lineB"])
        project.environ.clear()
        project.environ["ONE"] = project.EnvValue("1", confirmed=True)

    @mark.parametrize(
        "env, input_values",
        (
            ("empty_environ", ["1"]),
            ("simple_environ", [""]),
            ("empty_auto_env", ["1"]),
            ("simple_auto_env", []),
        ),
    )
    def test_pull(self, env, input_values, monkeypatch, request):
        request.getfixturevalue(env)
        mock_stdin(monkeypatch, input_values)
        assert project.environ["ONE"] == "1"

    @mark.parametrize(
        "env",
        (
            "simple_environ",
            "simple_auto_env",
        ),
    )
    def test_push(self, env, request):
        request.getfixturevalue(env)
        with raises(ValueError):
            project.environ["ONE"] = "11"

    @mark.parametrize(
        "env, input_values",
        (
            ("simple_environ", [""]),
            ("simple_auto_env", []),
        ),
    )
    def test_update(self, env, input_values, monkeypatch, request):
        request.getfixturevalue(env)
        project.environ["ONE"] = project.EnvValue("11", update=True)
        mock_stdin(monkeypatch, input_values)
        assert project.environ["ONE"] == "11"

    @mark.parametrize(
        "env",
        (
            "empty_environ",
            "empty_auto_env",
        ),
    )
    def test_confirmed(self, env, request):
        request.getfixturevalue(env)
        project.environ["ONE"] = project.EnvValue("1", confirmed=True)
        assert project.environ["ONE"] == "1"

    @mark.parametrize(
        "env",
        (
            "empty_environ",
            "simple_environ",
            "empty_auto_env",
            "simple_auto_env",
        ),
    )
    def test_python_cmd(self, env, request):
        request.getfixturevalue(env)
        assert project.environ["PYTHON_CMD"] == sys.executable

    @mark.parametrize(
        "env",
        (
            "empty_environ",
            "empty_auto_env",
        ),
    )
    def test_iter(self, env, request):
        request.getfixturevalue(env)
        project.environ["TWO"] = project.EnvValue("2", confirmed=True)
        result = {key: project.environ[key] for key in project.environ}
        assert result == {"PYTHON_CMD": sys.executable, "TWO": "2"}

    @mark.parametrize(
        "env",
        (
            "empty_environ",
            "simple_environ",
            "empty_auto_env",
            "simple_auto_env",
        ),
    )
    def test_run(self, env, request):
        request.getfixturevalue(env)
        result = commands.run(["cmd", "arg"])
        assert result.stdout.decode() == f"lineA{os.linesep}lineB{os.linesep}"


class TestStructure:
    @fixture
    def reset_environ(self, fake_process):
        fake_process.register_subprocess(["cmd", "arg"], stdout=["lineA", "lineB"])
        project.environ.clear()
        project.environ["FOLDER_A"] = project.EnvValue("folderA", confirmed=True)
        project.environ["FOLDER_B"] = project.EnvValue("folderB", confirmed=True)
        project.environ["NAME_A"] = project.EnvValue("testA", confirmed=True)
        project.environ["NAME_B"] = project.EnvValue("testB", confirmed=True)
        project.environ["VALUE"] = project.EnvValue("1", confirmed=True)
        project.environ["CONTENT"] = project.EnvValue("text", confirmed=True)

    @fixture
    def reset_structure(self):
        project.structure.clear()
        project.structure.get_config_dict(Toml("{FOLDER_A}/{NAME_A}.toml"))[
            "section"
        ] = {"first": "{VALUE}"}
        project.structure.get_config_list(
            TextFile("{FOLDER_B}/{NAME_B}", sep="\n\n")
        ).append("{CONTENT}")

    def test_get_new_configuration(self, reset_structure):
        configuration = project.structure.get_config_dict(Toml("testC.toml"))
        assert configuration == {}

    def test_get_old_configuration(self, reset_structure):
        configuration = project.structure.get_config_dict(
            Toml("{FOLDER_A}/{NAME_A}.toml")
        )
        assert configuration == {"section": {"first": StringTemplate("{VALUE}")}}

    def test_mkdir(self, reset_structure, reset_environ, tmp_path):
        project.structure.mkdir(tmp_path)
        assert (tmp_path / "folderA").is_dir()
        assert (tmp_path / "folderB").is_dir()

    def test_commit(self, reset_structure, reset_environ, tmp_path):
        project.structure.mkdir(tmp_path)
        project.structure.commit()
        assert (
            tmp_path / "folderA" / "testA.toml"
        ).read_text() == '[section]\nfirst = "1"\n'
        assert (tmp_path / "folderB" / "testB").read_text() == "text\n\n"
