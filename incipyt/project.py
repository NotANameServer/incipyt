"""TO-DO."""

import collections
import logging
import os
import sys
from collections import abc

import click

from incipyt._internal import templates

from incipyt._internal.utils import EnvValue, is_nonstring_sequence

logger = logging.getLogger(__name__)


class _Environ(collections.UserDict):
    """Manage environ variables using for substitutions in patterns.

    A :class:`Environ` object `environ` is a dictionnary initialized with
    system environ variables `os.environ`, a variable can be add like that:

    .. code-block::

        environ["VARIABLE_NAME"] = "something"

    However such a variable will not be considered in `environ` before being
    `confirmed`. Such confirmation will happen the first it is asked for:

    .. code-block::

        var_first = environ["VARIABLE_NAME"]
        # Prompt a message for confirmation of the value for `VARIABLE_NAME`
        var_second = environ["VARIABLE_NAME"]
        # As `VARIABLE_NAME` as been confirmed, don't ask anything

    Moreover, even if a specific variable hasn't been set, it can be asked for
    it anyway and it will be confirmed immediately. A variable can also be set
    and confirmed at the same time:

    .. code-block::

        environ["VARIABLE_NAME"] = EnvValue("something", confirmed=True)

    Note that if a variable has been set, it cannot be set again, except if
    explicitly specified:

    .. code-block::

        environ["VARIABLE_NAME"] = EnvValue("new_value", update=True)

    All iterative methods and in operator consider only `confirmed` variables.
    """

    def clear(self):
        self._confirmed = set()
        self.data = os.environ.copy()

        if "PYTHON_CMD" not in self.data:
            self.data["PYTHON_CMD"] = sys.executable
        self._confirmed.add("PYTHON_CMD")

    def __init__(self):
        self.clear()

    def __getitem__(self, key):
        if key not in self._confirmed:
            logger.debug("Missing environ variable %s, request it.", key)
            self.data[key] = self._prompt(key)
            self._confirmed.add(key)

        return self.data[key]

    def __setitem__(self, key, env_value):
        if not isinstance(env_value, EnvValue):
            env_value = EnvValue(env_value)

        if key in self.data and not env_value.update:
            raise ValueError(f"Environ variable {key} already exists, use update.")

        logger.debug("Set environ variable %s=%s.", key, env_value.value)
        self.data[key] = env_value.value
        if env_value.confirmed and key not in self._confirmed:
            self._confirmed.add(key)

    def __iter__(self):
        return iter(self._confirmed)

    def __contains__(self, key):
        return key in self._confirmed

    def keys(self):  # noqa: D102
        return self._confirmed

    def values(self):  # noqa: D102
        return [self.data[key] for key in self._confirmed]

    def items(self):  # noqa: D102
        return [(key, self.data[key]) for key in self._confirmed]

    def getitems_sanitized(self, keys, sanitizer=None):
        """Get multiple items at once and sanitize them.

        See also :func:`incipyt.system.Environment.__getitem__`, which will be
        used to pull each key from the environment.

        :param keys: Required environment keys. If a key is `None`, it will be ignored.
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

    def _prompt(self, key):
        return click.prompt(
            key.replace("_", " ").lower().capitalize(),
            default=self.data[key] if key in self.data else "",
            type=str,
        )

    def __ior__(self, other):
        self.update(other)
        return self


environ = _Environ()


class _Structure:
    """Represents all configuration and template files to commit for the new project.

    An instance internally stores mappables between path objects and template
    files or dictionaries modeling configuration files.

    Functions :meth:`get_configuration` and :meth:`register_template` add
    respectively configuration dictionary and template to the instance.

    When the project structure is finally ready, functions :meth:`mkdir` :meth:`commit`
    can be used to write folder and files in a new folder after substituting
    variables in path and files using an :class:`incipyt.project.Environ`.
    """

    def clear(self):
        self._configurations = {}

    def __init__(self):
        self.clear()

    def get_config_dict(self, config_root):
        """Get a configuration dictionary associated to the relative path `config_root`.

        :param config_root: Relative path of the configuration file.
        :type config_root: :class:`pathlib.Path`
        :return: A reference to the configuration dictionary
        :rtype: :class:`incipyt._internal.templates.TempateDict`
        """
        if config_root not in self._configurations:
            logger.debug(
                "Register configuration %s in project structure.", str(config_root)
            )
            self._configurations[config_root] = {}

        if not isinstance(self._configurations[config_root], abc.MutableMapping):
            raise TypeError(f"{config_root} is not a dict.")
        return templates.TemplateDict(self._configurations[config_root])

    def get_config_list(self, config_root):
        """Get a configuration list associated to the relative path `config_root`.

        :param config_root: Relative path of the configuration file.
        :type config_root: :class:`pathlib.Path`
        :return: A reference to the configuration list
        :rtype: :class:`incipyt._internal.templates.TempateList`
        """
        if config_root not in self._configurations:
            logger.debug(
                "Register configuration %s in project structure.", str(config_root)
            )
            self._configurations[config_root] = []

        if not is_nonstring_sequence(self._configurations[config_root]):
            raise TypeError(f"{config_root} is not a list.")
        return templates.TemplateList(self._configurations[config_root])

    def commit(self):
        """Commit current project structure on disk.

        :raises RuntimeError: If one of the configuration file already exists.
        """
        for config_root, config in self._configurations.items():
            logger.info("Process environ variables for %s.", str(config_root))
            _Structure._visit(config)

        for config_root, config in self._configurations.items():
            logger.info("Write configuration file %s.", str(config_root))
            config_root.dump_in(config)

    def mkdir(self, workon):
        """Make all directories of the project structure in workon.

        :param workon: Work-on path.
        :type workon: :class:`pathlib.Path`
        """
        for config_root in self._configurations:
            logger.debug("Commit %s path.", str(config_root))
            config_root.commit(workon)

        for config_root in self._configurations:
            logger.info("Mkdir folders for %s.", str(config_root))
            config_root.mkdir()

    @staticmethod
    def _visit(template):
        """Visit the `template` nested-dictionary structure.

        All :class:`incipyt._internal.templates.Formattable` values of the template dictionary will be
        evaluated and replaced by their results. All nested structures will be recursively
        visited and processed too.

        :param template: The template dictionary or list to visit.
        :type template: :class:`collections.abc.MutableMapping` of :class:`collections.abc.MutableSequence`
        """
        if is_nonstring_sequence(template):
            for index, value in enumerate(template):
                if isinstance(value, templates.Formattable):
                    template[index] = value.format()
                else:
                    _Structure._visit(value)
                if not template[index]:
                    template[index] = None

            while None in template:
                template.remove(None)

        elif isinstance(template, abc.MutableMapping):  # noqa: SIM106
            for key, value in template.items():
                logger.debug("Visit %s to process environ variables.", key)

                if isinstance(value, templates.Formattable):
                    template[key] = value.format()
                else:
                    _Structure._visit(value)
                if not template[key]:
                    template[key] = None

            for key in [key for key, value in template.items() if value is None]:
                del template[key]

        else:
            raise AssertionError(f"{type(template)} do not support visitation.")


structure = _Structure()
