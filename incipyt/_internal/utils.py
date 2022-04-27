import collections.abc
import dataclasses

from typing import Any


@dataclasses.dataclass
class EnvValue:
    value: Any
    update: bool = False
    confirmed: bool = False


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


def attrs_hash(a, *args, **kwargs):
    return hash(tuple(getattr(a, attr) for attr in args) + tuple(kwargs.items()))


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


def unfold_dict(config):
    unfolded_config = {}

    for key_section, value_section in config.items():
        if isinstance(value_section, collections.abc.Mapping):
            if key_section not in unfolded_config:
                unfolded_config[key_section] = {}
            for key, value in value_section.items():
                if isinstance(value, collections.abc.Mapping):
                    unfolded_config[key_section][key] = "\n" + "\n".join(
                        f"{k} = {v}" for k, v in value.items()
                    )
                else:
                    unfolded_config[key_section][key] = value
        else:
            unfolded_config[key_section] = value_section

    return unfolded_config


def unfold_list(config):
    unfolded_config = {}

    for key, value in config.items():
        if isinstance(value, collections.abc.Mapping):
            unfolded_config[key] = unfold_list(value)
        elif is_nonstring_sequence(value):
            unfolded_config[key] = "\n" + "\n".join(value)
        else:
            unfolded_config[key] = value

    return unfolded_config
