"""TO-DO."""

import collections.abc
import logging
import os
import pathlib
import subprocess

import click

from incipyt._internal import utils


logger = logging.getLogger(__name__)


class Environment:
    """Manage environment variables using for substitutions in patterns.

    Functions :meth:`pull`and :meth:`push` can be used to add or request a
    specific envirnoment variable.

    Function :meth:`requests` ask the user if a value is missing.

    An instance is also a visitor for :class:`incipyt.system.Hierarchy`
    elements involving pattern with environment variables.
    """

    def __init__(self, auto_confirm):
        self._auto_confirm = auto_confirm
        self._confirmed = []
        self._variables = os.environ.copy()

        if "PYTHON_CMD" not in self._variables:
            self._variables["PYTHON_CMD"] = "python"
        self._confirmed.append("PYTHON_CMD")

    def pull(self, key):
        """Try to pull the actual value for `key`.

        If `key` is already confirmed, just return the associated value, if not,
        first asks for it -- see :func:`incipyt.system.Environment.requests`
        -- then returns it.

        :param key: Environment key asked.
        :type key: str
        :return: The actual value for `key`.
        :rtype: str
        """
        if not self._auto_confirm and key not in self._confirmed:
            logger.debug(f"Environement variable {key} not confirmed, request it.")
            self._variables[key] = self.requests(key)
            self._confirmed.append(key)
        elif self._auto_confirm and key not in self._variables:
            logger.debug(f"Missing environement variable {key}, request it.")
            self._variables[key] = self.requests(key)

        return self._variables[key]

    def push(self, key, value, update=False, confirmed=False):
        """Try to push a `key` = `value` associaton.

        :param key: Key of the association to push.
        :type key: str
        :param value: Value of the association to push.
        :type value: str
        :param update: Allow existing keys.
        :type update: bool
        :param confirmed: Has the value to be considered as confirmed ?
        :type update: bool
        :raises RuntimeError: Raise if `key` already exists in the actual environment.
        """
        if key in self._variables and not update:
            raise RuntimeError(
                f"Environment variable {key} already exists, use update."
            )

        logger.debug(f"Push environement variable {key}={value}.")
        self._variables[key] = value
        if confirmed and key not in self._confirmed:
            self._confirmed.append(key)

    def requests(self, key):
        """Request to the user the value to associate to `key`.

        :param key: Key to request to the user.
        :type key: str
        :raises NotImplementedError: TO-DO.
        """
        return click.prompt(
            key.replace("_", " ").lower().capitalize(),
            default=self._variables[key] if key in self._variables else "",
            type=str,
        )

    def render(self, template):
        """Render the Jinja `template` to process substitutions.

        :param template: The Jinja template to process.
        :type template: :class:`jinja2.Template`
        :return: The template aftersubstitution.
        :rtype: str
        """
        return template.render(**self._variables)

    def visit(self, template):
        """Visit the nested-dictionary structure `template` to process substitutions.

        For all callable values of the template dictionary, replace it by
        applying the substitution callback.
        For all nested dictionary values of the template dictionary,
        recursively apply :func:`incipyt.system.Environment.visit`.

        :param template: The template dictionary to visit.
        :type template: dict
        """
        for key, value in template.items():
            logger.debug(f"Visit {key} to process environment variables.")
            if callable(value):
                template[key] = value(self)
            elif isinstance(value, collections.abc.MutableMapping):
                self.visit(value)
                if not value:
                    template[key] = None
            elif isinstance(value, collections.abc.MutableSequence):
                for index, element in enumerate(value):
                    if callable(element):
                        value[index] = element(self)
                    if isinstance(element, collections.abc.MutableMapping):
                        self.visit(element)
                if all(element is None for element in value):
                    template[key] = None

        for key in [key for key, value in template.items() if value is None]:
            del template[key]

    def run(self, command):
        """Run a command after substitution using the environment.

        :param command: List of the command elements.
        :type command: List
        :return: stdout docoded.
        :rtype: str
        """
        completed_process = subprocess.run(
            [c(self) if callable(c) else c for c in command],
            capture_output=True,
            check=True,
        )
        logger.info(
            f"""{' '.join(completed_process.args)}
{completed_process.stdout.decode()}"""
        )
        return completed_process.stdout.decode()


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
        :rtype: dict
        """
        if config_root not in self._configurations:
            logger.debug(
                f"Register configuration {config_root} in hierarchy {id(self)}."
            )
            self._configurations[config_root] = {}

        return utils.TemplateDict(self._configurations[config_root])

    def register_template(self, template_root, template):
        """Register a Jinja template associated to the relative path `config_root`.

        :param template_root: Relative path of the configuration file.
        :type template_root: :class:`pathlib.PurePath`
        :param template: A Jinja template to register.
        :type template: :class:`jinja2.Template`
        :raises RuntimeError: If `template_root`already registered.
        """
        if template_root in self._templates:
            raise RuntimeError(f"Template {template_root} already exists.")

        logger.debug(f"Register template {template_root} in hierarchy {id(self)}.")
        self._templates[template_root] = template

    def commit(self, environment):
        """Commit current hierarchy on disk.

        :param environment: Environment to use for substitution in pattern.
        :type environment: :class:`incipyt.system.Environment`.
        :raises RuntimeError: If one of the configuration file already exists.
        """
        for config_root, config in self._configurations.items():
            logger.info(f"Process environment variables for {config_root}.")
            environment.visit(config)

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
        :type environment: :class:`incipyt.system.Environment
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
    :type workon: Union[str, :class:`pathlib.Path`]
    :param environment: Environment to use for substitution in pattern.
    :type environment: :class:`incipyt.system.Environment`
    :param actions: List of actions to configure all tools.
    :type actions: List
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
