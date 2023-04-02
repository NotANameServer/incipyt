import os
import sys

from incipyt import commands, project, signals, tools
from incipyt._internal import sanitizers, templates
from incipyt._internal.dumpers import Toml
from incipyt.tools.pep517.base import LINUX_MIN_PYTHON_VERSION


class Poetry(tools.Tool):
    """Scripts to add Poetry to :class:`incipyt.project._Structure`."""

    def __init__(self, check_build=False, **kwargs):
        self.check_build = check_build
        signals.build_dependency.connect(self._slot_dependency)
        signals.classifier.connect(self._slot_classifier)
        signals.project_url.connect(self._slot_url)

    def add_to_structure(self):
        """Add poetry configuration to `project.structure`.

        :file:`pyptoject.toml`

        .. code-block::

            [build-system]
            build-backend: "poetry.core.masonry.api"
            requires: ["poetry_core"]

            [tool.poetry]
            authors = [
                "{AUTHOR_NAME} <{AUTHOR_EMAIL}>"
            ]
            classifiers = [
                "Programming Language :: Python :: 3 :: Only"
            ]
            description = "{SUMMARY_DESCRIPTION}"
            maintainers = [
                "{AUTHOR_NAME} <{AUTHOR_EMAIL}>"
            ]
            name = "{PROJECT_NAME}"
            readme = "README.md"
            version = "{PACKAGE_VERSION}"

            [tool.poetry.dependencies]
            python = ">={PYTHON_VERSION}"

            [tool.poetry.extras]
            dev = [
                "build",
                "poetry",
            ]

        If this configuration cannot be populate like that, an error is raised.

        Here key-value association is appended, if a key already exists the
        value is appended to the current one(s), the user will be asked to
        choose when commiting.

        :raises RuntimeError: If a build-system is already setup im pyproject.toml.
        """
        pyproject = project.structure.get_config_dict(Toml("pyproject.toml"))

        if "build-system" in pyproject:
            raise RuntimeError("Build system already registered.")

        pyproject["build-system"] = {
            "build-backend": "poetry.core.masonry.api",
            "requires": ["poetry_core"],
        }

        pyproject["tool", "poetry"] = {
            "authors": ["{AUTHOR_NAME} <{AUTHOR_EMAIL}>"],
            "description": templates.StringTemplate(
                "{SUMMARY_DESCRIPTION}",
                SUMMARY_DESCRIPTION="\t",
            ),
            "license": "{LICENSE}",
            "maintainers": ["{AUTHOR_NAME} <{AUTHOR_EMAIL}>"],
            "name": templates.StringTemplate(
                "{PROJECT_NAME}",
                sanitizer=sanitizers.project,
            ),
            "readme": "README.md",
            "version": templates.StringTemplate(
                "{PACKAGE_VERSION}",
                sanitizer=sanitizers.version,
                PACKAGE_VERSION="0.0.0",
            ),
        }

        pyproject["tool", "poetry", "dependencies"] = {
            "python": templates.StringTemplate(
                ">={AUDIENCE_PYTHON_VERSION}",
                sanitizer=sanitizers.version,
                AUDIENCE_PYTHON_VERSION="{0[0]}.{0[1]}".format(
                    min(sys.version_info, LINUX_MIN_PYTHON_VERSION)
                ),
            ),
        }

        project.structure.use_template("{PROJECT_NAME}/__init__.py", sanitizer=sanitizers.package)
        project.structure.use_template("README.md")

        signals.build_dependency.emit(dep_name="build")
        signals.build_dependency.emit(dep_name="poetry")

        signals.classifier.emit(classifier="Programming Language :: Python :: 3 :: Only")

        signals.vcs_ignore.emit(pattern="dist")

    def _slot_classifier(self, classifier, **kwargs):
        pyproject = project.structure.get_config_dict(Toml("pyproject.toml"))
        if ("tool", "poetry", "classifiers") not in pyproject:
            pyproject["tool", "poetry", "classifiers"] = []
        pyproject["tool", "poetry", "classifiers"].append(classifier)

    def _slot_dependency(self, dep_name, **kwargs):
        project.structure.get_config_dict(Toml("pyproject.toml"))[
            "tool", "poetry", "dev-dependencies"
        ] = {dep_name: "*"}

    def _slot_url(self, url_kind, url_value, **kwargs):
        project.structure.get_config_dict(Toml("pyproject.toml"))["tool", "poetry"] = {
            url_kind: url_value
        }

    def post(self, workon):
        """Editable install and build for test.

        :param workon: Work-on folder.
        :type workon: :class:`pathlib.Path`
        """
        commands.pip_install(["poetry"])
        commands.python_m(
            ["poetry", "env", "use", project.environ["PYTHON_CMD"]],
            cwd=os.fspath(workon),
        )
        commands.python_m(
            ["poetry", "install"],
            cwd=os.fspath(workon),
        )
        if self.check_build:
            commands.pip_install(["build"])
            commands.build([os.fspath(workon)])
