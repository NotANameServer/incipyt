import click
from pytest import fixture, mark, raises

from incipyt import project, variables
from incipyt._internal.templates import (
    ChoiceTemplate,
    StringTemplate,
    TemplateDict,
)
from tests.utils import mock_stdin


class TestStringTemplate:
    @fixture
    def reset_environ(self):
        project.environ.clear()

    @fixture
    def simple_st(self, reset_environ):
        return StringTemplate("{ONE}")

    @fixture
    def sanitizer_st(self, reset_environ):
        return StringTemplate("{ONE}", sanitizer=lambda k, v: f"{v}-sanitizer")

    @fixture
    def multiple_st(self, reset_environ):
        return StringTemplate("{ONE}-{TWO}-{THREE}")

    @mark.parametrize(
        "st, env_vars, stdin, res",
        (
            ("simple_st", {"ONE": "1"}, "", "1"),
            ("sanitizer_st", {"ONE": "1"}, "", "1"),
            ("multiple_st", {"ONE": "1", "TWO": "2", "THREE": "3"}, "\n\n", "1"),
        ),
    )
    def test_env_key_push_default(self, st, env_vars, stdin, res, request, monkeypatch):
        st = request.getfixturevalue(st)
        mock_stdin(monkeypatch, stdin)
        for key, value in env_vars.items():
            variables._EnvMetadata(key, default=value)
        st.format()
        assert project.environ["ONE"] == res

    @mark.parametrize(
        "st, env_vars, res",
        (
            ("simple_st", {"ONE": "1"}, "1"),
            ("sanitizer_st", {"ONE": "1"}, "1"),
            ("multiple_st", {"ONE": "1", "TWO": "2", "THREE": "3"}, "1"),
        ),
    )
    def test_env_key_push_environ(self, st, env_vars, res, request):
        st = request.getfixturevalue(st)
        project.environ |= env_vars
        st.format()
        assert project.environ["ONE"] == res

    @mark.parametrize(
        "st, env_vars, stdin",
        (
            ("simple_st", ["ONE"], ""),
            ("sanitizer_st", ["ONE"], ""),
            ("multiple_st", ["ONE", "TWO", "THREE"], "\n\n"),
        ),
    )
    def test_env_key_push_required(self, st, env_vars, stdin, request, monkeypatch):
        st = request.getfixturevalue(st)
        mock_stdin(monkeypatch, stdin)
        for key in env_vars:
            variables._EnvMetadata(key, required=True)
        st.format()
        assert not project.environ["ONE"]

    @mark.parametrize(
        "st, env_vars, stdin, res",
        (
            ("simple_st", {"ONE": "1"}, "", "1"),
            ("sanitizer_st", {"ONE": "1"}, "", "1-sanitizer"),
            ("multiple_st", {"ONE": "1", "TWO": "2", "THREE": "3"}, "\n\n", "1-2-3"),
        ),
    )
    def test_format_default(self, st, env_vars, stdin, res, request, monkeypatch):
        st = request.getfixturevalue(st)
        mock_stdin(monkeypatch, stdin)
        for key, value in env_vars.items():
            variables._EnvMetadata(key, default=value)
        assert st.format() == res

    @mark.parametrize(
        "st, env_vars, res",
        (
            ("simple_st", {"ONE": "1"}, "1"),
            ("sanitizer_st", {"ONE": "1"}, "1-sanitizer"),
            ("multiple_st", {"ONE": "1", "TWO": "2", "THREE": "3"}, "1-2-3"),
        ),
    )
    def test_format_environ(self, st, env_vars, res, request):
        st = request.getfixturevalue(st)
        project.environ |= env_vars
        assert st.format() == res

    @mark.parametrize(
        "st, env_vars, stdin",
        (
            ("simple_st", {}, ""),
            ("sanitizer_st", {}, ""),
            ("multiple_st", {"TWO": "2", "THREE": "3"}, "\n\n"),
        ),
    )
    def test_format_none(self, st, env_vars, stdin, request, monkeypatch):
        st = request.getfixturevalue(st)
        mock_stdin(monkeypatch, stdin)
        for key, value in env_vars.items():
            variables._EnvMetadata(key, default=value)
        assert st.format() is None

    @mark.parametrize(
        "st, env_vars, stdin, res",
        (
            ("simple_st", ["ONE"], "", ""),
            ("sanitizer_st", ["ONE"], "", "-sanitizer"),
            ("multiple_st", ["ONE", "TWO", "THREE"], "\n\n", "--"),
        ),
    )
    def test_format_required(self, st, env_vars, stdin, res, request, monkeypatch):
        st = request.getfixturevalue(st)
        mock_stdin(monkeypatch, stdin)
        for key in env_vars:
            variables._EnvMetadata(key, required=True)
        assert st.format() == res


