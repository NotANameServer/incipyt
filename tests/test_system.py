import sys

from pytest import fixture, mark, raises

from incipyt.system import Environment, EnvValue
from tests.utils import mock_stdin


class TestEnvironment:
    @staticmethod
    def runner(command):
        return " ".join(command)

    @fixture
    def empty_env(self):
        return Environment(runner=TestEnvironment.runner)

    @fixture
    def simple_env(self):
        env = Environment(runner=TestEnvironment.runner)
        env["ONE"] = "1"
        return env

    @fixture
    def empty_auto_env(self):
        return Environment(auto_confirm=True, runner=TestEnvironment.runner)

    @fixture
    def simple_auto_env(self):
        env = Environment(auto_confirm=True, runner=TestEnvironment.runner)
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
