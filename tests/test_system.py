import sys

from pytest import fixture, mark, raises

from incipyt.system import Environment, EnvValue, Hierarchy
from incipyt._internal.dumpers import Jinja, Toml
from incipyt._internal.templates import Requires

from jinja2 import Template

from tests.utils import mock_stdin


class TestEnvironment:
    @fixture
    def empty_env(self, fake_process):
        fake_process.register_subprocess(["cmd", "arg"], stdout=["lineA", "lineB"])
        return Environment()

    @fixture
    def simple_env(self, fake_process):
        fake_process.register_subprocess(["cmd", "arg"], stdout=["lineA", "lineB"])
        env = Environment()
        env["ONE"] = "1"
        return env

    @fixture
    def empty_auto_env(self, fake_process):
        fake_process.register_subprocess(["cmd", "arg"], stdout=["lineA", "lineB"])
        return Environment(auto_confirm=True)

    @fixture
    def simple_auto_env(self, fake_process):
        fake_process.register_subprocess(["cmd", "arg"], stdout=["lineA", "lineB"])
        env = Environment(auto_confirm=True)
        env["ONE"] = "1"
        return env

    @mark.parametrize(
        "env, input_values",
        (
            ("empty_env", ["1"]),
            ("simple_env", [""]),
            ("empty_auto_env", ["1"]),
            ("simple_auto_env", []),
        ),
    )
    def test_pull(self, env, input_values, monkeypatch, request):
        env = request.getfixturevalue(env)
        mock_stdin(monkeypatch, input_values)
        assert env["ONE"] == "1"

    @mark.parametrize(
        "env",
        (
            "simple_env",
            "simple_auto_env",
        ),
    )
    def test_push(self, env, request):
        env = request.getfixturevalue(env)
        with raises(RuntimeError):
            env["ONE"] = "11"

    @mark.parametrize(
        "env, input_values",
        (
            ("simple_env", [""]),
            ("simple_auto_env", []),
        ),
    )
    def test_update(self, env, input_values, monkeypatch, request):
        env = request.getfixturevalue(env)
        env["ONE"] = EnvValue("11", update=True)
        mock_stdin(monkeypatch, input_values)
        assert env["ONE"] == "11"

    @mark.parametrize(
        "env",
        (
            "empty_env",
            "empty_auto_env",
        ),
    )
    def test_confirmed(self, env, request):
        env = request.getfixturevalue(env)
        env["ONE"] = EnvValue("1", confirmed=True)
        assert env["ONE"] == "1"

    @mark.parametrize(
        "env",
        (
            "empty_env",
            "simple_env",
            "empty_auto_env",
            "simple_auto_env",
        ),
    )
    def test_python_cmd(self, env, request):
        env = request.getfixturevalue(env)
        assert env[env.python.variable] == sys.executable

    @mark.parametrize(
        "env",
        (
            "empty_env",
            "simple_env",
            "empty_auto_env",
            "simple_auto_env",
        ),
    )
    def test_iter(self, env, request):
        env = request.getfixturevalue(env)
        env["TWO"] = EnvValue("2", confirmed=True)
        result = {key: env[key] for key in env}
        assert result == {env.python.variable: sys.executable, "TWO": "2"}

    @mark.parametrize(
        "env",
        (
            "empty_env",
            "simple_env",
            "empty_auto_env",
            "simple_auto_env",
        ),
    )
    def test_run(self, env, fake_process, request):
        env = request.getfixturevalue(env)
        result = env.run(["cmd", "arg"])
        assert result == "lineA\nlineB\n"


class TestHierarchy:
    @fixture
    def env(self, fake_process):
        fake_process.register_subprocess(["cmd", "arg"], stdout=["lineA", "lineB"])
        env = Environment()
        env["FOLDER_A"] = EnvValue("folderA", confirmed=True)
        env["FOLDER_B"] = EnvValue("folderB", confirmed=True)
        env["NAME_A"] = EnvValue("testA", confirmed=True)
        env["NAME_B"] = EnvValue("testB", confirmed=True)
        env["VALUE"] = EnvValue("1", confirmed=True)
        env["CONTENT"] = EnvValue("text", confirmed=True)
        return env

    @fixture
    def hierarchy(self):
        hierarchy = Hierarchy()
        conf = hierarchy.get_configuration(Toml("{FOLDER_A}/{NAME_A}.toml"))
        conf["section"] = {"first": "{VALUE}"}
        hierarchy.register_template(
            Jinja("{FOLDER_B}/{NAME_B}"),
            Template("{{CONTENT}}\n"),
        )
        return hierarchy

    def test_get_new_configuration(self, hierarchy):
        configuration = hierarchy.get_configuration(Toml("testC.toml"))
        assert configuration == {}

    def test_get_old_configuration(self, hierarchy):
        configuration = hierarchy.get_configuration(Toml("{FOLDER_A}/{NAME_A}.toml"))
        assert configuration == {"section": {"first": Requires("{VALUE}")}}

    def test_mkdir(self, hierarchy, env, tmp_path):
        hierarchy.mkdir(tmp_path, env)
        assert (tmp_path / "folderA").is_dir()
        assert (tmp_path / "folderB").is_dir()

    def test_commit(self, hierarchy, env, tmp_path):
        hierarchy.mkdir(tmp_path, env)
        hierarchy.commit(env)
        assert (
            tmp_path / "folderA" / "testA.toml"
        ).read_text() == '[section]\nfirst = "1"\n'
        assert (tmp_path / "folderB" / "testB").read_text() == "text"
