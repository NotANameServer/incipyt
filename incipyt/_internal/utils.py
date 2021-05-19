import collections.abc


def is_nonstring_sequence(obj):
    return (
        isinstance(obj, collections.abc.Sequence)
        and not isinstance(obj, collections.abc.ByteString)
        and not isinstance(obj, str)
    )


def make_repr(obj, *args, **kwargs):
    """Make a representation string with ease.

    :param obj: Any object to get a representation.
    :return: String representation of `obj`.
    :rtype: str
    """
    from_attributes = [f"{a}={getattr(obj, a)}" for a in args]
    from_kwargs = [f"{k}={v}" for k, v in kwargs.items()]
    params = ", ".join(from_attributes + from_kwargs)

    return f"""{type(obj).__name__}({params})"""


def attrs_eq(a, b, *args):
    """Compare two objects with their attributs.

    :return: `True` if all provided attributes of objects `a` and `b` are equals.
    :rtype: bool
    """
    try:
        return all(getattr(a, attr) == getattr(b, attr) for attr in args)
    except AttributeError:
        return False