class TestChoiceTemplate:
    @fixture
    def reset_environ(self):
        project.environ.clear()

    @fixture
    def simple_mst(self, reset_environ):
        return ChoiceTemplate("a", "b")

    @fixture
    def formattable_mst(self, reset_environ):
        return ChoiceTemplate(StringTemplate("a"), StringTemplate("b"))

    def test_mst_tail(self, simple_mst):
        mst = ChoiceTemplate("x", simple_mst)
        assert mst._values == {StringTemplate("x"), StringTemplate("a"), StringTemplate("b")}

    @mark.parametrize("mst", ("simple_mst", "formattable_mst"))
    def test_call(self, mst, monkeypatch, request):
        mst = request.getfixturevalue(mst)
        mock_stdin(monkeypatch, "a")
        assert mst.format() == "a"

    @mark.parametrize("mst", ("simple_mst", "formattable_mst"))
    def test_call_invalid(self, mst, monkeypatch, request):
        mst = request.getfixturevalue(mst)
        mock_stdin(monkeypatch, "x")
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
            ("simple_td", TemplateDict({"1": ChoiceTemplate("x", "a")})),
            ("choice_td", TemplateDict({"1": ChoiceTemplate.from_items("x", "a", "b")})),
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
            ("simple_td", TemplateDict({"1": ChoiceTemplate("x", "a")})),
            ("choice_td", TemplateDict({"1": ChoiceTemplate.from_items("x", "a", "b")})),
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
            ("nested_td", TemplateDict({"1": {"2": {"3": ChoiceTemplate("x", "a")}}})),
        ),
    )
    def test_chained_setitem(self, td, res, request):
        td = request.getfixturevalue(td)
        td["1", "2", "3"] = "x"
        assert td == res

    @mark.parametrize(
        "td, res",
        (
            ("empty_td", TemplateDict({"1": [StringTemplate("a"), StringTemplate("x")]})),
            (
                "sequence_td",
                TemplateDict(
                    {"1": [StringTemplate("a"), StringTemplate("b"), StringTemplate("x")]}
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
            ("nested_td", TemplateDict({"1": {"2": {"3": ChoiceTemplate("x", "a")}}})),
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
    def empty_td(self, reset_environ):
        return {}

    @fixture
    def simple_td(self, reset_environ):
        return {"1": StringTemplate("{ONE}")}

    @fixture
    def nested_td(self, reset_environ):
        return {"1": {"2": {"3": StringTemplate("{ONE}")}}}

    @fixture
    def choice_td(self, reset_environ):
        return {"1": ChoiceTemplate("{ONE}", "b")}

    @fixture
    def sequence_td(self, reset_environ):
        return {"1": [StringTemplate("{ONE}"), {2: StringTemplate("b")}]}

    @fixture
    def single_td(self, reset_environ):
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
    def test_call(self, td, res, input_values, monkeypatch, request):
        td = request.getfixturevalue(td)
        mock_stdin(monkeypatch, input_values)
        project._Structure._visit(td)
        assert td == res
