import dataclasses
import logging
import os
import sys
from datetime import date
from typing import Any

# as of may 2022, the latest stable release of most bsd/linux
# distributions ship a python whoose verion is at least 3.9
LINUX_MIN_PYTHON_VERSION = (3, 9)


logger = logging.getLogger(__name__)

metadata = {}


@dataclasses.dataclass
class _EnvMetadata:
    """Metadata dataclass for environment variables.

    If a specific `environ` variable hasn't been set, its metadata is used to constraint
    how the prompt is done. If no metadata has been explicitly register, the prompt
    behaves as a metadata with default field has been register.

    Field `default: Any = ""`:

    .. code-block::

        _EnvMetadata("VARIABLE_NAME", default="something")

    The `default` value is used as a suggestion for the prompt.

    Field `do_not_prompt: bool = False`:

    .. code-block::

        _EnvMetadata("VARIABLE_NAME", do_not_prompt=True)

    If True, the prompt is bypassed and the `default` value is used.

    Field `required: bool = False`:

    .. code-block::

        EnvMetadata("VARIABLE_NAME", required=True)

    When there is no `default` suggestion, if no value is given when prompt asks for it
    `None` is saved in `environ` and all :class:`incipyt._internal.templates.Formattable`
    values will be purge from template dictionary before commiting. When `True`, an empty
    string is saved in `environ`. Note that if the `default` suggestion is not empty,
    `required` has no effect as the prompt result will never be an empty string.
    """

    name: str
    default: Any = ""
    do_not_prompt: bool = False
    required: bool = False

    def __post_init__(self):
        if self.name in metadata:
            raise ValueError(
                f"Metadata for environ variable {self.name} already exists, update it instead of instantiate."
            )
        metadata[self.name] = self


_EnvMetadata(
    "AUDIENCE_PYTHON_VERSION",
    default="{0[0]}.{0[1]}".format(min(sys.version_info, LINUX_MIN_PYTHON_VERSION)),
)
_EnvMetadata("AUTHOR_NAME")
_EnvMetadata("AUTHOR_EMAIL")
_EnvMetadata("LICENSE", default="Copyright", do_not_prompt=True)
_EnvMetadata("PACKAGE_VERSION", default="0.0.0")
_EnvMetadata("PROJECT_NAME")
_EnvMetadata("PYTHON_CMD", default=sys.executable, do_not_prompt=True)
_EnvMetadata("SUMMARY_DESCRIPTION", required=True)
_EnvMetadata("YEAR", default=date.today().year, do_not_prompt=True)

# Populate metadata from system environment variables
for var_name, var_value in os.environ.items():
    if var_name not in metadata:
        _EnvMetadata(var_name, default=var_value)
    else:
        metadata[var_name].default = var_value
