"""This module contains classes related to template definition and rendering.

Incipyt mainly uses two kinds of templates: bare template strings that behave
like builtin Python string formatting. It also provides special wrappers to
allow easier templating of collections data structures, such as dict-like
template objects.
"""

import contextlib
import logging
from collections import abc
from string import Formatter
from typing import Any, Callable, NamedTuple

import click

from incipyt import project
from incipyt._internal import utils

logger = logging.getLogger(__name__)


class StringTemplate:
    """This class acts like a wrapper around a format string.

    When an instance is called, it renders the underlying format string using
    environ values and overrides.
    """

    def __init__(
        self, format_string, confirmed=False, sanitizer=None, value_error=True, **kwargs
    ):
        r"""This class acts like a wrapper around a format string.

        When an instance is called, it renders the underlying format string
        using environ values and overrides.

        :param format_string: A format string whose keyword argument will be substituted.
        :type format_string: :class:`str`
        :param confirmed: Confirmed status for new variables from keyword args.
        :type confirmed: :class:`bool`, optionnal
        :param sanitizer: An optionnal callable to sanitize the values given (key, value) pairs.
        :type sanitizer: :class:`function` or `None`, optionnal
        :param value_error: Empty values generate errors.
        :type value_error: :class:`bool`
        :param \**kwargs: Variables overrides that will be used for rendering and pushed to the environ.
            Automatically wrapped in :class:`incipyt._internal.utils.EnvValue` if needed.
        :type \**kwargs: :class:`str`, optionnal
        """
        self._confirmed = confirmed
        self._sanitizer = sanitizer
        self._value_error = value_error
        self._format_string = format_string
        self._kwargs = kwargs

    def __eq__(self, other):
        return utils.attrs_eq(
            self,
            other,
            "_format_string",
            "_confirmed",
            "_sanitizer",
            "_value_error",
            "_kwargs",
        )

    def __hash__(self):
        return utils.attrs_hash(
            self,
            "_format_string",
            "_confirmed",
            "_sanitizer",
            "_value_error",
            **self._kwargs,
        )

    def format(self):  # noqa: A003
        """Format the underlying format string using variables from the environ.

        :return: The formatted string.
        :rtype: :class:`str`
        """
        return FormatterEnviron(
            sanitizer=self._sanitizer, value_error=self._value_error
        ).format(
            self._format_string,
            **{
                key: (
                    value
                    if isinstance(value, utils.EnvValue)
                    else utils.EnvValue(value, confirmed=self._confirmed)
                )
                for key, value in self._kwargs.items()
            },
        )

    def __repr__(self):
        return utils.make_repr(
            self,
            format_string=self._format_string,
            confirmed=self._confirmed,
            sanitizer=self._sanitizer,
            value_error=self._value_error,
            kwargs=self._kwargs,
        )


class Transform(NamedTuple):
    """Compound type containing a value and a "transform".

    A transform is a callable that will be used to transform the value. If no
    transform is provided, the identity function will be used, hence the value
    will not be transformed.
    """

    value: Any
    transform: Callable = StringTemplate

    @staticmethod
    def _get_transform(value, transform=StringTemplate):
        """Wrap `value` in :class:`incipyt._internal.templates.Transform` if needed.

        Wrapping with a `None` transform will result in
        :class:`incipyt._internal.templates.StringTemplate` being used.

        :param value: A bare value or already wrapped value.
        :type value: :class:`str` or :class:`incipyt._internal.templates.Transform`
        :param transform: Callable to be wrapped.
        :type transform: :class:`function` or `None`, optionnal
        :return: Original or wrapped `value`.
        :rtype: :class:`incipyt._internal.templates.Transform`
        """
        if isinstance(value, Transform):
            assert callable(value.transform), "Transform has to be callable."
            return value
        return Transform(value, transform)

    @staticmethod
    def _get_value(value, transform):
        """Transform a value according to its wrapped transformation or fallback.

        :param value: Value to transform. If it is formattable, it will not be transformed.
        :type value: :class:`str` or :class:`function` or :class:`incipyt._internal.templates.Transform`
        :param transform: Fallback callable for transformation.
        :type transform: :class:`function`
        :return: Transformed `value`.
        :rtype: :class:`str` or `formattable`
        """
        if isinstance(value, Transform):
            return Transform._get_value(*value)
        elif utils.formattable(value) and not isinstance(value, str):
            return value
        else:
            return transform(value)


