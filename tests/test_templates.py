import click
from pytest import fixture, mark, raises

from incipyt._internal.templates import (
    ChoiceTemplate,
    StringTemplate,
    TemplateDict,
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


class TestChoiceTemplate:
    @fixture
    def simple_mst(self):
        return ChoiceTemplate("a", "b")

    @fixture
    def formattable_mst(self):
        return ChoiceTemplate(StringTemplate("a"), StringTemplate("b"))

    @fixture
    def reset_environ(self):
        project.environ.clear()

    def test_mst_tail(self, simple_mst):
        mst = ChoiceTemplate("x", simple_mst)
        assert mst._values == {
            StringTemplate("x"),
            StringTemplate("a"),
            StringTemplate("b"),
        }

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


class TestTemplateCollection:
    @fixture
    def empty_td(self):
        return TemplateDict({})

    @fixture
    def simple_td(self):
        return TemplateDict({"1": StringTemplate("a")})

    @fixture
    def nested_td(self):
        return TemplateDict({"1": {"2": {"3": StringTemplate("a")}}})

    @fixture
    def choice_td(self):
        return TemplateDict({"1": ChoiceTemplate("a", "b")})

    @fixture
    def sequence_td(self):
        return TemplateDict({"1": [StringTemplate("a"), StringTemplate("b")]})

    @mark.parametrize(
        "td, res",
        (
            ("empty_td", TemplateDict({"1": StringTemplate("x")})),
            (
                "simple_td",
                TemplateDict({"1": ChoiceTemplate("x", "a")}),
            ),
            (
                "choice_td",
                TemplateDict({"1": ChoiceTemplate.from_items("x", "a", "b")}),
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
            ("empty_td", TemplateDict({"1": StringTemplate("x")})),
            (
                "simple_td",
                TemplateDict({"1": ChoiceTemplate("x", "a")}),
            ),
            (
                "choice_td",
                TemplateDict({"1": ChoiceTemplate.from_items("x", "a", "b")}),
            ),
        ),
    )
    def test_setitem_callable(self, td, res, request):
        td = request.getfixturevalue(td)
        td["1"] = StringTemplate("x")
        assert td == res

    @mark.parametrize(
        "td, res",
        (
            ("empty_td", TemplateDict({"1": {"2": {"3": StringTemplate("x")}}})),
            (
                "nested_td",
                TemplateDict({"1": {"2": {"3": ChoiceTemplate("x", "a")}}}),
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
            (
                "empty_td",
                TemplateDict({"1": [StringTemplate("a"), StringTemplate("x")]}),
            ),
            (
                "sequence_td",
                TemplateDict(
                    {
                        "1": [
                            StringTemplate("a"),
                            StringTemplate("b"),
                            StringTemplate("x"),
                        ]
                    }
                ),
            ),
        ),
    )
    def test_sequence_setitem(self, td, res, request):
        td = request.getfixturevalue(td)
        td["1"] = ["a", "x"]
        assert td == res

    @mark.parametrize(
        "td, res",
        (
            (
                "empty_td",
                TemplateDict(
                    {
                        "1": [
                            StringTemplate("a"),
                            [StringTemplate("x"), StringTemplate("y")],
                            {"2": StringTemplate("z")},
                        ]
                    }
                ),
            ),
            (
                "sequence_td",
                TemplateDict(
                    {
                        "1": [
                            StringTemplate("a"),
                            StringTemplate("b"),
                            [StringTemplate("x"), StringTemplate("y")],
                            {"2": StringTemplate("z")},
                        ]
                    }
                ),
            ),
        ),
    )
    def test_nested_sequence_setitem(self, td, res, request):
        td = request.getfixturevalue(td)
        td["1"] = ["a", ["x", "y"], {"2": "z"}]
        assert td == res

    @mark.parametrize(
        "td, res",
        (
            ("empty_td", TemplateDict({"1": {"2": {"3": StringTemplate("x")}}})),
            (
                "nested_td",
                TemplateDict({"1": {"2": {"3": ChoiceTemplate("x", "a")}}}),
            ),
        ),
    )
    def test_ior(self, td, res, request):
        td = request.getfixturevalue(td)
        td |= {"1": {"2": {"3": "x"}}}
        assert td == res


class TestTemplateVisitor:
    @fixture
    def reset_environ(self):
        project.environ.clear()

    @fixture
    def empty_td(self):
        return {}

    @fixture
    def simple_td(self):
        return {"1": StringTemplate("{ONE}")}

    @fixture
    def nested_td(self):
        return {"1": {"2": {"3": StringTemplate("{ONE}")}}}

    @fixture
    def choice_td(self):
        return {"1": ChoiceTemplate("{ONE}", "b")}

    @fixture
    def sequence_td(self):
        return {"1": [StringTemplate("{ONE}"), {2: StringTemplate("b")}]}

    @fixture
    def single_td(self):
        return {"1": [StringTemplate("{ONE}")]}

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
            ("choice_td", {"1": "a"}, ["a", "a"]),
        ),
    )
    def test_call(self, td, res, reset_environ, input_values, monkeypatch, request):
        mock_stdin(monkeypatch, input_values)
        td = request.getfixturevalue(td)
        project._Structure._visit(td)
        assert td == res
