import dataclasses
import logging
import sys
from datetime import date
from typing import Any

from incipyt._internal.utils import strtobool

logger = logging.getLogger(__name__)

# the public index where every variable metadata is saved
variables = {}


@dataclasses.dataclass
class Variable:
    """Metadata dataclass for environment variables."""

    name: str
    """
    the unique option name as found in :class:`~incipyt.project.environ`
    """

    type: callable = str  # noqa: A003
    """the function used to parse the value from a string"""

    _default: Any = ""

    def _get_default(self):
        return self._default

    default = property(_get_default)
    """
    the read-only default value for the option, copied inside of the
    environment at runtime
    """

    prompt: bool = True
    """
    whether the user should be asked for confirmation before using the
    :attr:`default` value.
    """

    _required: bool = False

    def _get_required(self):
        return self._required

    def _set_required(self, flag):
        if self._default and flag:
            raise ValueError(
                "A variable can only be required when it doesn't provide a default value"
            )
        self._required = flag

    required = property(_get_required, _set_required)
    """
    whether the user is allowed to provide an empty string in case he is
    prompted for this variable
    """

    help: str = ""  # noqa: A003
    """
    the free text that appears next to this variable in the listing of
    the command line ``--help``
    """

    def __init__(
        self,
        name,
        type=type,  # noqa: A002
        default=_default,
        prompt=prompt,
        required=_required,
        help=help,  # noqa: A002
    ):
        self.name = name
        self.type = type
        self._default = default
        self.prompt = prompt
        self.required = required
        self.help = help
        variables[self.name] = self


# please keep the variables alphabetically sorted

Variable(
    "AUDIENCE_PYTHON_VERSION",
    # as of may 2022, the latest stable release of most bsd/linux
    # distributions ship a python whoose version is at least 3.9
    default="{0[0]}.{0[1]}".format(min(sys.version_info, (3, 9))),
    help="The minimal python version your project will suppport.",
)
Variable("AUTHOR_EMAIL", help="The author email.")
Variable("AUTHOR_NAME", help="The author name.")
Variable(
    "CHECK_BUILD",
    type=strtobool,
    default=False,
    prompt=False,
    help="Whether to verify the newly created project correctly builds.",
)
Variable("LICENSE", default="Copyright", prompt=False)
Variable("PACKAGE_VERSION", default="0.0.0", help="The version of the new project.")
Variable("PROJECT_NAME", help="The project name.")
Variable(
    "PYTHON_CMD",
    default=sys.executable,
    prompt=False,
    help="The path to the python executable to run commands with.",
)
Variable("REPOSITORY", help="The HTTP URL to the online repository")
Variable("SUMMARY_DESCRIPTION", required=True, help="The project short description.")
Variable(
    "VENV_FOLDER",
    default=".venv",
    prompt=False,
    help="The name of the virtual environment folder for venv.",
)
Variable("YEAR", type=int, default=date.today().year, prompt=False, help="The current year.")