class MultiStringTemplate:
    """Class to hold multiple values for a single key.

    When an instance is called, the user will be asked to pick a value using
    the command line interface.
    """

    def __init__(self, head, tail):
        """Class to hold multiple string for a single key.

        When an instance is called, the user will be asked to pick a string
        using the command line interface.

        :param head: Entry to put a the head of the stack.
        :type tail: :class:str
        :param tail: Tail of the stack.
        :type tail: :class:`incipyt._intternal.templates.MultiStringTemplate` or any bare value
        """
        self._values = (
            {Transform._get_value(*Transform._get_transform(head))} | tail._values
            if isinstance(tail, MultiStringTemplate)
            else {
                Transform._get_value(*Transform._get_transform(head)),
                Transform._get_value(*Transform._get_transform(tail)),
            }
        )

    def format(self):  # noqa: A003
        """Ask the user to pick a value using the command line interface.

        If it is formattable, it will be formatted.

        :return: The user-choosen value.
        """
        return click.prompt(
            "Conflicting configuration, choose between",
            type=click.Choice(
                [
                    value.format() if utils.formattable(value) else value
                    for value in self._values
                ]
            ),
        )

    def __eq__(self, other):
        return utils.attrs_eq(self, other, "_values")

    def __hash__(self):
        return hash(tuple(self._values))

    def __repr__(self):
        return f"{type(self).__name__}({self._values})"

    @classmethod
    def from_items(cls, *args):
        r"""Build a class instance from any number of bare values.

        :param \*args: Entries to wrap.
        :return: New class instance
        :rtype: :class:`incipyt._intternal.templates.MultiStringTemplate`
        """
        instance = cls(args[0], args[1])
        for value in args[2:]:
            instance = cls(value, instance)
        return instance


