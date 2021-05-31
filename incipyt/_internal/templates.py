import collections
import logging
from string import Formatter
from typing import Any, Callable, NamedTuple

import click

from incipyt._internal import utils
from incipyt._internal.utils import EnvValue

logger = logging.getLogger(__name__)


class PythonEnv(NamedTuple):
    variable: str = "PYTHON_CMD"

    @property
    def requires(self):
        return Requires(f"{{{self.variable}}}")


class Transform(NamedTuple):
    value: Any
    transform: Callable = lambda x: x


class Requires:
    def __init__(self, template, confirmed=False, sanitizer=None, **kwargs):
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
        context = RenderContext(environment)
        template = TemplateString(self._template)

        for key in template.keys:
            if key in self._kwargs:
                environment[key] = EnvValue(
                    self._kwargs[key], confirmed=self._confirmed
                )

        return context.render_string(template, self._sanitizer)


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
        return utils.attrs_eq(self, other, "_values")

    @classmethod
    def from_items(cls, *args):
        instance = cls.__new__(cls)
        instance._values = list(args)
        return instance


class TemplateDict(collections.UserDict):
    """This class will act like a proxy around a provided mapping.

    .. code-block::

        # configuration == {}
        configuration["keyA"] = "{VARIABLE_NAME}"
        # configuration == {"keyA": Requires("{VARIABLE_NAME}")}

        # configuration == {}
        configuration["keyA"] = a_callable
        # configuration == {"keyA": a_callable}

        # configuration == {}
        configuration["keyA"] = Transform("{VARIABLE_NAME}", a_function)
        # configuration == {"keyA": a_function("{VARIABLE_NAME}")}

        # configuration == {}
        configuration["keyA", "keyB"] = "{VARIABLE_NAME}"
        # configuration == {"keyA": {"keyB": Requires("{VARIABLE_NAME}")} }

        # configuration == {}
        configuration["keyA"] = ["{VARIABLE_NAME}"]
        # configuration == {"keyA": [Requires("{VARIABLE_NAME}")]}

        # configuration == {}
        configuration["keyA"] = {"keyB": "{VARIABLE_NAME}"}
        # configuration == {"keyA": {"keyB": Requires("{VARIABLE_NAME}")} }

        # configuration == {"keyA": previous_value}
        configuration["keyA"] = "{VARIABLE_NAME}"
        # if previous_value is a callable (assertion)
        # configuration == {"keyA": MulitpleValues(Requires("{VARIABLE_NAME}"), previous_value)}

        # configuration == {"keyA": previous_list}
        configuration["keyA"] = ["{VARIABLE_NAME}"]
        # if previous_list is a list (assertion) and not already in previous_list
        # configuration == {"keyA": previous_list + [Requires("{VARIABLE_NAME}")]}
    """

    def __init__(self, mapping):
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
        """Wrap value in :class:`incipyt._internal.templates.Transform` if needed.

        :param value: A raw or wrapped string.
        :type value: :class:`str` or :class:`incipyt._internal.templates.Transform`
        :return: `value` itself or wrapped.
        :rtype: :class:`incipyt._internal.templates.Transform`
        """
        if isinstance(value, Transform):
            assert callable(value[1]), "Second Transform element has to be callable."
            return value
        return Transform(value, transform if transform else Requires)

    @staticmethod
    def _get_value(value, transform):
        """Transform a value according to wrapped transformation or fallback.

        :param value: Value to transform
        :type value: :class:`str` or :class:`callable` or :class:`incipyt._internal.templates.Transform`
        :param transform: Fallback function for transformation
        :type transform: :class:`callable`
        :return: `value` after transformation
        :rtype: :class:`str` or :class:`callable`
        """
        if isinstance(value, Transform):
            return value.transform(value.value)
        if callable(value):
            return value
        return transform(value)


class TemplateVisitor:
    """Visit the nested-dictionary structure `template` to process substitutions.

    For all callable values of the template dictionary, replace it by
    applying the substitution callback.
    For all nested dictionary values of the template dictionary,
    recursively apply this visitor.

    :param environment: The environment variables used to visit.
    :type environment: :class:`incipyt.system.Environment`
    :param template: The template dictionary to visit.
    :type template: :class:`dict`
    """

    def __init__(self, environment):
        self.environment = environment

    def __call__(self, template):
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


class TemplateString(collections.UserString):
    @property
    def keys(self):
        """Set of all variables the template string contains."""
        return {item[1] for item in Formatter().parse(self.data)}

    def render(self, context, sanitizer=None):
        """Interpolate the template string with variables from a given
        RenderContext.
        """
        variables = context.getitems_sanitized(self.keys, sanitizer)

        if all(variables.values()):
            return self.format(**variables)


class RenderContext(collections.UserDict):
    def __init__(self, env):
        self.data = env

    def __contains__(self, key):
        if key not in self.data:
            self[key]

        return True

    def __getitem__(self, key):
        # Explicit call to inner dict __getitem__ to create env keys
        return self.data[key]

    def getitems_sanitized(self, keys, sanitizer=None):
        """Get multiple items at once and sanitize them.

        See also :func:`incipyt.system.Environment.__getitem__`, which will be
        used to pull each key from the environment.

        :param keys: Required environment keys. If a key is `None`, it will be
        ignored.
        :type keys: :class:`collections.abc.Sequence`
        :param sanitizer: Will be called on key-value pairs to sanitize values.
        :type sanitizer: :class:`function`
        :return: Sanitized environment key-value pairs.
        :rtype: :class:`dict`
        """
        return {
            key: sanitizer(key, self[key]) if sanitizer else self[key]
            for key in keys
            if key is not None
        }

    def render_template(self, template):
        """Render a Jinja template."""
        return "".join(
            template.root_render_func(template.new_context(self, shared=True))
        )

    def render_string(self, template_string, sanitizer=None):
        """Render a TemplateString."""
        return template_string.render(self, sanitizer)
