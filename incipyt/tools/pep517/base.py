import os

from incipyt import commands, project, signals, tools
from incipyt._internal import sanitizers, templates
from incipyt._internal.dumpers import Toml


class BuildSystem(tools.Tool):
    """Scripts to add generic PEP 517 build system to :class:`incipyt.project._Structure`."""

    def __init__(self):
        signals.build_dependency.connect(self._slot_dependency)
        signals.classifier.connect(self._slot_classifier)
        signals.project_url.connect(self._slot_url)

    def add_to_structure(self):
        """Add PEP 517 core structure to `project.structure`.

        :file:`pyptoject.toml`

        .. code-block::
            [project]
            authors = [
                {name = "{AUTHOR_NAME}", email = "{AUTHOR_EMAIL}"}
            ]
            classifiers = [
                "Programming Language :: Python :: 3 :: Only"
            ]
            description = "{SUMMARY_DESCRIPTION}"
            maintainers = [
                {name = "{AUTHOR_NAME}", email = "{AUTHOR_EMAIL}"}
            ]
            name = "{PROJECT_NAME}"
            readme = "README.md"
            requires-python = ">={PYTHON_VERSION}"
            version = "{PACKAGE_VERSION}"

            [project.optional-dependencies]
            dev = [
                "build>=0.2.0",
            ]

        If this configuration cannot be populate like that, an error is raised.

        Here key-value association is appended, if a key already exists the
        value is appended to the current one(s), the user will be asked to
        choose when commiting.
        """
        pyproject = project.structure.get_config_dict(Toml("pyproject.toml"))

        pyproject["project"] = {
            "authors": [{"name": "{AUTHOR_NAME}", "email": "{AUTHOR_EMAIL}"}],
            "description": "{SUMMARY_DESCRIPTION}",
            "license": {"file": "LICENSE"},
            "maintainers": [{"name": "{AUTHOR_NAME}", "email": "{AUTHOR_EMAIL}"}],
            "name": templates.StringTemplate(
                "{PROJECT_NAME}",
                sanitizer=sanitizers.project,
            ),
            "readme": "README.md",
            "requires-python": templates.StringTemplate(
                ">={AUDIENCE_PYTHON_VERSION}", sanitizer=sanitizers.version
            ),
            "version": templates.StringTemplate(
                "{PACKAGE_VERSION}", sanitizer=sanitizers.version
            ),
        }

        project.structure.use_template("{PROJECT_NAME}/__init__.py", sanitizer=sanitizers.package)
        project.structure.use_template("README.md")

        signals.build_dependency.emit(dep_name="build", min_version="0.2.0")

        signals.classifier.emit(classifier="Programming Language :: Python :: 3 :: Only")

        signals.vcs_ignore.emit(pattern="dist/")
        signals.vcs_ignore.emit(pattern="*.egg-info")

    def _slot_classifier(self, classifier, **kwargs):
        pyproject = project.structure.get_config_dict(Toml("pyproject.toml"))
        if ("project", "classifiers") not in pyproject:
            pyproject["project", "classifiers"] = []
        pyproject["project", "classifiers"].append(classifier)

    def _slot_dependency(self, dep_name, min_version=None, **kwargs):
        pyproject = project.structure.get_config_dict(Toml("pyproject.toml"))
        if ("project", "optional-dependencies", "dev") not in pyproject:
            pyproject["project", "optional-dependencies", "dev"] = []
        pyproject["project", "optional-dependencies", "dev"].append(
            dep_name if min_version is None else f"{dep_name}>={min_version}"
        )

    def _slot_url(self, url_kind, url_value, **kwargs):
        project.structure.get_config_dict(Toml("pyproject.toml"))["project", "urls"] = {
            url_kind: url_value
        }

    def post(self, workon):
        """Editable install and build for test.

        :param workon: Work-on folder.
        :type workon: :class:`pathlib.Path`
        """
        commands.pip_install(["--editable", f"{workon}[dev]"])
        if project.environ["CHECK_BUILD"]:
            commands.build([os.fspath(workon)])
