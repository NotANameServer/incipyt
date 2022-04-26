"""This module contains classes related to template definition and rendering.

Incipyt mainly uses two kinds of templates: bare template strings that behave
like builtin Python string formatting. It also provides special wrappers to
allow easier templating of collections data structures, such as dict-like
template objects.
"""

import contextlib
import logging
from abc import ABCMeta, abstractmethod
from collections import abc
from string import Formatter

import click

from incipyt import project
from incipyt._internal import utils

logger = logging.getLogger(__name__)


class Formattable(metaclass=ABCMeta):
    @abstractmethod
    def format(self):  # noqa: A003
        raise NotImplementedError


class StringTemplate(Formattable):
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

    @classmethod
    def wrap(cls, value):
        return value if isinstance(value, Formattable) else cls(value)


class ChoiceTemplate(Formattable):
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
        :type tail: :class:`incipyt._intternal.templates.ChoiceTemplate` or any bare value
        """
        self._values = (
            {StringTemplate.wrap(head)} | tail._values
            if isinstance(tail, ChoiceTemplate)
            else {
                StringTemplate.wrap(head),
                StringTemplate.wrap(tail),
            }
        )

    def format(self):  # noqa: A003
        """Ask the user to pick a value using the command line interface.

        If it is :class:`incipyt._internal.templates.Formattable`, it will be formatted.

        :return: The user-choosen value.
        """
        return click.prompt(
            "Conflicting configuration, choose between",
            type=click.Choice(
                [
                    value.format() if isinstance(value, Formattable) else value
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
        :rtype: :class:`incipyt._intternal.templates.ChoiceTemplate`
        """
        instance = cls.__new__(cls)
        instance._values = {StringTemplate.wrap(arg) for arg in args}
        return instance


class TemplateDict(abc.MutableMapping):
    """Proxy class around a provided mapping.

    This is itended to ease configuration templating.

    :Class instanciation:

    >>> cfg = TemplateDict({})

    :Setting values:

    Following exemples assume `cfg` is a :class:`incipyt._internal.templates.StringTemplate` around an empty `dict`.

    Bare values will be wrapped into :class:`incipyt._internal.templates.StringTemplate`
    automatically :

    >>> cfg["key"] = "{VARIABLE_NAME}"
    >>> print(cfg)
        TemplateDict(data={'key': StringTemplate(format_string={VARIABLE_NAME})})

    :class:`incipyt._internal.templates.Formattable` will be kept as-is:

    >>> cfg["key"] = a_formattable
    >>> print(cfg)
        TemplateDict(data={'key': a_formattable})

    Collections are supported as well:

    >>> cfg["key"] = ["{VARIABLE_NAME}"]
    >>> print(cfg)
        TemplateDict(data={'key': [StringTemplate("{VARIABLE_NAME}")]})

    >>> cfg["key"] = {"keyB": "{VARIABLE_NAME}"}
    >>> print(cfg)
        TemplateDict(data={'key': {'keyB': StringTemplate(format_string={VARIABLE_NAME})}})

    :Nested keys:

    To ease nested structure definition, the following syntax is supported:

    >>> cfg["keyA", "keyB"] = "{VARIABLE_NAME}"
    >>> print(cfg)
        TemplateDict(data={'keyA': {'keyB': StringTemplate(format_string={VARIABLE_NAME})}})

    :Multiple values:

    Instances of :class:`incipyt._internal.templates.ChoiceTemplate` will be
    created in case of value overrides. For instance, if `previous_value` is a
    :class:`incipyt._internal.templates.Formattable`:

    >>> cfg = TemplateDict({"key": previous_value})
    >>> cfg["key"] = "{VARIABLE_NAME}"
    >>> print(cfg)
        TemplateDict(data={'key': ChoiceTemplate({StringTemplate(format_string={VARIABLE_NAME}), previous_value})})

    If `previous_list` is a mutable sequence, any value not already present in
    it will be appended:

    >>> cfg = TemplateDict({"key": previous_list})
    >>> cfg["key"] = ["{VARIABLE_NAME}"]
    >>> cfg == {"key": previous_list + [StringTemplate("{VARIABLE_NAME}")]}
        True

    :Inplace union:

    The inplace union operator `|=` can be used to set multiple keys at once:

    >>> cfg = TemplateDict({})
    >>> cgf |= {"keyA": "{VARIABLE_NAME}", "keyB": "{OTHER_NAME}"}
    >>> print(cfg)
        TemplateDict(data={'keyA': StringTemplate(format_string={VARIABLE_NAME}), 'keyB': StringTemplate(format_string={OTHER_NAME})})
    """

    def __init__(self, data):
        """Proxy class around a provided mapping.

        This is itended to ease configuration templating.

        :param mapping: Existing mapping holding entries to wrap.
        :type mapping: :class:`collections.abc.MutableMapping`
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

        if isinstance(value, abc.Mapping):
            if keys not in self.data:
                self.data[keys] = {}

            if utils.is_nonstring_sequence(self.data[keys]):
                raise TypeError(
                    f"{self.data[keys]}) is already a sequence, cannot set to a dict."
                )
            for k, v in value.items():
                TemplateDict(self.data[keys])[k] = v

        elif utils.is_nonstring_sequence(value):
            if keys not in self.data:
                self.data[keys] = []

            if isinstance(self.data[keys], abc.Mapping):
                raise TypeError(
                    f"{self.data[keys]} is already a mapping, cannot set to a list."
                )
            TemplateList(self.data[keys]).extend(value)

        else:
            if keys in self.data:
                self.data[keys] = ChoiceTemplate(value, self.data[keys])
            else:
                self.data[keys] = StringTemplate.wrap(value)

    def __ior__(self, other):
        self.update(other)
        return self


class TemplateList(abc.MutableSequence):
    """Proxy class around a provided mapping.

    This is itended to ease configuration templating.

    See :class:`incipyt._internal.templates.StringTemplate` for usage details.
    """

    def __init__(self, data):
        """Proxy class around a provided sequence.

        This is itended to ease configuration templating.

        :param mapping: Existing mapping holding entries to wrap.
        :type mapping: :class:`collections.abc.MutableSequence`
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
        if utils.is_nonstring_sequence(value):
            self.data.insert(index, [])
            TemplateList(self.data[index]).extend(value)
        elif isinstance(value, abc.Mapping):
            self.data.insert(index, {})
            TemplateDict(self.data[index]).update(value)
        else:
            new_value = StringTemplate.wrap(value)
            if new_value not in self.data:
                self.data.insert(index, new_value)


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
