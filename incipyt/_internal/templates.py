"""This module contains classes related to template definition and rendering.

Incipyt mainly uses two kinds of templates: bare template strings that behave
like builtin Python string formatting and Jinja 2 templates. It also provides
special wrappers to allow easier templating of collections data structures,
such as dict-like template objects.
"""

import collections
import contextlib
import logging
from string import Formatter
from typing import Any, Callable, NamedTuple

import click

from incipyt._internal import utils

logger = logging.getLogger(__name__)


class PythonEnv(NamedTuple):
    variable: str = "PYTHON_CMD"

    @property
    def requires(self):
        return Requires(f"{{{self.variable}}}")


class Transform(NamedTuple):
    """Compound type containing a value and a "transform".

    A transform is a callable that will be used to transform the value. If no
    transform is provided, the identity function will be used, hence the value
    will not be transformed.
    """

    value: Any
    transform: Callable = lambda x: x


class Requires:
    """This class acts like a wrapper around a template string.

    When an instance is called, it renders the underlying template string using
    environment values and overrides.
    """

    def __init__(self, template, confirmed=False, sanitizer=None, **kwargs):
        r"""This class acts like a wrapper around a template string.

        When an instance is called, it renders the underlying template string
        using environment values and overrides.

        :param template: A template string whose placeholders will be interpolated.
        :type template: :class:`str`
        :param confirmed: Confirmed status for new variables from keyword args.
        :type confirmed: :class:`bool`, optionnal
        :param sanitizer: An optionnal callable to sanitize the values given (key, value) pairs.
        :type sanitizer: :class:`function` or `None`, optionnal
        :param \**kwargs: Variables overrides that will be used for rendering and pushed to the environment. Automatically wrapped in :class:`incipyt._internal.utils.EnvValue` if needed.
        :type \**kwargs: :class:`str`, optionnal
        """
        self._confirmed = confirmed
        self._sanitizer = sanitizer
        self._template = template
        self._kwargs = kwargs

    def __repr__(self):
        return utils.make_repr(
            self,
            template=self._template,
            confirmed=self._confirmed,
            sanitizer=self._sanitizer,
            kwargs=self._kwargs,
        )

    def __eq__(self, other):
        return utils.attrs_eq(
            self, other, "_template", "_confirmed", "_sanitizer", "_kwargs"
        )

    def __call__(self, environment):
        """Render the underlying template string using variables from a given
        environment.

        :param environment: Environment to use variables from.
        :type environment: :class:`incipyt.system.Environment`
        :return: The interpolated template string.
        :rtype: :class:`str`
        """
        return RenderContext(environment, sanitizer=self._sanitizer).render_string(
            self._template,
            **{
                key: (
                    value
                    if isinstance(value, utils.EnvValue)
                    else utils.EnvValue(value, confirmed=self._confirmed)
                )
                for key, value in self._kwargs.items()
            },
        )


class MultipleValues:
    """Class to hold multiple values for a single key.

    When an instance is called, the user will be asked to pick a value using
    the command line interface.
    """

    def __init__(self, head, tail):
        """Class to hold multiple values for a single key.

        When an instance is called, the user will be asked to pick a value
        using the command line interface.

        :param head: Entry to put a the head of the stack.
        :type tail: :class:str
        :param tail: Tail of the stack.
        :type tail: :class:`incipyt._intternal.templates.MultipleValues` or any bare value
        """
        self._values = (
            [head] + tail._values if isinstance(tail, MultipleValues) else [head, tail]
        )

    def __call__(self, environment):
        """Ask the user to pick a value using the command line interface.

        If it is callable, it will be evaluated.

        :param environment: Environment to pass to callables.
        :type environment: :class:`incipyt.system.Environment`
        :return: The user-choosen value.
        """
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
        return utils.attrs_eq(self, other, "_values")

    @classmethod
    def from_items(cls, *args):
        r"""Build a class instance from any number of bare values.

        :param \*args: Entries to wrap.
        :return: New class instance
        :rtype: :class:`incipyt._intternal.templates.MultipleValues`
        """
        instance = cls.__new__(cls)
        instance._values = list(args)
        return instance


