"""TO-DO."""

import collections
import collections.abc
import dataclasses
import logging
import os
import subprocess
import sys

import click

from incipyt._internal import templates

from incipyt._internal.utils import EnvValue

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class _Python:
    variable: str = "PYTHON_CMD"

    @property
    def requires(self):
        from incipyt._internal.templates import Requires

        return Requires(f"{{{self.variable}}}")


python = _Python()


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

        if python.variable not in self.data:
            self.data[python.variable] = sys.executable
        self._confirmed.add(python.variable)

    def __init__(self):
        self.clear()

    def __getitem__(self, key):
        if key not in self.data:
            logger.debug("Missing environ variable %s, request it.", key)
            self.data[key] = self._requests(key)

        return self.data[key]

    def __setitem__(self, key, env_value):
        if not isinstance(env_value, EnvValue):
            env_value = EnvValue(env_value)

        if key in self.data and not env_value.update:
            raise RuntimeError(f"Environ variable {key} already exists, use update.")

        logger.debug("Set environ variable %s=%s.", key, env_value.value)
        self.data[key] = env_value.value
        if env_value.confirmed and key not in self._confirmed:
            self._confirmed.add(key)

    def __iter__(self):
        return iter(self._confirmed)

    def _requests(self, key):
        return click.prompt(
            key.replace("_", " ").lower().capitalize(),
            default=self.data[key] if key in self.data else "",
            type=str,
        )


environ = _Environ()


def run(args, **kwargs):
    r"""Run a command after substitution using the environ.

    :param args: List of the command elements.
    :type args: :class:`list`
    :param \**kwargs: Other options forwarded to `subprocess.run`
    :return: Represents a process that has finished
    :rtype: :class:`subprocess.CompletedProcess`
    """
    formatted = [arg() if callable(arg) else arg for arg in args]
    logger.info(" ".join(formatted))
    result = subprocess.run(formatted, capture_output=True, check=True, **kwargs)
    logger.info(result.stdout.decode())
    return result


class Hierarchy:
    """Represents all configuration and template files to commit for the new project.

    An instance internally stores mappables between path objects and template
    files or dictionaries modeling configuration files.

    Functions :meth:`get_configuration` and :meth:`register_template` add
    respectively configuration dictionary and template to the instance.

    When the hierarchy is finally ready, functions :meth:`mkdir` :meth:`commit`
    can be used to write folder and files in a new folder after substituting
    variables in path and files using an :class:`incipyt.project.Environ`.
    """

    def __init__(self):
        self._configurations = {}
        self._templates = {}

    def get_configuration(self, config_root):
        """Get a configuration dictionary associated to the relative path `config_root`.

        :param config_root: Relative path of the configuration file.
        :type config_root: :class:`pathlib.PurePath`
        :return: A reference to the configuration dictionary
        :rtype: :class:`dict`
        """
        if config_root not in self._configurations:
            logger.debug(
                "Register configuration %s in hierarchy %d.", str(config_root), id(self)
            )
            self._configurations[config_root] = {}

        return templates.TemplateDict(self._configurations[config_root])

    def register_template(self, template_root, template):
        """Register a Jinja template associated to the relative path `config_root`.

        :param template_root: Relative path of the configuration file.
        :type template_root: :class:`pathlib.PurePath`
        :param template: A Jinja template to register.
        :type template: :class:`jinja2.Template`
        :raises RuntimeError: If `template_root` already registered.
        """
        if template_root in self._templates:
            raise RuntimeError("Template %s already exists.", str(template_root))

        logger.debug(
            "Register template %s in hierarchy %d.", str(template_root), id(self)
        )
        self._templates[template_root] = template

    def commit(self):
        """Commit current hierarchy on disk.

        :raises RuntimeError: If one of the configuration file already exists.
        """
        visitor = templates.TemplateVisitor()
        for config_root, config in self._configurations.items():
            logger.info("Process environ variables for %s.", str(config_root))
            visitor(config)

        for config_root, config in self._configurations.items():
            logger.info("Write configuration file %s.", str(config_root))
            config_root.dump_in(config)

        for template_root, template in self._templates.items():
            logger.info("Write template file %s.", str(template_root))
            template_root.dump_in(template)

    def mkdir(self, workon):
        """Make all directories of the hierarchy in workon.

        :param workon: Work-on path.
        :type workon: :class:`pathlib.Path`
        """
        for config_root in self._configurations:
            logger.debug("Commit %s path.", str(config_root))
            config_root.commit(workon)

        for template_root in self._templates:
            logger.debug("Commit template file %s.", str(template_root))
            template_root.commit(workon)

        for config_root in self._configurations:
            logger.info("Mkdir folders for %s.", str(config_root))
            config_root.mkdir_in()

        for template_root in self._templates:
            logger.info("Mkdir folders for %s.", str(template_root))
            template_root.mkdir_in()
