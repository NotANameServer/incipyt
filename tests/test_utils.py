import pytest

from incipyt._internal.utils import TemplateDict, MultipleValues, Requires, Transform


class TestTemplateDict:
    @pytest.fixture
    def empty_td(self):
        return TemplateDict({})

    @pytest.fixture
    def simple_td(self):
        return TemplateDict({"1": {"2": {"3": None}}})

    @pytest.mark.parametrize(
        "td, res",
        (
            ("empty_td", {"1": Requires(True)}),
            ("simple_td", {"1": MultipleValues(Requires(True), {"2": {"3": None}})}),
        ),
    )
    def test_setitem(self, td, res, request):
        td = request.getfixturevalue(td)
        td["1"] = True

        assert td == res

    @pytest.mark.parametrize(
        "td, res",
        (
            ("empty_td", {"1": True}),
            ("simple_td", {"1": MultipleValues(True, {"2": {"3": None}})}),
        ),
    )
    def test_setitem_notransform(self, td, res, request):
        td = request.getfixturevalue(td)
        td["1"] = Transform(True)

        assert td == res

    @pytest.mark.parametrize(
        "td, res",
        (
            ("empty_td", {"1": {"2": {"3": Requires(True)}}}),
            ("simple_td", {"1": {"2": {"3": MultipleValues(Requires(True), None)}}}),
        ),
    )
    def test_chained_setitem(self, td, res, request):
        td = request.getfixturevalue(td)
        td["1", "2", "3"] = True

        assert td == res

    @pytest.mark.parametrize(
        "td, res",
        (
            ("empty_td", {"1": {"2": Requires(True)}}),
            ("simple_td", {"1": {"2": MultipleValues(Requires(True), {"3": None})}}),
        ),
    )
    def test_ior(self, td, res, request):
        td = request.getfixturevalue(td)
        td |= {"1": {"2": True}}

        assert td == res
