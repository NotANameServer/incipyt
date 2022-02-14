from incipyt import tools, signals, project
from incipyt._internal import templates
from incipyt._internal.dumpers import Requirement


class Git(tools._Tool):
    """Scripts to add Git to :class:`incipyt.project._Structure`."""

    def __init__(self):
        signals.vcs_ignore.connect(self._slot)

    def add_to_structure(self):
        """Add git configuration to `project.structure`.

        Register git related project URLs:
        - Repository: {REPOSITORY}
        - Issue: {REPOSITORY}/issues
        - Documentation: {REPOSITORY}/wiki
        """
        signals.project_url.emit(
            url_kind="Repository", url_value=templates.StringTemplate("{REPOSITORY}")
        )
        signals.project_url.emit(
            url_kind="Issue", url_value=templates.StringTemplate("{REPOSITORY}/issues")
        )
        signals.project_url.emit(
            url_kind="Documentation",
            url_value=templates.StringTemplate("{REPOSITORY}/wiki"),
        )

    def _slot(self, pattern, **kwargs):
        gitignore = project.structure.get_configuration(Requirement(".gitignore"))
        gitignore[None] = [pattern]

    def pre(self, workon):
        """Run `git init`.

        Also push {AUTHOR_NAME} and {AUTHOR_EMAIL} using `git config user.*`.

        :param workon: Work-on folder.
        :type workon: :class:`pathlib.Path`
        """
        project.run(["git", "init", str(workon)])

        project.environ["AUTHOR_NAME"] = project.EnvValue(
            project.run(["git", "-C", str(workon), "config", "user.name"])
            .stdout.decode()
            .strip(),
            update=True,
        )
        project.environ["AUTHOR_EMAIL"] = project.EnvValue(
            project.run(["git", "-C", str(workon), "config", "user.email"])
            .stdout.decode()
            .strip(),
            update=True,
        )

    def post(self, workon):
        """Run `git add --all`.

        :param workon: Work-on folder.
        :type workon: :class:`pathlib.Path`
        """
        project.run(["git", "-C", str(workon), "add", "--all"])
