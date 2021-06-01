from jinja2 import Template
from pytest import fixture, mark, raises

from incipyt._internal.templates import RenderContext
from incipyt.system import Environment
from tests.utils import mock_stdin


class _Context:
    @fixture
    def env(self):
        env = Environment(auto_confirm=True)
        env["VARIABLE_NAME"] = "value"
        env["EMPTY_VARIABLE"] = ""
        return env

    @fixture
    def simple_ctx(self, env):
        return RenderContext(env)

    @fixture
    def populated_ctx(self, simple_ctx):
        simple_ctx.render_string("{VARIABLE_NAME}")
        return simple_ctx


class TestRenderContext(_Context):
    def test_contains(self, simple_ctx):
        assert "VARIABLE_NAME" in simple_ctx

    def test_contains_undefined(self, simple_ctx, monkeypatch):
        mock_stdin(monkeypatch, "value")
        assert "OTHER_NAME" in simple_ctx
        assert simple_ctx["OTHER_NAME"] == "value"

    def test_getitem_empty(self, simple_ctx):
        with raises(ValueError):
            simple_ctx["EMPTY_VARIABLE"]

    def test_getitem_sanitized(self, simple_ctx):
        simple_ctx._sanitizer = lambda k, v: v.upper()
        assert simple_ctx["VARIABLE_NAME"] == "VALUE"

    @mark.parametrize(
        "ctx, res",
        (
            ("simple_ctx", set()),
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
            ("populated_ctx", ["VARIABLE_NAME"], ["value"]),
        ),
    )
    def test_key_values(self, ctx, keys, values, request):
        ctx = request.getfixturevalue(ctx)
        assert list(ctx.keys()) == keys
        assert list(ctx.values()) == values
        assert list(ctx.items()) == list(zip(keys, values))


class TestRenderString(_Context):
    def test_interp(self, simple_ctx):
        assert simple_ctx.render_string("{VARIABLE_NAME}") == "value"

    def test_interp_kwarg(self, simple_ctx):
        assert simple_ctx.render_string("{OTHER_NAME}", OTHER_NAME="value") == "value"

    def test_interp_undefined(self, simple_ctx, monkeypatch):
        mock_stdin(monkeypatch, "value")
        assert simple_ctx.render_string("{OTHER_NAME}") == "value"

    def test_interp_empty(self, simple_ctx):
        assert simple_ctx.render_string("{VARIABLE_NAME}{EMPTY_VARIABLE}") is None


class TestRenderTemplate(_Context):
    def test_interp(self, simple_ctx):
        assert simple_ctx.render_template(Template("{{ VARIABLE_NAME }}")) == "value"

    def test_iterp_undefined(self, simple_ctx, monkeypatch):
        mock_stdin(monkeypatch, "value")
        assert simple_ctx.render_template(Template("{{ OTHER_NAME }}")) == "value"

    def test_iterp_empty(self, simple_ctx):
        assert (
            simple_ctx.render_template(
                Template("{{ VARIABLE_NAME }}{{ EMPTY_VARIABLE }}")
            )
            is None
        )
