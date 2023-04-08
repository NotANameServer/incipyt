import dataclasses
import logging
import os
import sys
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
    """

    name: str
    default: Any = ""

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
_EnvMetadata("PACKAGE_VERSION", default="0.0.0")
_EnvMetadata("PROJECT_NAME")

# Populate metadata from system environment variables
for var_name, var_value in os.environ.items():
    if var_name not in metadata:
        _EnvMetadata(var_name, default=var_value)
    else:
        metadata[var_name].default = var_value