class TemplateDict(abc.MutableMapping):
    """Proxy class around a provided mapping.

    This is itended to ease configuration templating.

    :Class instanciation:

    >>> cfg = TemplateDict({})

    :Setting values:

    Following exemples assume `cfg` is a `TemplateDict` around an empty `dict`.

    Bare values will be wrapped into :class:`incipyt._internal.templates.StringTemplate`
    automatically :

    >>> cfg["key"] = "{VARIABLE_NAME}"
    >>> print(cfg)
        {"key": StringTemplate("{VARIABLE_NAME}")}

    Callables will be kept as-is:

    >>> cfg["key"] = a_formattable
    >>> print(cfg)
        {"key": a_formattable}

    Values of :class:`incipyt._internal.templates.Transform` instances will be
    evaluated accordingly to their transform:

    >>> cfg["key"] = Transform("{VARIABLE_NAME}", a_formattable)
    >>> print(cfg)
        {"key": a_formattable("{VARIABLE_NAME}")}

    Not giving an explicit callable to
    :class:`incipyt._internal.templates.Transform` will default to the identity
    function and keep the values as-is:

    >>> cfg["key"] = Transform("Something")
    >>> print(cfg)
        {"key": "Something"}

    Collections are supported as well:

    >>> cfg["key"] = ["{VARIABLE_NAME}"]
    >>> print(cfg)
        {"key": [StringTemplate("{VARIABLE_NAME}")]}

    >>> cfg["key"] = {"keyB": "{VARIABLE_NAME}"}
    >>> print(cfg)
        {"key": {"keyB": StringTemplate("{VARIABLE_NAME}")}}

    :Nested keys:

    To ease nested structure definition, the following syntax is supported:

    >>> cfg["keyA", "keyB"] = "{VARIABLE_NAME}"
    >>> print(cfg)
        {"keyA": {"keyB": StringTemplate("{VARIABLE_NAME}")}}

    :Multiple values:

    Instances of :class:`incipyt._internal.templates.MultiStringTemplate` will be
    created in case of value overrides. For instance, if `previous_value` is
    formattable:

    >>> cfg == TemplateDict({"key": previous_value})
    >>> cfg["key"] = "{VARIABLE_NAME}"
    >>> print(cfg)
        {"key": MulitpleValues(StringTemplate("{VARIABLE_NAME}"), previous_value)}

    If `previous_list` is a mutable sequence, any value not already present in
    it will be appended:

    >>> cfg == TemplateDict({"key": previous_list})
    >>> cfg["key"] = ["{VARIABLE_NAME}"]
    >>> cfg == {"key": previous_list + [StringTemplate("{VARIABLE_NAME}")]}
        True

    :Inplace union:

    The inplace union operator `|=` can be used to set multiple keys at once:

    >>> cfg = TemplateDict({})
    >>> cgf |= {"keyA": "{VARIABLE_NAME}", "keyB": "{OTHER_NAME}"}
    >>> print(cfg)
        {"keyA": StringTemplate("{VARIABLE_NAME}"), "keyB": StringTemplate("{OTHER_NAME}")}
    """

    def __init__(self, data):
        """Proxy class around a provided mapping.

        This is itended to ease configuration templating.

        :param mapping: Existing mapping holding entries to wrap.
        :type mapping: :class:`abc.MutableMapping`
        """
        self.data = data

    def __getitem__(self, keys):
        if not utils.is_nonstring_sequence(keys):
            keys = (keys,)

        config = self.data

        for key in keys:
            if key not in config:
                raise KeyError(f"Index [{', '.join(keys)}] does not exist.")
            config = config[key]

        if isinstance(config, abc.MutableMapping):
            return TemplateDict(config)
        elif utils.is_nonstring_sequence(config):
            return TemplateList(config)
        else:
            return config

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        return utils.make_repr(self, "data")

    def __delitem__(self, key):
        raise NotImplementedError(
            f"{type(self)} do not support __delitem__, add-only dict-like."
        )

    def __setitem__(self, keys, value):
        if utils.is_nonstring_sequence(keys):
            config = self.data

            for key in keys[:-1]:
                if key not in config:
                    config[key] = {}
                config = config[key]

            self[keys[:-1]][keys[-1]] = value
            return

        value, transform = Transform._get_transform(value)

        if isinstance(value, abc.Mapping):
            if keys not in self.data:
                self.data[keys] = {}

            assert not utils.is_nonstring_sequence(
                self.data[keys]
            ), f"{self.data[keys]} is already a sequence, cannot set to a dict."
            for key, value in value.items():
                TemplateDict(self.data[keys])[key] = Transform._get_transform(
                    value, transform
                )

        elif utils.is_nonstring_sequence(value):
            if keys not in self.data:
                self.data[keys] = []

            assert not isinstance(
                self.data[keys], abc.Mapping
            ), f"{self.data[keys]} is already a mapping, cannot set to a list."
            TemplateList(self.data[keys]).extend(
                Transform._get_transform(value, transform)
            )

        else:
            if keys in self.data:
                self.data[keys] = MultiStringTemplate(
                    Transform._get_transform(value, transform), self.data[keys]
                )
            else:
                self.data[keys] = Transform._get_value(value, transform)

    def update(self, other=(), /, **kwds):
        other, transform_other = Transform._get_transform(other)

        if hasattr(other, "keys") and callable(other.keys):
            for key in other.keys():
                self[key] = Transform._get_transform(other[key], transform_other)
        else:
            for key, value in other:
                self[key] = Transform._get_transform(value, transform_other)

        kwds, transform_kwds = Transform._get_transform(kwds)

        for key, value in kwds.items():
            self[key] = Transform._get_transform(value, transform_kwds)

    def __ior__(self, other):
        self.update(other)
        return self


