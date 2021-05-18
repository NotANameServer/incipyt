import collections.abc
from string import Formatter

import click


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


def append_unique(config, value):
    assert isinstance(config, collections.abc.MutableSequence)

    if value not in config:
        config.append(value)


def is_not_string_sequence(obj):
    return (
        isinstance(obj, collections.abc.Sequence)
        and not isinstance(obj, collections.abc.ByteString)
        and not isinstance(obj, str)
    )


class TemplateDict(collections.UserDict):
    def __init__(self, mapping=None):
        # If an existing mapping is provided, this class will act like a proxy
        # around it
        self.data = {} if mapping is None else mapping

    def __setitem__(self, keys, value):
        if not is_not_string_sequence(keys):
            keys = [keys]

        self._set_item_from_chained_keys(self, keys, value)

    def set_items(self, mapping, transformer=None):
        self._set_items(self, mapping, transformer=transformer)

    @staticmethod
    def _set_item(mapping, key, value):
        assert isinstance(mapping, collections.abc.Mapping)

        if key in mapping:
            existing_value = mapping[key]
            if value == existing_value:
                return
            value = MultipleValues(value, existing_value)

        # Check if processed mapping is a proxy object or not to avoid endless
        # recursion on overriden __setitem__
        if hasattr(mapping, "data"):
            mapping.data[key] = value
        else:
            mapping[key] = value

    @staticmethod
    def _set_item_from_chained_keys(mapping, keys, value):
        assert isinstance(mapping, collections.abc.MutableMapping)
        assert is_not_string_sequence(keys)

        keys = list(keys)
        key = keys.pop(0)

        if not keys:
            TemplateDict._set_item(mapping, key, value)
            return

        if key not in mapping:
            mapping[key] = {}
        TemplateDict._set_item_from_chained_keys(mapping[key], keys, value)

    @staticmethod
    def _set_items(mapping, added_mapping, transformer=None):
        assert isinstance(mapping, collections.abc.MutableMapping)
        assert isinstance(added_mapping, collections.abc.Mapping)

        for key, value in added_mapping.items():
            if isinstance(value, collections.abc.Mapping):
                if key not in mapping:
                    mapping[key] = {}
                TemplateDict._set_items(mapping[key], value, transformer=transformer)

            else:
                TemplateDict._set_item(
                    mapping, key, transformer(value) if transformer else value
                )
