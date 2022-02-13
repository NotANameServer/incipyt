import click
from pytest import fixture, mark, raises

from incipyt._internal.templates import (
    MultipleValues,
    Requires,
    TemplateDict,
    Transform,
)
from incipyt import project
from tests.utils import mock_stdin


class TestRequires:
    @fixture
    def reset_environ(self):
        project.environ.clear()

    @fixture
    def simple_rq(self):
        return Requires("{ONE}")

    @fixture
    def kwarg_rq(self):
        return Requires("{ONE}", ONE="1-kwarg")

    @fixture
    def sanitizer_rq(self):
        return Requires("{ONE}", sanitizer=lambda k, v: f"{v}-sanitizer")

    @fixture
    def multiple_rq(self):
        return Requires("{ONE}-{TWO}-{THREE}")

    def test_env_key_push(self, kwarg_rq, reset_environ, monkeypatch):
        mock_stdin(monkeypatch, "")
        kwarg_rq()
        assert project.environ["ONE"] == "1-kwarg"

    def test_env_key_push_prompt(self, simple_rq, reset_environ, monkeypatch):
        mock_stdin(monkeypatch, "1")
        simple_rq()
        assert project.environ["ONE"] == "1"

    @mark.parametrize(
        "rq, variables, stdin, res",
        (
            ("simple_rq", {"ONE": "1"}, "", "1"),
            ("kwarg_rq", {}, "", "1-kwarg"),
            ("sanitizer_rq", {"ONE": "1"}, "", "1-sanitizer"),
            ("multiple_rq", {"ONE": "1", "TWO": "2", "THREE": "3"}, "\n\n", "1-2-3"),
        ),
    )
    def test_format(
        self, rq, variables, stdin, res, reset_environ, request, monkeypatch
    ):
        mock_stdin(monkeypatch, stdin)
        rq = request.getfixturevalue(rq)
        project.environ |= variables
        assert rq() == res

    @mark.parametrize(
        "rq, stdin",
        (
            ("simple_rq", ""),
            ("multiple_rq", "\n\n"),
        ),
    )
    def test_format_null(self, rq, stdin, reset_environ, request, monkeypatch):
        mock_stdin(monkeypatch, stdin)
        rq = request.getfixturevalue(rq)
        project.environ |= {"ONE": "", "TWO": "2", "THREE": "3"}
        assert rq() is None


class TestMultipleValue:
    @fixture
    def simple_mv(self):
        return MultipleValues("a", "b")

    @fixture
    def callable_mv(self):
        return MultipleValues(lambda: "a", lambda: "b")

    @fixture
    def reset_environ(self):
        project.environ.clear()

    def test_mv_tail(self, simple_mv):
        mv = MultipleValues("x", simple_mv)
        assert mv._values == ["x", "a", "b"]

    @mark.parametrize("mv", ("simple_mv", "callable_mv"))
    def test_call(self, mv, reset_environ, monkeypatch, request):
        mock_stdin(monkeypatch, "a")
        mv = request.getfixturevalue(mv)
        assert mv() == "a"

    @mark.parametrize("mv", ("simple_mv", "callable_mv"))
    def test_call_invalid(self, mv, reset_environ, monkeypatch, request):
        mock_stdin(monkeypatch, "x")
        mv = request.getfixturevalue(mv)
        with raises(click.exceptions.Abort):
            mv()


