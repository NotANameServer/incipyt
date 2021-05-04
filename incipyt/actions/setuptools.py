from jinja2 import Template

from incipyt import hooks
from incipyt._internal import utils
from incipyt._internal.dumpers import CfgIni, Jinja, Toml


class Setuptools:
    """Action to add Setuptools to :class:`incipyt.system.Hierarchy`."""

    def __init__(self):
        hooks.BuildDependancy.register(self._hook)

    def add_to(self, hierarchy):
        """Add setuptools configuration to `hierarchy`.

        pyptoject.toml
        .. code-block::

            [build-system]
            requires = [ "setuptools", "wheel",]
            build-backend = "setuptools.build_meta"

        If this configuration cannot be populate like that, an error is raised.

        setup.cfg
        .. code-block::

            [metadata]
            name = {NAME}
            version = 0.0.1

            [options]
            packages = {NAME}
            python_requires = >=3.6

            [options.package_data]
            * = data/*

        Here key-value association is appended, if a key already exists the
        value is appended to the current one(s), the user will be asked to
        choose when commiting.

        :param hierarchy: The actual hierarchy to update with setuptools configuration.
        :type hierarchy: :class:`incipyt.system.Hierarchy`
        :raises RuntimeError: If a build-system is already setup im pyproject.toml.
        """
        pyproject = hierarchy.get_configuration(Toml.make("pyproject.toml"))
        setup = hierarchy.get_configuration(CfgIni.make("setup.cfg"))

        if "build-system" in pyproject:
            raise RuntimeError("Build system already registered.")

        pyproject["build-system"] = {
            "requires": ["setuptools", "wheel"],
            "build-backend": "setuptools.build_meta",
        }

        if "metadata" not in setup:
            setup["metadata"] = {}
        if "options" not in setup:
            setup["options"] = {}
        if "options.package_data" not in setup:
            setup["options.package_data"] = {}
        if "options.extras_require" not in setup:
            setup["options.extras_require"] = {}

        utils.append(
            setup["metadata"],
            "name",
            utils.Requires("{NAME}", sanitizer=utils.sanitizer_project),
        )
        utils.append(setup["metadata"], "version", "0.0.1")
        utils.append(
            setup["options"],
            "packages",
            utils.Requires("{NAME}", sanitizer=utils.sanitizer_package),
        )
        utils.append(setup["options"], "python_requires", ">=3.6")
        utils.append(setup["options.package_data"], "*", "data/*")

        hierarchy.register_template(
            Jinja.make("setup.py", sanitizer=utils.sanitizer_package),
            Template(
                """import setuptools

setuptools.setup()

"""
            ),
        )
        hierarchy.register_template(
            Jinja.make("{NAME}/__init__.py", sanitizer=utils.sanitizer_package),
            Template(
                """
"""
            ),
        )

        hook_vcs = hooks.VCSIgnore(hierarchy)
        hook_vcs("build")
        hook_vcs("dist")
        hook_vcs("*.egg-info")

        hook_build = hooks.BuildDependancy(hierarchy)
        hook_build("build")

    def _hook(self, hierarchy, value):
        setup = hierarchy.get_configuration(CfgIni.make("setup.cfg"))
        if "dev" not in setup["options.extras_require"]:
            setup["options.extras_require"]["dev"] = []

        setup["options.extras_require"]["dev"].append(value)

    def __str__(self):
        return "setuptools"

    def pre(self, workon, environment):
        """Pre-action for setuptools, do nothing.

        :param workon: Work-on folder.
        :type workon: :class:`pathlib.Path`
        :param environment: Environment used to do pre-action
        :type environment: :class:`incipyt.system.Environment`
        """
        pass

    def post(self, workon, environment):
        """Editable install and build for test.

        :param workon: Work-on folder.
        :type workon: :class:`pathlib.Path`
        :param environment: Environment used to do post-action
        :type environment: :class:`incipyt.system.Environment`
        """
        environment.run(
            [
                utils.Requires("{PYTHON_CMD}"),
                "-m",
                "pip",
                "install",
                "--editable",
                f"{workon}[dev]",
            ]
        )
        environment.run(
            [
                utils.Requires("{PYTHON_CMD}"),
                "-m",
                "build",
                f"{workon}",
            ]
        )
