import textwrap

from incipyt import commands, project, signals, tools
from incipyt._internal import sanitizers, templates
from incipyt._internal.dumpers import CfgIni, TextFile, Toml


class Setuptools(tools.Tool):
    """Scripts to add Setuptools to :class:`incipyt.project._Structure`."""

    def __init__(self, check=False):
        self.check_build = check
        signals.build_dependency.connect(self._slot_dependency)
        signals.classifier.connect(self._slot_classifier)
        signals.project_url.connect(self._slot_url)

    def add_to_structure(self):
        """Add setuptools configuration to `project.structure`.

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
            long_description = file: README.md
            long_description_content_type = text/markdown
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

        :raises RuntimeError: If a build-system is already setup im pyproject.toml.
        """
        pyproject = project.structure.get_config_dict(Toml("pyproject.toml"))
        setup = project.structure.get_config_dict(CfgIni("setup.cfg"))

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
            "long_description": templates.Transform("file: README.md"),
            "long_description_content_type": templates.Transform("text/markdown"),
            "maintainer_email": "{AUTHOR_NAME} <{AUTHOR_EMAIL}>",
            "name": templates.StringTemplate(
                "{PROJECT_NAME}", sanitizer=sanitizers.project
            ),
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
            lambda template: templates.StringTemplate(
                template,
                sanitizer=sanitizers.version,
                PACKAGE_VERSION="0.0.0",
                PYTHON_VERSION="3.7",
            ),
        )

        setup["options", "packages"] = templates.StringTemplate(
            "{PROJECT_NAME}", sanitizer=sanitizers.package
        )

        setup["options.package_data", "*"] = templates.StringTemplate(
            "{PACKAGE_DATA}/*", confirmed=True, PACKAGE_DATA="data"
        )

        project.structure.get_config_list(TextFile("LICENSE", sep="\n\n")).append(
            "Copyright (c) {AUTHOR_NAME} <{AUTHOR_EMAIL}>"
        )

        project.structure.get_config_list(
            TextFile("{PROJECT_NAME}/__init__.py", sanitizer=sanitizers.package)
        ).append("")

        project.structure.get_config_list(TextFile("README.md", sep="\n\n")).append(
            templates.StringTemplate(
                textwrap.dedent(
                    """\
                # {PROJECT_NAME}

                {SUMMARY_DESCRIPTION}

                ## Usage

                ## Contribute

                Copyright (c) {AUTHOR_NAME} <{AUTHOR_EMAIL}>"""
                ),
                value_error=False,
            )
        )

        project.structure.get_config_list(TextFile("setup.py")).append(
            textwrap.dedent(
                """\
            import setuptools

            setuptools.setup()"""
            )
        )

        signals.build_dependency.emit(dep_name=templates.Transform("build"))

        signals.classifier.emit(
            classifier=templates.Transform(
                "Programming Language :: Python :: 3 :: Only"
            )
        )

        signals.vcs_ignore.emit(pattern=templates.Transform("build"))
        signals.vcs_ignore.emit(pattern=templates.Transform("dist"))
        signals.vcs_ignore.emit(pattern=templates.Transform("*.egg-info"))

    def _slot_classifier(self, classifier, **kwargs):
        setup = project.structure.get_config_dict(CfgIni("setup.cfg"))
        if ("metadata", "classifiers") not in setup:
            setup["metadata", "classifiers"] = []
        setup["metadata", "classifiers"].append(classifier)

    def _slot_dependency(self, dep_name, **kwargs):
        setup = project.structure.get_config_dict(CfgIni("setup.cfg"))
        if ("options.extras_require", "dev") not in setup:
            setup["options.extras_require", "dev"] = []
        setup["options.extras_require", "dev"].append(dep_name)

    def _slot_url(self, url_kind, url_value, **kwargs):
        project.structure.get_config_dict(CfgIni("setup.cfg"))[
            "metadata", "project_urls"
        ] = {url_kind: url_value}

    def post(self, workon):
        """Editable install and build for test.

        :param workon: Work-on folder.
        :type workon: :class:`pathlib.Path`
        """
        commands.pip(["install", "--editable", f"{workon}[dev]"])
        if self.check_build:
            commands.build([f"{workon}"])