class TemplateDict(collections.UserDict):
    """Proxy class around a provided mapping.

    This is itended to ease configuration templating.

    :Class instanciation:

    >>> cfg = TemplateDict({})

    :Setting values:

    Following exemples assume `cfg` is a `TemplateDict` around an empty `dict`.

    Bare values will be wrapped into :class:`incipyt._internal.templates.Requires`
    automatically :

    >>> cfg["key"] = "{VARIABLE_NAME}"
    >>> print(cfg)
        {"key": Requires("{VARIABLE_NAME}")}

    Callables will be kept as-is:

    >>> cfg["key"] = a_callable
    >>> print(cfg)
        {"key": a_callable}

    Values of :class:`incipyt._internal.templates.Transform` instances will be
    evaluated accordingly to their transform:

    >>> cfg["key"] = Transform("{VARIABLE_NAME}", a_callable)
    >>> print(cfg)
        {"key": a_callable("{VARIABLE_NAME}")}

    Not giving an explicit callable to
    :class:`incipyt._internal.templates.Transform` will default to the identity
    function and keep the values as-is:

    >>> cfg["key"] = Transform("Something")
    >>> print(cfg)
        {"key": "Something"}

    Collections are supported as well:

    >>> cfg["key"] = ["{VARIABLE_NAME}"]
    >>> print(cfg)
        {"key": [Requires("{VARIABLE_NAME}")]}

    >>> cfg["key"] = {"keyB": "{VARIABLE_NAME}"}
    >>> print(cfg)
        {"key": {"keyB": Requires("{VARIABLE_NAME}")}}

    :Nested keys:

    To ease nested structure definition, the following syntax is supported:

    >>> cfg["keyA", "keyB"] = "{VARIABLE_NAME}"
    >>> print(cfg)
        {"keyA": {"keyB": Requires("{VARIABLE_NAME}")}}

    :Multiple values:

    Instances of :class:`incipyt._internal.templates.MultipleValues` will be
    created in case of value overrides. For instance, if `previous_value` is
    callable:

    >>> cfg == TemplateDict({"key": previous_value})
    >>> cfg["key"] = "{VARIABLE_NAME}"
    >>> print(cfg)
        {"key": MulitpleValues(Requires("{VARIABLE_NAME}"), previous_value)}

    If `previous_list` is a mutable sequence, any value not already present in
    it will be appended:

    >>> cfg == TemplateDict({"key": previous_list})
    >>> cfg["key"] = ["{VARIABLE_NAME}"]
    >>> cfg == {"key": previous_list + [Requires("{VARIABLE_NAME}")]}
        True

    :Inplace union:

    The inplace union operator `|=` can be used to set multiple keys at once:

    >>> cfg = TemplateDict({})
    >>> cgf |= {"keyA": "{VARIABLE_NAME}", "keyB": "{OTHER_NAME}"}
    >>> print(cfg)
        {"keyA": Requires("{VARIABLE_NAME}"), "keyB": Requires("{OTHER_NAME}")}
    """

    def __init__(self, mapping):
        """Proxy class around a provided mapping.

        This is itended to ease configuration templating.

        :param mapping: Existing mapping holding entries to wrap.
        :type mapping: :class:`collections.abc.MutableMapping`
        """
        self.data = mapping

    def __setitem__(self, keys, value):
        value, transform = self._get_transform(value)
        if not utils.is_nonstring_sequence(keys):
            keys = (keys,)

        if isinstance(value, collections.abc.Mapping):
            for k, v in value.items():
                self[keys + (k,)] = self._get_transform(v, transform)
            return

        config = self.data

        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        key = keys[-1]

        if utils.is_nonstring_sequence(value):
            if key not in config:
                config[key] = []

            assert not isinstance(
                config[key], collections.abc.Mapping
            ), f"{config[key]} is already a mapping, cannot set to a sequence."

            for v in value:
                if v not in config[key]:
                    config[key].append(self._get_value(v, transform))

        else:
            value = self._get_value(value, transform)
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
            self[key] = self._get_transform(value, transform)
        return self

    def __or__(self, other):
        raise NotImplementedError(
            f"{type(self)} do not support |, use self.data | or |=."
        )

    @staticmethod
    def _get_transform(value, transform=None):
        """Wrap `value` in :class:`incipyt._internal.templates.Transform` if needed.

        Wrapping with a `None` transform will result in
        :class:`incipyt._internal.templates.Requires` being used.

        :param value: A bare value or already wrapped value.
        :type value: :class:`str` or :class:`incipyt._internal.templates.Transform`
        :param transform: Callable to be wrapped.
        :type transform: :class:`function` or `None`, optionnal
        :return: Original or wrapped `value`.
        :rtype: :class:`incipyt._internal.templates.Transform`
        """
        if isinstance(value, Transform):
            assert callable(value[1]), "Second Transform element has to be callable."
            return value
        return Transform(value, transform if transform else Requires)

    @staticmethod
    def _get_value(value, transform):
        """Transform a value according to its wrapped transformation or fallback.

        :param value: Value to transform. If it is callable, it will not be transformed.
        :type value: :class:`str` or :class:`function` or :class:`incipyt._internal.templates.Transform`
        :param transform: Fallback callable for transformation.
        :type transform: :class:`function`
        :return: Transformed `value`.
        :rtype: :class:`str` or :class:`callable`
        """
        if isinstance(value, Transform):
            return value.transform(value.value)
        if callable(value):
            return value
        return transform(value)


