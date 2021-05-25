from io import StringIO

from pytest import mark

from incipyt._internal.utils import is_nonstring_sequence


@mark.parametrize(
    "obj, res",
    (
        (None, False),
        (b"abc", False),
        ("abc", False),
        (StringIO("abc"), False),
        ({}, False),
        ([], True),
        ((), True),
    ),
)
def test_nonstring_sequence(obj, res):
    assert is_nonstring_sequence(obj) == res
