import collections
import importlib
import logging
from collections import abc

import click

from incipyt import variables
from incipyt._internal import dumpers, templates
from incipyt._internal.utils import is_nonstring_sequence

logger = logging.getLogger(__name__)


class _Environ(collections.UserDict):
    """Manage environ variables using for substitutions in patterns.

    A :class:`Environ` object `environ` is a dictionnary.

    .. code-block::

        environ["VARIABLE_NAME"] = "something"

    If a specific variable hasn't been set, it can be asked for it anyway and
    it will be add to the `environ` immediately.
    """

    def clear(self):
        self.data.clear()

        importlib.reload(variables)

    def __init__(self):
        self.data = {}
        self.clear()

    def __getitem__(self, key):
        if key not in self.data:
            logger.debug("Missing environ variable %s, request it.", key)
            self.data[key] = self._prompt(key)

        return self.data[key]

    def __setitem__(self, key, value):
        if key in self.data:
            raise ValueError(f"Environ variable {key} already exists, delete it before.")

        logger.debug("Set environ variable %s=%s.", key, value)
        self.data[key] = value

    def _prompt(self, key):
        if key in variables.metadata and variables.metadata[key].do_not_prompt:
            user_input = variables.metadata[key].default
        else:
            user_input = click.prompt(
                key.replace("_", " ").lower().capitalize(),
                default=variables.metadata[key].default if key in variables.metadata else "",
                type=str,
            )
        return user_input if user_input else None


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
            logger.debug("Register configuration %s in project structure.", str(config_root))
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
            logger.debug("Register configuration %s in project structure.", str(config_root))
            self._configurations[config_root] = []

        if not is_nonstring_sequence(self._configurations[config_root]):
            raise TypeError(f"{config_root} is not a list.")
        return templates.TemplateList(self._configurations[config_root])

    def use_template(self, template_name, dest=None, sanitizer=None):
        """Use a file as template to populate a configuration file.

        :param template_name: Relative path of the template file.
        :type template_name: :class:`str`
        :param dest: Relative path of the configuration file.
        :type dest: :class:`str` or `None`, optionnal
        :param sanitizer: An optionnal callable to sanitize the values given (key, value) pairs.
        :type sanitizer: :class:`function` or `None`, optionnal
        """
        self.get_config_list(dumpers.TextFile(dest or template_name, sanitizer=sanitizer)).append(
            templates.StringTemplate.from_file(template_name)
        )

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

        elif isinstance(template, abc.MutableMapping):
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
