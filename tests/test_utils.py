import pytest

from incipyt._internal.templates import (
    TemplateDict,
    MultipleValues,
    Requires,
    Transform,
)


class TestTemplateDict:
    @pytest.fixture
    def empty_td(self):
        return TemplateDict({})

    @pytest.fixture
    def simple_td(self):
        return TemplateDict({"1": "a"})

    @pytest.fixture
    def nested_td(self):
        return TemplateDict({"1": {"2": {"3": "a"}}})

    @pytest.fixture
    def multiple_td(self):
        return TemplateDict({"1": MultipleValues("a", "b")})

    @pytest.fixture
    def sequence_td(self):
        return TemplateDict({"1": ["a", "b"]})

    @pytest.mark.parametrize(
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

    @pytest.mark.parametrize(
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

    @pytest.mark.parametrize(
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

    @pytest.mark.parametrize(
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

    @pytest.mark.parametrize(
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

    @pytest.mark.parametrize(
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

    @pytest.mark.parametrize(
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

    @pytest.mark.parametrize(
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
        with pytest.raises(NotImplementedError):
            simple_td | {}

    @pytest.mark.xfail
    @pytest.mark.parametrize("td", ("simple_td", "multiple_td"))
    @pytest.mark.parametrize("val", (["x"], {"2": "x"}))
    def test_bare_override(self, td, val, request):
        td = request.getfixturevalue(td)
        with pytest.raises(AssertionError):
            td["1"] = val

    @pytest.mark.xfail
    @pytest.mark.parametrize("td", ("nested_td", "sequence_td"))
    def test_override(self, td, request):
        td = request.getfixturevalue(td)
        with pytest.raises(AssertionError):
            td["1"] = "x"
