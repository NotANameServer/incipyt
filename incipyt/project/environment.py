import collections
import contextlib
import logging
from functools import partial, partialmethod

import click

from .meta_variables import variables

logger = logging.getLogger(__name__)


class PromptDict(collections.UserDict):
    """Prompt user upon access to any item."""

    def __getitem__(self, key):
        var = variables[key]
        default_value = super().__getitem__(key)

        if var.required and default_value == "":
            raise KeyError(f"Default value {default_value!r} for key {key!r} is empty, skip")

        confirmed_value = click.prompt(
            key.replace("_", " ").lower().capitalize(),
            default=default_value,
            type=var.type,
        )
        if not confirmed_value and var.required:
            raise KeyError(
                f"Default value {default_value!r} for key {key!r} rejected by user, skip"
            )
        return confirmed_value


class _Environment(collections.UserDict):  # singleton
    r"""Variable-Value mapping for template placeholders.

    The value is extracted from one of the many sources (cli, config
    file, os environ, ...), prompting the user for confirmation upon
    first usage of "unconfirmed" value (e.g. value from the config file
    or value lacking a sensitive default).

    The variable resolution order is as follow:

     1. previously selected value
     2. CLI's --option
     3. os.environ (starting with INCIPYT_)
     4. runtime injected default
     5. hardcoded default
    --- / use as-is \ prompt for confirmation /
     6. configuration file
     7. runtime suggested default
     8. os.environ (not starting with INCIPYT_)
     9. hardcoded suggested default
    10. explicit prompt

    If the value is found in any of the 5 first sources, the value is
    used as-is. If the value is found is the later 5 last sources, the
    user is prompted asking for a confirmation.

    The resolution order is fixed, incipyt contributors are invited to
    use ``__setattr__`` (1), ``inject`` (4) or ``suggest`` (7) to add
    values inside of the environment at the place they think is best.

    Mass injection of values are possible via the ``feed_`` methods.
    """

    def clear(self):
        """Reset the environment."""
        self.data = {}

        self._source_cli = {}  #: click -o/--option
        self._source_osenviron_confirmed = {}  #: os.environ w/ INCIPYT_
        self._source_tool_confirmed = {}  #: self.inject()
        self._source_default_confirmed = {}  #: Variable(prompt=False)
        self._source_config = PromptDict()  #: incipyt/config.toml
        self._source_tool_prompt = PromptDict()  #: self.suggest()
        self._source_osenviron_prompt = PromptDict()  #: os.environ w/o INCIPYT_
        self._source_default_prompt = PromptDict()  #: Variable(prompt=True)

        self._sources = collections.ChainMap(
            self._source_cli,
            self._source_osenviron_confirmed,
            self._source_tool_confirmed,
            self._source_default_confirmed,
            self._source_config,
            self._source_tool_prompt,
            self._source_osenviron_prompt,
            self._source_default_prompt,
        )

    def __init__(self):
        self.clear()

    def __getitem__(self, key):
        if key not in self.data:
            logger.debug("Missing environment variable %s, request it.", key)
            self.data[key] = self._prompt(key)

        return self.data[key]

    def __setitem__(self, key, value):
        """Bypass sources and force the value of an environment variable."""
        if key in self.data:
            raise ValueError(f"Environment variable {key} already exists, delete it before.")

        logger.debug("Set environment variable %s=%s.", key, value)
        self.data[key] = value

    def _prompt(self, key):
        var = variables.get(key)
        if var is None:
            raise ValueError(f"Unknown variable: {key!r}")

        # Get the value from a source (cli/.../default), possibly prompting
        # the user for a confirmation
        with contextlib.suppress(KeyError):
            return self._sources[key]

        # No default value found, prompt user
        click_prompt = partial(click.prompt, key.replace("_", " ").capitalize(), type=var.type)
        if not var.required:
            click_prompt.keywords["default"] = ""
            return click_prompt() or None  # it asks only once
        return click_prompt()  # it keeps asking until the user gives a value

    def inject(self, key, value):
        """Inject a confirmed key=value pair inside the sources."""
        self._source_tool_confirmed[key] = value

    def suggest(self, key, value):
        """Suggest an unconfirmed key=value pair inside the sources."""
        self._source_tool_prompt[key] = value

    def _feed(self, source_name, options):
        source = getattr(self, source_name)
        for key, value in options.items():
            if (var := variables.get(key)) is None:
                raise ValueError(f"{key!r} is an unknown variable")
            source[key] = var.type(value)

    def _feed_pair(self, source_name, options, *, prompt):
        self._feed(f"{source_name}_{'prompt' if prompt else 'confirmed'}", options)

    feed_cli = partialmethod(_feed, "_source_cli")
    feed_config = partialmethod(_feed, "_source_config")
    feed_tool = partialmethod(_feed_pair, "_source_tool")
    feed_osenviron = partialmethod(_feed_pair, "_source_osenviron")
    feed_default = partialmethod(_feed_pair, "_source_default")


environ = _Environment()  # singleton
