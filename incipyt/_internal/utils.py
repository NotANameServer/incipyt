import collections
from string import Formatter

import click


def is_nonstring_sequence(obj):
    return (
        isinstance(obj, collections.abc.Sequence)
        and not isinstance(obj, collections.abc.ByteString)
        and not isinstance(obj, str)
    )


def make_repr(obj, *args, **kwargs):
    """Utility function to ease `__repr__` definition."""
    from_attributes = [f"{a}={getattr(obj, a)}" for a in args]
    from_kwargs = [f"{k}={v}" for k, v in kwargs.items()]
    params = ", ".join(from_attributes + from_kwargs)

    return f"""{type(obj).__name__}({params})"""


def attrs_eq(a, b, *args):
    """Return `True` if all provided attributes of objects `a` and `b` are equals."""
    try:
        return all(getattr(a, attr) == getattr(b, attr) for attr in args)
    except AttributeError:
        return False


Transform = collections.namedtuple(
    "Transform", ("value", "transform"), defaults=(lambda x: x,)
)


class Requires:
    def __init__(self, template, confirmed=False, sanitizer=None, **kwargs):
        self._confirmed = confirmed
        self._sanitizer = sanitizer
        self._template = template
        self._kwargs = kwargs

    def __str__(self):
        return f"f'{self._template}'"

    def __repr__(self):
        return make_repr(
            self,
            template=self._template,
            confirmed=self._confirmed,
            santizer=self._sanitizer,
            kwargs=self._kwargs,
        )

    def __eq__(self, other):
        return attrs_eq(self, other, "_template", "_confirmed", "_sanitizer", "_kwargs")

    def __call__(self, environment):
        for _, key, _, _ in Formatter().parse(self._template):
            if key not in self._kwargs:
                continue

            environment.push(key, self._kwargs[key], confirmed=self._confirmed)

        args = {
            key: (
                self._sanitizer(key, environment.pull(key))
                if self._sanitizer
                else environment.pull(key)
            )
            for _, key, _, _ in Formatter().parse(self._template)
            if key is not None
        }
        if any(not v for v in args.values()):
            return None

        return self._template.format(**args)


class MultipleValues:
    def __init__(self, head, tail):
        self._values = (
            [head] + tail._values if isinstance(tail, MultipleValues) else [head, tail]
        )

    def __call__(self, environment):
        return click.prompt(
            "Conflicting configuration, choose between",
            type=click.Choice(
                [
                    value(environment) if callable(value) else value
                    for value in self._values
                ]
            ),
        )

    def __repr__(self):
        return f"{type(self).__name__}({self._values})"

    def __eq__(self, other):
        return attrs_eq(self, other, "_values")


class TemplateDict(collections.UserDict):
    """This class will act like a proxy around a provided mapping."""

    def __init__(self, mapping):
        self.data = mapping

    def __setitem__(self, keys, value):
        value, transform = self._get_transform(value)
        if not is_nonstring_sequence(keys):
            keys = (keys,)

        if isinstance(value, collections.abc.Mapping):
            for k, v in value.items():
                self[keys + (k,)] = Transform(v, transform)
            return

        config = self.data

        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        key = keys[-1]

        if is_nonstring_sequence(value):
            if key not in config:
                config[key] = []

            assert not isinstance(
                config[key], collections.abc.Mapping
            ), f"{config[key]} is already a mapping, cannot set to a sequence."

            for v in value:
                if v not in config[key]:
                    config[key].append(v if callable(v) else transform(v))

        else:
            value = value if callable(value) else transform(value)
            if key in config:
                if config[key] != value:
                    config[key] = MultipleValues(value, config[key])
            else:
                config[key] = value

    def __ior__(self, other):
        other, transform = self._get_transform(other)

        assert isinstance(
            other, collections.abc.Mapping
        ), f"RHS of |= for {type(self)} should be a mapping."

        for key, value in other.items():
            self[key] = Transform(value, transform)
        return self

    def __or__(self, other):
        raise NotImplementedError(
            f"{type(self)} do not support |, use self.data | or |=."
        )

    @staticmethod
    def _get_transform(value):
        """Return a `(value, transform)` pair from a potential two-tuple. If a
        `Transform` is provided, it will be returned as-is. If a bare value is
        provided, a `Transform` will be created and `transform` will fallback
        to `Requires`.
        """
        if isinstance(value, Transform):
            assert callable(value[1]), "Second Transform element has to be callable."
            return value
        return Transform(value, Requires)
