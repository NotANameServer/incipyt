import collections.abc
import dataclasses

from typing import Any


@dataclasses.dataclass
class EnvValue:
    value: Any
    update: bool = False
    confirmed: bool = False


def is_nonstring_sequence(obj):
    """Check if a given object is a non-string sequence.

    :param obj: Any object to check.
    :return: `True` if `obj` is a non-string :class:`Sequence` instance.
    :rtype: :class:`bool`
    """
    return (
        isinstance(obj, collections.abc.Sequence)
        and not isinstance(obj, collections.abc.ByteString)
        and not isinstance(obj, str)
    )


def make_repr(obj, *args, **kwargs):
    r"""Make a representation string with ease.

    :param obj: Any object to make a representation for.
    :param \*args: Attributes names to include.
    :type \*args: :class:`str`
    :param \**kwargs: Other `attribute_name=any_value` to include.
    :return: String representation of `obj`.
    :rtype: :class:`str`
    """
    from_attributes = [f"{a}={getattr(obj, a)}" for a in args]
    from_kwargs = [f"{k}={v}" for k, v in kwargs.items()]
    params = ", ".join(from_attributes + from_kwargs)

    return f"""{type(obj).__name__}({params})"""


def attrs_eq(a, b, *args):
    r"""Compare two objects according to their attributes.

    :param a: First object to compare.
    :param b: Second object to compare.
    :param \*args: Attributes names to check for.
    :type \*args: :class:`str`
    :return: `True` if all provided attributes of objects `a` and `b` are equals.
    :rtype: :class:`bool`
    """
    try:
        return all(getattr(a, attr) == getattr(b, attr) for attr in args)
    except AttributeError:
        return False


def formattable(obj):
    r"""Know if an object is formattable.

    :param obj: Object to know if :meth:`format` can be used.
    :return: `True` :meth:`format` can be called.
    :rtype: :class:`bool`
    """
    return hasattr(obj, "format") and callable(obj.format)
