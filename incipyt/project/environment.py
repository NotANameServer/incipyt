import collections
import importlib
import logging

import click

from incipyt import variables

logger = logging.getLogger(__name__)


class _Environment(collections.UserDict):  # singleton
    """Manage environment variables using for substitutions in patterns.

    A :class:`Environment` object `environment` is a dictionnary.

    .. code-block::

        environment["VARIABLE_NAME"] = "something"

    If a specific variable hasn't been set, it can be asked for it anyway and
    it will be add to the `environment` immediately.
    """

    def clear(self):
        """Reset the environmentment."""
        self.data.clear()

        importlib.reload(variables)

    def __init__(self):
        self.data = {}
        self.clear()

    def __getitem__(self, key):
        if key not in self.data:
            logger.debug("Missing environment variable %s, request it.", key)
            self.data[key] = self._prompt(key)

        return self.data[key]

    def __setitem__(self, key, value):
        if key in self.data:
            raise ValueError(f"Environment variable {key} already exists, delete it before.")

        logger.debug("Set environment variable %s=%s.", key, value)
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
        if user_input:
            return user_input
        else:
            return (
                user_input
                if key in variables.metadata and variables.metadata[key].required
                else None
            )

environ = _Environment()  # singleton
