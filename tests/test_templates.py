import click
from pytest import fixture, mark, raises

from incipyt._internal.templates import (
    MultiStringTemplate,
    StringTemplate,
    TemplateDict,
    Transform,
)
from incipyt import project
from tests.utils import mock_stdin


class TestStringTemplate:
    @fixture
    def reset_environ(self):
        project.environ.clear()

    @fixture
    def simple_st(self):
        return StringTemplate("{ONE}")

    @fixture
    def kwarg_st(self):
        return StringTemplate("{ONE}", ONE="1-kwarg")

    @fixture
    def sanitizer_st(self):
        return StringTemplate("{ONE}", sanitizer=lambda k, v: f"{v}-sanitizer")

    @fixture
    def multiple_st(self):
        return StringTemplate("{ONE}-{TWO}-{THREE}")

    def test_env_key_push(self, kwarg_st, reset_environ, monkeypatch):
        mock_stdin(monkeypatch, "")
        kwarg_st.format()
        assert project.environ["ONE"] == "1-kwarg"

    def test_env_key_push_prompt(self, simple_st, reset_environ, monkeypatch):
        mock_stdin(monkeypatch, "1")
        simple_st.format()
        assert project.environ["ONE"] == "1"

    @mark.parametrize(
        "st, variables, stdin, res",
        (
            ("simple_st", {"ONE": "1"}, "", "1"),
            ("kwarg_st", {}, "", "1-kwarg"),
            ("sanitizer_st", {"ONE": "1"}, "", "1-sanitizer"),
            ("multiple_st", {"ONE": "1", "TWO": "2", "THREE": "3"}, "\n\n", "1-2-3"),
        ),
    )
    def test_format(
        self, st, variables, stdin, res, reset_environ, request, monkeypatch
    ):
        mock_stdin(monkeypatch, stdin)
        st = request.getfixturevalue(st)
        project.environ |= variables
        assert st.format() == res

    @mark.parametrize(
        "st, stdin",
        (
            ("simple_st", ""),
            ("multiple_st", "\n\n"),
        ),
    )
    def test_format_null(self, st, stdin, reset_environ, request, monkeypatch):
        mock_stdin(monkeypatch, stdin)
        st = request.getfixturevalue(st)
        project.environ |= {"ONE": "", "TWO": "2", "THREE": "3"}
        assert st.format() is None


class TestMultiStringTemplate:
    @fixture
    def simple_mst(self):
        return MultiStringTemplate("a", "b")

    @fixture
    def formattable_mst(self):
        return MultiStringTemplate(StringTemplate("a"), StringTemplate("b"))

    @fixture
    def reset_environ(self):
        project.environ.clear()

    def test_mst_tail(self, simple_mst):
        mst = MultiStringTemplate("x", simple_mst)
        assert mst._values == ["x", "a", "b"]

    @mark.parametrize("mst", ("simple_mst", "formattable_mst"))
    def test_call(self, mst, reset_environ, monkeypatch, request):
        mock_stdin(monkeypatch, "a")
        mst = request.getfixturevalue(mst)
        assert mst.format() == "a"

    @mark.parametrize("mst", ("simple_mst", "formattable_mst"))
    def test_call_invalid(self, mst, reset_environ, monkeypatch, request):
        mock_stdin(monkeypatch, "x")
        mst = request.getfixturevalue(mst)
        with raises(click.exceptions.Abort):
            mst.format()


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
        return TemplateDict({"1": MultiStringTemplate("a", "b")})

    @fixture
    def sequence_td(self):
        return TemplateDict({"1": ["a", "b"]})

    @mark.parametrize(
        "td, res",
        (
            ("empty_td", {"1": StringTemplate("x")}),
            ("simple_td", {"1": MultiStringTemplate(StringTemplate("x"), "a")}),
            (
                "multiple_td",
                {"1": MultiStringTemplate.from_items(StringTemplate("x"), "a", "b")},
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
            ("simple_td", {"1": MultiStringTemplate("x", "a")}),
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
            ("simple_td", {"1": MultiStringTemplate("x", "a")}),
        ),
    )
    def test_setitem_notransform(self, td, res, request):
        td = request.getfixturevalue(td)
        td["1"] = Transform("x")
        assert td == res

    @mark.parametrize(
        "td, res",
        (
            ("empty_td", {"1": StringTemplate("x")}),
            ("simple_td", {"1": MultiStringTemplate(StringTemplate("x"), "a")}),
        ),
    )
    def test_setitem_callable(self, td, res, request):
        td = request.getfixturevalue(td)
        td["1"] = StringTemplate("x")
        assert td == res

    @mark.parametrize(
        "td, res",
        (
            ("empty_td", {"1": {"2": {"3": StringTemplate("x")}}}),
            (
                "nested_td",
                {"1": {"2": {"3": MultiStringTemplate(StringTemplate("x"), "a")}}},
            ),
        ),
    )
    def test_chained_setitem(self, td, res, request):
        td = request.getfixturevalue(td)
        td["1", "2", "3"] = "x"
        assert td == res

    @mark.parametrize(
        "td, res",
        (
            ("empty_td", {"1": [StringTemplate("a"), StringTemplate("x")]}),
            ("sequence_td", {"1": ["a", "b", StringTemplate("x")]}),
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
            ("empty_td", {"1": {"2": {"3": StringTemplate("x")}}}),
            (
                "nested_td",
                {"1": {"2": {"3": MultiStringTemplate(StringTemplate("x"), "a")}}},
            ),
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
        return TemplateDict({"1": StringTemplate("{ONE}")})

    @fixture
    def nested_td(self):
        return TemplateDict({"1": {"2": {"3": StringTemplate("{ONE}")}}})

    @fixture
    def multiple_td(self):
        return TemplateDict({"1": MultiStringTemplate(StringTemplate("{ONE}"), "b")})

    @fixture
    def sequence_td(self):
        return TemplateDict({"1": [StringTemplate("{ONE}"), {2: "b"}]})

    @fixture
    def single_td(self):
        return TemplateDict({"1": [StringTemplate("{ONE}")]})

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
