from incipyt import project
from incipyt._internal.dumpers import Toml
from incipyt.tools import pep517


class Setuptools(pep517.BuildSystem):
    """Scripts to add Setuptools to :class:`incipyt.project._Structure`."""

    def add_to_structure(self):
        """Add setuptools configuration to `project.structure`.

        :file:`pyptoject.toml`

        .. code-block::

            [build-system]
            build-backend: "setuptools.build_meta"
            requires: ["setuptools>=64.0.0"]

        If this configuration cannot be populate like that, an error is raised.

        :raises RuntimeError: If a build-system is already setup in pyproject.toml.
        """
        super().add_to_structure()

        pyproject = project.structure.get_config_dict(Toml("pyproject.toml"))

        if "build-system" in pyproject:
            raise RuntimeError("Build system already registered.")

        pyproject["build-system"] = {
            "build-backend": "setuptools.build_meta",
            "requires": ["setuptools>=64.0.0"],
        }
