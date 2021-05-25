from jinja2 import Template

from incipyt import hooks
from incipyt._internal import sanitizers
from incipyt._internal import templates
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

        :file:`pyptoject.toml`

        .. code-block::

            [build-system]
            requires = [ "setuptools", "wheel",]
            build-backend = "setuptools.build_meta"

        If this configuration cannot be populate like that, an error is raised.

        :file:`setup.cfg`

        .. code-block::

            [metadata]
            author_email = {AUTHOR_NAME} <{AUTHOR_EMAIL}>
            description = {SUMMARY_DESCRIPTION}
            maintainer_email = {AUTHOR_NAME} <{AUTHOR_EMAIL}>
            name = {PROJECT_NAME}
            version = {PACKAGE_VERSION}
            classifiers =
                Programming Language :: Python :: 3 :: Only

            [options]
            python_requires = >={PYTHON_VERSION}
            packages = {PROJECT_NAME}

            [options.package_data]
            * = {PACKAGE_DATA}/*

            [options.extras_require]
            dev =
                build

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

        pyproject["build-system"] = templates.Transform(
            {
                "requires": ["setuptools", "wheel"],
                "build-backend": "setuptools.build_meta",
            }
        )

        setup["metadata"] = {
            "author_email": "{AUTHOR_NAME} <{AUTHOR_EMAIL}>",
            "description": "{SUMMARY_DESCRIPTION}",
            "maintainer_email": "{AUTHOR_NAME} <{AUTHOR_EMAIL}>",
            "name": templates.Requires("{PROJECT_NAME}", sanitizer=sanitizers.project),
        }

        setup |= templates.Transform(
            {
                "metadata": {
                    "version": "{PACKAGE_VERSION}",
                },
                "options": {
                    "python_requires": ">={PYTHON_VERSION}",
                },
            },
            lambda template: templates.Requires(
                template,
                sanitizer=sanitizers.version,
                PACKAGE_VERSION="0.0.0",
                PYTHON_VERSION="3.6",
            ),
        )

        setup["options", "packages"] = templates.Requires(
            "{PROJECT_NAME}", sanitizer=sanitizers.package
        )

        setup["options.package_data", "*"] = templates.Requires(
            "{PACKAGE_DATA}/*", confirmed=True, PACKAGE_DATA="data"
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
            Jinja.make("README.md"),
            Template(
                textwrap.dedent("""\
                    # {{PROJECT_NAME}}

                    {{SUMMARY_DESCRIPTION}}

                    ## Usage

                    ## Contribute

                    Copyright (c) {{AUTHOR_NAME}}
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
        hook_build(templates.Transform("build"))

        hook_classifier = hooks.Classifier(hierarchy)
        hook_classifier(
            templates.Transform("Programming Language :: Python :: 3 :: Only")
        )

        hook_vcs = hooks.VCSIgnore(hierarchy)
        hook_vcs(templates.Transform("build"))
        hook_vcs(templates.Transform("dist"))
        hook_vcs(templates.Transform("*.egg-info"))

    def _hook_classifier(self, hierarchy, value):
        setup = hierarchy.get_configuration(CfgIni.make("setup.cfg"))
        setup["metadata", "classifiers"] = [value]

    def _hook_dependancy(self, hierarchy, value):
        setup = hierarchy.get_configuration(CfgIni.make("setup.cfg"))
        setup["options.extras_require", "dev"] = [value]

    def _hook_url(self, hierarchy, url_kind, url_value):
        setup = hierarchy.get_configuration(CfgIni.make("setup.cfg"))
        setup["metadata", "project_urls", url_kind] = url_value

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
                templates.Requires("{PYTHON_CMD}"),
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
                    templates.Requires("{PYTHON_CMD}"),
                    "-m",
                    "build",
                    f"{workon}",
                ]
            )