class TestTemplateDict:
    @fixture
    def empty_td(self):
        return TemplateDict({})

    @fixture
    def simple_td(self):
        return TemplateDict({"1": "a"})

    @fixture
    def nested_td(self):
        return TemplateDict({"1": {"2": {"3": "a"}}})

    @fixture
    def multiple_td(self):
        return TemplateDict({"1": MultipleValues("a", "b")})

    @fixture
    def sequence_td(self):
        return TemplateDict({"1": ["a", "b"]})

    @mark.parametrize(
        "td, res",
        (
            ("empty_td", {"1": Requires("x")}),
            ("simple_td", {"1": MultipleValues(Requires("x"), "a")}),
            (
                "multiple_td",
                {"1": MultipleValues.from_items(Requires("x"), "a", "b")},
            ),
        ),
    )
    def test_setitem(self, td, res, request):
        td = request.getfixturevalue(td)
        td["1"] = "x"
        assert td == res

    @mark.parametrize(
        "td, res",
        (
            ("empty_td", {"1": "x"}),
            ("simple_td", {"1": MultipleValues("x", "a")}),
        ),
    )
    def test_setitem_transform(self, td, res, request):
        td = request.getfixturevalue(td)
        td["1"] = Transform("", lambda _: "x")
        assert td == res

    @mark.parametrize(
        "td, res",
        (
            ("empty_td", {"1": "x"}),
            ("simple_td", {"1": MultipleValues("x", "a")}),
        ),
    )
    def test_setitem_notransform(self, td, res, request):
        td = request.getfixturevalue(td)
        td["1"] = Transform("x")
        assert td == res

    @mark.parametrize(
        "td, res",
        (
            ("empty_td", {"1": Requires("x")}),
            ("simple_td", {"1": MultipleValues(Requires("x"), "a")}),
        ),
    )
    def test_setitem_callable(self, td, res, request):
        td = request.getfixturevalue(td)
        td["1"] = Requires("x")
        assert td == res

    @mark.parametrize(
        "td, res",
        (
            ("empty_td", {"1": {"2": {"3": Requires("x")}}}),
            ("nested_td", {"1": {"2": {"3": MultipleValues(Requires("x"), "a")}}}),
        ),
    )
    def test_chained_setitem(self, td, res, request):
        td = request.getfixturevalue(td)
        td["1", "2", "3"] = "x"
        assert td == res

    @mark.parametrize(
        "td, res",
        (
            ("empty_td", {"1": [Requires("a"), Requires("x")]}),
            ("sequence_td", {"1": ["a", "b", Requires("x")]}),
        ),
    )
    def test_sequence_setitem(self, td, res, request):
        td = request.getfixturevalue(td)
        td["1"] = ["a", "x"]
        assert td == res

    @mark.parametrize(
        "td, res",
        (
            ("empty_td", {"1": ["x"]}),
            ("sequence_td", {"1": ["a", "b", "x"]}),
        ),
    )
    def test_sequence_setitem_transform(self, td, res, request):
        td = request.getfixturevalue(td)
        td["1"] = [Transform("", lambda _: "x")]
        assert td == res

    @mark.parametrize(
        "td, res",
        (
            ("empty_td", {"1": {"2": {"3": Requires("x")}}}),
            ("nested_td", {"1": {"2": {"3": MultipleValues(Requires("x"), "a")}}}),
        ),
    )
    def test_ior(self, td, res, request):
        td = request.getfixturevalue(td)
        td |= {"1": {"2": {"3": "x"}}}
        assert td == res

    def test_or(self, simple_td):
        with raises(NotImplementedError):
            simple_td | {}

    @mark.xfail
    @mark.parametrize("td", ("simple_td", "multiple_td"))
    @mark.parametrize("val", (["x"], {"2": "x"}))
    def test_bare_override(self, td, val, request):
        td = request.getfixturevalue(td)
        with raises(AssertionError):
            td["1"] = val

    @mark.xfail
    @mark.parametrize("td", ("nested_td", "sequence_td"))
    def test_override(self, td, request):
        td = request.getfixturevalue(td)
        with raises(AssertionError):
            td["1"] = "x"


class TestTemplateVisitor:
    @fixture
    def reset_environ(self):
        project.environ.clear()

    @fixture
    def empty_td(self):
        return TemplateDict({})

    @fixture
    def simple_td(self):
        return TemplateDict({"1": Requires("{ONE}")})

    @fixture
    def nested_td(self):
        return TemplateDict({"1": {"2": {"3": Requires("{ONE}")}}})

    @fixture
    def multiple_td(self):
        return TemplateDict({"1": MultipleValues(Requires("{ONE}"), "b")})

    @fixture
    def sequence_td(self):
        return TemplateDict({"1": [Requires("{ONE}"), {2: "b"}]})

    @fixture
    def single_td(self):
        return TemplateDict({"1": [Requires("{ONE}")]})

    @mark.parametrize(
        "td, res, input_values",
        (
            ("empty_td", {}, []),
            ("simple_td", {"1": "a"}, ["a"]),
            ("simple_td", {}, [""]),
            ("nested_td", {"1": {"2": {"3": "a"}}}, ["a"]),
            ("nested_td", {}, [""]),
            ("sequence_td", {"1": ["a", {2: "b"}]}, ["a"]),
            ("sequence_td", {"1": [{2: "b"}]}, [""]),
            ("single_td", {"1": ["a"]}, ["a"]),
            ("single_td", {}, [""]),
            ("multiple_td", {"1": "a"}, ["a", "a"]),
        ),
    )
    def test_call(self, td, res, reset_environ, input_values, monkeypatch, request):
        mock_stdin(monkeypatch, input_values)
        td = request.getfixturevalue(td)
        project._Structure._visit(td)
        assert td == res
