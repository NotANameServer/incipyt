from pytest import fixture, mark, raises

from incipyt._internal.templates import (
    TemplateDict,
    MultipleValues,
    Requires,
    Transform,
)


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