class TemplateList(abc.MutableSequence):
    """Proxy class around a provided mapping.

    This is itended to ease configuration templating.

    See :class:`TemplateDict` for usage details.
    """

    def __init__(self, data):
        """Proxy class around a provided sequence.

        This is itended to ease configuration templating.

        :param mapping: Existing mapping holding entries to wrap.
        :type mapping: :class:`abc.MutableSequence`
        """
        self.data = data

    def __getitem__(self, index):
        if utils.is_nonstring_sequence(self.data[index]):
            return TemplateList(self.data[index])
        elif isinstance(self.data[index], abc.MutableMapping):
            return TemplateDict(self.data[index])
        else:
            return self.data[index]

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        return utils.make_repr(self, "data")

    def __eq__(self, other):
        return utils.attrs_eq(self, other, "data")

    def __setitem__(self, index, value):
        raise NotImplementedError(
            f"{type(self)} do not support __setitem__, add-only list-like."
        )

    def __delitem__(self, value):
        raise NotImplementedError(
            f"{type(self)} do not support del, add-only list-like."
        )

    def insert(self, index, value):
        value, transform = Transform._get_transform(value)

        if utils.is_nonstring_sequence(value):
            self.data.insert(index, [])
            TemplateList(self.data[index]).extend(
                Transform._get_transform(value, transform)
            )
        elif isinstance(value, abc.Mapping):
            self.data.insert(index, {})
            TemplateDict(self.data[index]).update(
                Transform._get_transform(value, transform)
            )
        else:
            new_value = Transform._get_value(value, transform)
            if new_value not in self.data:
                self.data.insert(index, new_value)

    def extend(self, other):
        other, transform = Transform._get_transform(other)

        for value in other:
            self.append(Transform._get_transform(value, transform))


class FormatterEnviron(abc.Mapping):
    """Class wrapping an environ and providing an interface to render templates.

    It can be used to render template strings.
    """

    def __init__(self, sanitizer=None, value_error=True):
        """Class wrapping an environ and providing an interface to render templates.

        :param sanitizer: An optionnal callable to sanitize the values given (key, value) pairs.
        :type sanitizer: :class:`function` or `None`, optionnal
        :param environ: Consider empty string value as an error.
        :type environ: :class:`bool`, optional
        """
        self.data = project.environ
        self._keys = set()
        self._sanitizer = sanitizer
        self._value_error = value_error

    def __contains__(self, key):
        if key not in self.data:
            self.data.__getitem__(key)

        return True

    def __getitem__(self, key):
        # Call to inner dict __getitem__ will create missing keys
        value = self.data[key]
        if self._value_error and not value:
            raise ValueError

        return self._sanitizer(key, value) if self._sanitizer else value

    def __iter__(self):
        return iter(self._keys)

    def __len__(self):
        return len(self._keys)

    def keys(self):
        return iter(self)

    def values(self):
        return (self[key] for key in self)

    def items(self):
        return zip(self.keys(), self.values())

    def format(self, format_string, **kwargs):  # noqa: A003
        r"""Render a format string.

        Variables will be request from the underlying environ, and undefined
        variables will be created. If `self._value_error` is `True` and an
        empty variable will cause the whole render result to be `None`.

        Additional variables can be specified using keyword arguments. They
        will be added to the environ, hence they will override environ values.

        :param template: A format string whose keyword argument will be substituted.
        :type template: :class:`str`
        :param \**kwargs: Additional variables that will override environ variables.
        :type \**kwargs: :class:`str`, optionnal
        :return: The rendered template or `None` if a context variable is empty.
        :rtype: :class:`str` or `None`
        """

        self._keys = {item[1] for item in Formatter().parse(format_string) if item[1]}
        for key in self:
            if key in kwargs:
                self.data[key] = kwargs[key]

        with contextlib.suppress(ValueError):
            return format_string.format(**self)
