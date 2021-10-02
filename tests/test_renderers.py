from pytest import fixture, mark, raises

from incipyt import project
from incipyt._internal.templates import FormatterEnviron

from tests.utils import mock_stdin


class _Context:
    @fixture
    def reset_environ(self):
        project.environ.clear()
        project.environ["VARIABLE_NAME"] = project.EnvValue("value", confirmed=True)
        project.environ["EMPTY_VARIABLE"] = project.EnvValue("", confirmed=True)

    @fixture
    def simple_ctx(self, reset_environ):
        return FormatterEnviron()

    @fixture
    def no_error_ctx(self, reset_environ):
        return FormatterEnviron(value_error=False)

    @fixture
    def populated_ctx(self, simple_ctx):
        simple_ctx.format("{VARIABLE_NAME}")
        return simple_ctx


class TestFormatterEnviron(_Context):
    def test_contains(self, simple_ctx):
        assert "VARIABLE_NAME" in simple_ctx

    @mark.parametrize("ctx", ("simple_ctx", "no_error_ctx"))
    def test_contains_undefined(self, ctx, monkeypatch, request):
        mock_stdin(monkeypatch, "value")
        ctx = request.getfixturevalue(ctx)
        assert "OTHER_NAME" in ctx
        assert ctx["OTHER_NAME"] == "value"

    def test_getitem_empty_simple(self, simple_ctx):
        with raises(ValueError):
            simple_ctx["EMPTY_VARIABLE"]

    def test_getitem_empty_no_error(self, no_error_ctx):
        assert no_error_ctx["EMPTY_VARIABLE"] == ""

    @mark.parametrize("ctx", ("simple_ctx", "no_error_ctx"))
    def test_getitem_sanitized(self, ctx, request):
        ctx = request.getfixturevalue(ctx)
        ctx._sanitizer = lambda k, v: v.upper()
        assert ctx["VARIABLE_NAME"] == "VALUE"

    @mark.parametrize(
        "ctx, res",
        (
            ("simple_ctx", set()),
            ("no_error_ctx", set()),
            ("populated_ctx", {"VARIABLE_NAME"}),
        ),
    )
    def test_iteration(self, ctx, res, request):
        ctx = request.getfixturevalue(ctx)
        assert set(ctx) == res
        assert len(ctx) == len(res)

    @mark.parametrize(
        "ctx, keys, values",
        (
            ("simple_ctx", [], []),
            ("no_error_ctx", [], []),
            ("populated_ctx", ["VARIABLE_NAME"], ["value"]),
        ),
    )
    def test_key_values(self, ctx, keys, values, request):
        ctx = request.getfixturevalue(ctx)
        assert list(ctx.keys()) == keys
        assert list(ctx.values()) == values
        assert list(ctx.items()) == list(zip(keys, values))


class TestRenderString(_Context):
    @mark.parametrize("ctx", ("simple_ctx", "no_error_ctx"))
    def test_interp(self, ctx, request):
        ctx = request.getfixturevalue(ctx)
        assert ctx.format("{VARIABLE_NAME}") == "value"

    @mark.parametrize("ctx", ("simple_ctx", "no_error_ctx"))
    def test_interp_kwarg(self, ctx, monkeypatch, request):
        mock_stdin(monkeypatch, "")
        ctx = request.getfixturevalue(ctx)
        assert ctx.format("{OTHER_NAME}", OTHER_NAME="value") == "value"

    @mark.parametrize("ctx", ("simple_ctx", "no_error_ctx"))
    def test_interp_undefined(self, ctx, monkeypatch, request):
        mock_stdin(monkeypatch, "value")
        ctx = request.getfixturevalue(ctx)
        assert ctx.format("{OTHER_NAME}") == "value"

    @mark.parametrize(
        "ctx, res",
        (
            ("simple_ctx", None),
            ("no_error_ctx", "value"),
        ),
    )
    def test_interp_empty(self, ctx, res, request):
        ctx = request.getfixturevalue(ctx)
        assert ctx.format("{VARIABLE_NAME}{EMPTY_VARIABLE}") == res
