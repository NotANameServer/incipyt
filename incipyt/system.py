"""TO-DO."""

import collections
import collections.abc
import logging
import os
import pathlib
import subprocess
import sys

import click

from incipyt._internal import templates
from incipyt._internal.templates import PythonEnv
from incipyt._internal.utils import EnvValue

logger = logging.getLogger(__name__)


class Environment(collections.UserDict):
    """Manage environment variables using for substitutions in patterns.

    A :class:`Environment` object `env` is a dictionnary initialized with
    system environment variables `os.env`, a variable can be add like that:

    .. code-block::

        env["VARIABLE_NAME"] = "something"

    However such a variable will not be considered in `env` before being
    `confirmed`. Such confirmation will happen the first it is asked for:

    .. code-block::

        var_first = env["VARIABLE_NAME"]
        # Prompt a message for confirmation of the value for `VARIABLE_NAME`
        var_second = env["VARIABLE_NAME"]
        # As `VARIABLE_NAME` as been confirmed, don't ask anything

    Moreover, even if a specific variable hasn't been set, it can be asked for
    it anyway and it will be confirmed immediately. A variable can also be set
    and confirmed at the same time:

    .. code-block::

        env["VARIABLE_NAME"] = EnvValue("something", confirmed=True)

    Note that if a variable has been set, it cannot be set again, except if
    explicitly specified:

    .. code-block::

        env["VARIABLE_NAME"] = EnvValue("new_value", update=True)

    All iterative methods and in operator consider only `confirmed` variables.
    """

    python = PythonEnv()

    @staticmethod
    def default_runner(command):
        """Run `command` using :func:`subprocess.run`.

        :param command: List of the command elements.
        :type command: :class:`list`
        :return: stdout docoded.
        :rtype: :class:`str`
        """
        completed_process = subprocess.run(command, capture_output=True, check=True)
        return completed_process.stdout.decode()

    def __init__(self, auto_confirm=False, runner=None):
        """Environment initializer.

        :param auto_confirm: Do not ask confirmation for variables with a default value.
        :type auto_confirm: :class:`bool`
        :param runner: Callable to run subprocess. Default if :func:`incipyt.system.Environment.default_runner`
        :type runner: :class:`callable`
        """
        self.auto_confirm = auto_confirm
        self.runner = runner if runner else self.default_runner

        self._confirmed = set()
        self.data = os.environ.copy()

        if self.python.variable not in self.data:
            self.data[self.python.variable] = sys.executable
        self._confirmed.add(self.python.variable)

    def __getitem__(self, key):
        if not self.auto_confirm and key not in self._confirmed:
            logger.debug(f"Environment variable {key} not confirmed, request it.")
            self.data[key] = self._requests(key)
            self._confirmed.add(key)
        elif self.auto_confirm and key not in self.data:
            logger.debug(f"Missing environment variable {key}, request it.")
            self.data[key] = self._requests(key)

        return self.data[key]

    def __setitem__(self, key, env_value):
        if not isinstance(env_value, EnvValue):
            env_value = EnvValue(env_value)

        if key in self.data and not env_value.update:
            raise RuntimeError(
                f"Environment variable {key} already exists, use update."
            )

        logger.debug(f"Set environment variable {key}={env_value.value}.")
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

    def run(self, command):
        """Run a command after substitution using the environment.

        :param command: List of the command elements.
        :type command: :class:`list`
        :return: stdout docoded.
        :rtype: :class:`str`
        """
        cmd = [c(self) if callable(c) else c for c in command]
        logger.info(" ".join(cmd))
        result = self.runner(cmd)
        logger.info(result)
        return result


class Hierarchy:
    """Represents all configuration and template files to commit for the new project.

    An instance internally stores mappables between path objects and template
    files or dictionaries modeling configuration files.

    Functions :meth:`get_configuration` and :meth:`register_template` add
    respectively configuration dictionary and template to the instance.

    When the hierarchy is finally ready, functions :meth:`mkdir` :meth:`commit`
    can be used to write folder and files in a new folder after substituting
    variables in path and files using an :class:`incipyt.system.Environment`.
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
                f"Register configuration {config_root} in hierarchy {id(self)}."
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
            raise RuntimeError(f"Template {template_root} already exists.")

        logger.debug(f"Register template {template_root} in hierarchy {id(self)}.")
        self._templates[template_root] = template

    def commit(self, environment):
        """Commit current hierarchy on disk.

        :param environment: Environment to use for substitution in pattern.
        :type environment: :class:`incipyt.system.Environment`
        :raises RuntimeError: If one of the configuration file already exists.
        """
        visitor = templates.TemplateVisitor(environment)
        for config_root, config in self._configurations.items():
            logger.info(f"Process environment variables for {config_root}.")
            visitor(config)

        for config_root, config in self._configurations.items():
            logger.info(f"Write configuration file {config_root}.")
            config_root.dump_in(config)

        for template_root, template in self._templates.items():
            logger.info(f"Write template file {template_root}.")
            template_root.dump_in(template)

    def mkdir(self, workon, environment):
        """Make all directories of the hierarchy in workon.

        :param workon: Work-on path.
        :type workon: :class:`pathlib.Path`
        :param environment: Environment to use for substitution in pattern.
        :type environment: :class:`incipyt.system.Environment`
        """
        for config_root in self._configurations:
            logger.debug(f"Commit {config_root} path.")
            config_root.commit(workon, environment)

        for template_root in self._templates:
            logger.debug(f"Commit template file {template_root}.")
            template_root.commit(workon, environment)

        for config_root in self._configurations:
            logger.info(f"Mkdir folders for {config_root}.")
            config_root.mkdir_in()

        for template_root in self._templates:
            logger.info(f"Mkdir folders for {template_root}.")
            template_root.mkdir_in()


def process_actions(workon, environment, actions):
    """Process a list of actions configuring required tools.

    Performs five steps:
    - Succesylly preform `add_to`function of actions to a new
    :class:`incipyt.system.Hierarchy`.
    - Make all directories.
    - Run all `pre` functions of actions.
    - Commit the hierarchy on the disk: all configuration files are created.
    - Run all `post` functions of actions.

    :param workon: Work-on path.
    :type workon: :class:`str` or :class:`pathlib.Path`
    :param environment: Environment to use for substitution in pattern.
    :type environment: :class:`incipyt.system.Environment`
    :param actions: List of actions to configure all tools.
    :type actions: :class:`list`
    """
    workon_path = pathlib.Path(workon)

    hierarchy = Hierarchy()
    for action in actions:
        logger.info(f"Add {action} to hierarchy.")
        action.add_to(hierarchy)

    logger.info(f"Mkdir folder for hierarchy on {workon_path}.")
    hierarchy.mkdir(workon_path, environment)

    for action in actions:
        logger.info(f"Running pre-action for {action}.")
        action.pre(workon_path, environment)

    logger.info("Commit hierarchy.")
    hierarchy.commit(environment)

    for action in actions:
        logger.info(f"Running post-action for {action}.")
        action.post(workon_path, environment)
