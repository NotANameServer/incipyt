from jinja2 import Template

from incipyt import hooks
from incipyt._internal import sanitizers
from incipyt._internal import utils
from incipyt._internal.dumpers import CfgIni, Jinja, Toml


class Setuptools:
    """Action to add Setuptools to :class:`incipyt.system.Hierarchy`."""

    def __init__(self, check=False):
        self.check_build = check
        hooks.BuildDependancy.register(self._hook_dependancy)
        hooks.Classifier.register(self._hook_classifier)
        hooks.ProjectURL.register(self._hook_url)

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
            author_email = {AUTHOR_NAME} <{AUTHOR_EMAIL}>
            description = {SUMMARY_DESCRIPTION}
            maintainer_email = {AUTHOR_NAME} <{AUTHOR_EMAIL}>
            version = {PACKAGE_VERSION}
            name = {PROJECT_NAME}

            [options]
            python_requires = >={PYTHON_VERSION}
            packages = {PROJECT_NAME}

            [options.package_data]
            * = {PACKAGE_DATA}/*

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

        utils.set_items(
            setup,
            {
                "metadata": {
                    "author_email": "{AUTHOR_NAME} <{AUTHOR_EMAIL}>",
                    "description": "{SUMMARY_DESCRIPTION}",
                    "maintainer_email": "{AUTHOR_NAME} <{AUTHOR_EMAIL}>",
                },
            },
            utils.Requires,
        )
        utils.set_items(
            setup,
            {
                "metadata": {
                    "version": "{PACKAGE_VERSION}",
                },
                "options": {
                    "python_requires": ">={PYTHON_VERSION}",
                },
            },
            lambda template: utils.Requires(
                template,
                sanitizer=sanitizers.version,
                PACKAGE_VERSION="0.0.0",
                PYTHON_VERSION="3.6",
            ),
        )

        if "metadata" not in setup:
            setup["metadata"] = {}
        utils.set_item(
            setup["metadata"],
            "name",
            utils.Requires("{PROJECT_NAME}", sanitizer=sanitizers.project),
        )

        if "options" not in setup:
            setup["options"] = {}
        utils.set_item(
            setup["options"],
            "packages",
            utils.Requires("{PROJECT_NAME}", sanitizer=sanitizers.package),
        )

        if "options.package_data" not in setup:
            setup["options.package_data"] = {}
        utils.set_item(
            setup["options.package_data"],
            "*",
            utils.Requires("{PACKAGE_DATA}/*", confirmed=True, PACKAGE_DATA="data"),
        )

        hierarchy.register_template(
            Jinja.make("LICENSE"),
            Template(
                """Copyright (c) {{AUTHOR_NAME}}

"""
            ),
        )
        hierarchy.register_template(
            Jinja.make("{PROJECT_NAME}/__init__.py", sanitizer=sanitizers.package),
            Template(
                """
"""
            ),
        )
        hierarchy.register_template(
            Jinja.make("setup.py"),
            Template(
                """import setuptools

setuptools.setup()

"""
            ),
        )

        hook_build = hooks.BuildDependancy(hierarchy)
        hook_build("build")

        hook_classifier = hooks.Classifier(hierarchy)
        hook_classifier("Programming Language :: Python :: 3 :: Only")

        hook_vcs = hooks.VCSIgnore(hierarchy)
        hook_vcs("build")
        hook_vcs("dist")
        hook_vcs("*.egg-info")

    def _hook_classifier(self, hierarchy, value):
        setup = hierarchy.get_configuration(CfgIni.make("setup.cfg"))
        if "metadata" not in setup:
            setup["metadata"] = {}
        if "classifiers" not in setup["metadata"]:
            setup["metadata"]["classifiers"] = []

        utils.append_unique(setup["metadata"]["classifiers"], value)

    def _hook_dependancy(self, hierarchy, value):
        setup = hierarchy.get_configuration(CfgIni.make("setup.cfg"))
        if "options.extras_require" not in setup:
            setup["options.extras_require"] = {}
        if "dev" not in setup["options.extras_require"]:
            setup["options.extras_require"]["dev"] = []

        utils.append_unique(setup["options.extras_require"]["dev"], value)

    def _hook_url(self, hierarchy, url_kind, url_value):
        setup = hierarchy.get_configuration(CfgIni.make("setup.cfg"))
        if "metadata" not in setup:
            setup["metadata"] = {}
        if "project_urls" not in setup["metadata"]:
            setup["metadata"]["project_urls"] = {}

        utils.set_item(setup["metadata"]["project_urls"], url_kind, url_value)

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
        if self.check_build:
            environment.run(
                [
                    utils.Requires("{PYTHON_CMD}"),
                    "-m",
                    "build",
                    f"{workon}",
                ]
            )