class TemplateVisitor:
    """Class to visit a template dictionary and process it according to environment variables.

    All callable values of the template dictionary will be evaluated and
    replaced by their results. All nested structures will be recursively
    visited and processed too.
    """

    def __init__(self, environment):
        """Class to visit a template dictionary and process it according to environment variables.

        :param environment: Environment to pass to callables.
        :type environment: :class:`incipyt.system.Environment`
        """
        self.environment = environment

    def __call__(self, template):
        """Visit the `template` nested-dictionary structure.

        :param template: The template dictionary to visit.
        :type template: :class:`collections.abc.Mapping`
        """
        for key, value in template.items():
            logger.debug(f"Visit {key} to process environment variables.")

            if callable(value):
                template[key] = value(self.environment)

            elif isinstance(value, collections.abc.MutableMapping):
                self(value)
                if not value:
                    template[key] = None

            elif isinstance(value, collections.abc.MutableSequence):
                for index, element in enumerate(value):
                    if callable(element):
                        value[index] = element(self.environment)
                    if isinstance(element, collections.abc.MutableMapping):
                        self(element)
                if all(element is None for element in value):
                    template[key] = None

        for key in [key for key, value in template.items() if value is None]:
            del template[key]


class RenderContext(collections.abc.Mapping):
    """Class wrapping an environment and providing an interface to render templates.

    It can be used to render template strings and Jinja templates.
    """

    def __init__(self, environment, sanitizer=None):
        """Class wrapping an environment and providing an interface to render templates.

        :param environment: Environment to get variables from.
        :type environment: :class:`incipyt.system.Environment`
        :param sanitizer: An optionnal callable to sanitize the values given (key, value) pairs.
        :type sanitizer: :class:`function` or `None`, optionnal
        """
        self.data = environment
        self._sanitizer = sanitizer
        self._keys = set()

    def __contains__(self, key):
        if key not in self.data:
            self.data.__getitem__(key)

        return True

    def __getitem__(self, key):
        # Call to inner dict __getitem__ will create missing keys
        value = self.data[key]
        if not value:
            raise ValueError

        return self._sanitizer(key, value) if self._sanitizer else value

    def __iter__(self):
        return iter(self._keys)

    def __len__(self):
        return len(self._keys)

    def keys(self):
        return self._keys

    def values(self):
        return [self[key] for key in self._keys]

    def items(self):
        return [(key, self[key]) for key in self._keys]

    def render_template(self, template):
        """Render a Jinja template.

        Variables will be request from the underlying environment, and
        undefined variables will be created. An empty variable will cause the
        whole render result to be `None`.

        :param template: Jinja template to render.
        :type template: :class:`jinja2.Template`
        :return: The rendered template or `None` if a context variable is empty.
        :rtype: :class:`str` or `None`
        """
        with contextlib.suppress(ValueError):
            return "".join(
                template.root_render_func(template.new_context(self, shared=True))
            )

    def render_string(self, template, **kwargs):
        r"""Render a template string.

        Variables will be request from the underlying environment, and
        undefined variables will be created. An empty variable will cause the
        whole render result to be `None`.

        Additional variables can be specified using keyword arguments. They
        will be added to the environment, hence they will override environment
        values.

        :param template: Template string to render.
        :type template: :class:`str`
        :param \**kwargs: Additional variables that will override environment variables.
        :type \**kwargs: :class:`str`, optionnal
        :return: The rendered template or `None` if a context variable is empty.
        :rtype: :class:`str` or `None`
        """

        self._keys = {item[1] for item in Formatter().parse(template) if item[1]}
        for key in self:
            if key in kwargs:
                self.data[key] = kwargs[key]

        with contextlib.suppress(ValueError):
            return template.format(**self)
