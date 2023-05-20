from collections import abc

from pytest import fixture, mark

from incipyt import project
from incipyt.__main__ import feed_environ
from incipyt._internal.templates import FormatterEnviron
from incipyt.project.meta_variables import Variable
from tests.utils import mock_stdin


@fixture(scope="function")
def patch_variables():
    try:
        variables = project.variables.copy()
        project.variables.clear()

        def patch(env_vars=None, required=False):
            env_vars = env_vars or []
            if isinstance(env_vars, abc.Mapping):
                for key, value in env_vars.items():
                    Variable(key, default=value, required=required)
            else:
                for key in env_vars:
                    Variable(key, required=required)
            feed_environ()

        yield patch

    finally:
        project.variables.update(variables)


class _Context:
    @fixture
    def environ_ctx(self, patch_variables):
        patch_variables(["EMPTY_VARIABLE", "OTHER_VARIABLE", "VARIABLE_NAME"])
        project.environ["VARIABLE_NAME"] = "value"
        return FormatterEnviron()

    @fixture
    def empty_ctx(self, patch_variables):
        patch_variables(["VARIABLE_NAME"])
        return FormatterEnviron()

    @fixture
    def default_ctx(self, patch_variables):
        patch_variables({"VARIABLE_NAME": "value"})
        return FormatterEnviron()

    @fixture
    def required_ctx(self, patch_variables):
        patch_variables(["VARIABLE_NAME"], required=True)
        return FormatterEnviron()


class TestFormatterEnviron(_Context):
    @mark.parametrize(
        "ctx, input_values",
        (
            ("environ_ctx", []),
            ("empty_ctx", ["value"]),
            ("default_ctx", [""]),
            ("required_ctx", ["value"]),
        ),
    )
    def test_contains(self, ctx, input_values, monkeypatch, request):
        ctx = request.getfixturevalue(ctx)
        mock_stdin(monkeypatch, input_values)
        ctx.format("{VARIABLE_NAME}")
        assert "VARIABLE_NAME" in ctx

    @mark.parametrize(
        "ctx, input_values",
        (
            ("environ_ctx", []),
            ("empty_ctx", ["value"]),
            ("default_ctx", [""]),
            ("required_ctx", ["value"]),
        ),
    )
    def test_getitem(self, ctx, input_values, monkeypatch, request):
        ctx = request.getfixturevalue(ctx)
        mock_stdin(monkeypatch, input_values)
        ctx.format("{VARIABLE_NAME}")
        assert ctx["VARIABLE_NAME"] == "value"

    @mark.parametrize("ctx, res", (("empty_ctx", None), ("default_ctx", "value")))
    def test_getitem_empty(self, ctx, res, monkeypatch, request):
        ctx = request.getfixturevalue(ctx)
        mock_stdin(monkeypatch, "")
        ctx.format("{VARIABLE_NAME}")
        assert ctx["VARIABLE_NAME"] == res

    @mark.parametrize(
        "ctx, input_values",
        (
            ("environ_ctx", []),
            ("empty_ctx", ["value"]),
            ("default_ctx", [""]),
            ("required_ctx", ["value"]),
        ),
    )
    def test_getitem_sanitized(self, ctx, input_values, monkeypatch, request):
        ctx = request.getfixturevalue(ctx)
        mock_stdin(monkeypatch, input_values)
        ctx._sanitizer = lambda k, v: v.upper()
        ctx.format("{VARIABLE_NAME}")
        assert ctx["VARIABLE_NAME"] == "VALUE"

    @mark.parametrize(
        "ctx, input_values",
        (
            ("environ_ctx", []),
            ("empty_ctx", ["value"]),
            ("default_ctx", [""]),
            ("required_ctx", ["value"]),
        ),
    )
    def test_iteration(self, ctx, input_values, monkeypatch, request):
        ctx = request.getfixturevalue(ctx)
        mock_stdin(monkeypatch, input_values)
        ctx.format("{VARIABLE_NAME}")
        assert set(ctx) == {"VARIABLE_NAME"}
        assert len(ctx) == 1

    @mark.parametrize(
        "ctx, input_values",
        (
            ("environ_ctx", []),
            ("empty_ctx", ["value"]),
            ("default_ctx", [""]),
            ("required_ctx", ["value"]),
        ),
    )
    def test_key_values(self, ctx, input_values, monkeypatch, request):
        ctx = request.getfixturevalue(ctx)
        mock_stdin(monkeypatch, input_values)
        ctx.format("{VARIABLE_NAME}")
        assert list(ctx.keys()) == ["VARIABLE_NAME"]
        assert list(ctx.values()) == ["value"]
        assert list(ctx.items()) == [("VARIABLE_NAME", "value")]


class TestRenderString(_Context):
    @mark.parametrize(
        "ctx, input_values",
        (
            ("environ_ctx", []),
            ("empty_ctx", ["value"]),
            ("default_ctx", [""]),
            ("required_ctx", ["value"]),
        ),
    )
    def test_interp(self, ctx, input_values, monkeypatch, request):
        ctx = request.getfixturevalue(ctx)
        mock_stdin(monkeypatch, input_values)
        assert ctx.format("{VARIABLE_NAME}") == "value"

    def test_interp_concat(self, environ_ctx, monkeypatch):
        mock_stdin(monkeypatch, "other")
        assert environ_ctx.format("{VARIABLE_NAME}_{OTHER_VARIABLE}") == "value_other"

    def test_interp_empty(self, environ_ctx, monkeypatch):
        mock_stdin(monkeypatch, "")
        assert environ_ctx.format("{VARIABLE_NAME}_{EMPTY_VARIABLE}") is None
