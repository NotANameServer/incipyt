import os

from incipyt import commands, project, signals, tools
from incipyt._internal.dumpers import TextFile


class Git(tools.Tool):
    """Scripts to add Git to :class:`incipyt.project._Structure`."""

    def __init__(self):
        signals.vcs_ignore.connect(self._slot)

    def add_to_structure(self):
        """Add git configuration to `project.structure`.

        Register git related project URLs.

        URLs:
            - Repository: {REPOSITORY}
            - Issue: {REPOSITORY}/issues
            - Documentation: {REPOSITORY}/wiki
        """
        signals.project_url.emit(
            url_kind="Documentation", url_value="{REPOSITORY}/wiki"
        )
        signals.project_url.emit(url_kind="Issue", url_value="{REPOSITORY}/issues")
        signals.project_url.emit(url_kind="Repository", url_value="{REPOSITORY}")

    def _slot(self, pattern, **kwargs):
        project.structure.get_config_list(TextFile(".gitignore")).append(pattern)

    def pre(self, workon):
        """Run `git init`.

        Also push {AUTHOR_NAME} and {AUTHOR_EMAIL} using `git config user.*`.

        :param workon: Work-on folder.
        :type workon: :class:`pathlib.Path`
        """
        commands.run(["git", "init", os.fspath(workon)])

        project.environ["AUTHOR_EMAIL"] = project.EnvValue(
            commands.run(["git", "-C", os.fspath(workon), "config", "user.email"])
            .stdout.decode()
            .strip(),
            update=True,
        )
        project.environ["AUTHOR_NAME"] = project.EnvValue(
            commands.run(["git", "-C", os.fspath(workon), "config", "user.name"])
            .stdout.decode()
            .strip(),
            update=True,
        )

    def post(self, workon):
        """Run `git add --all`.

        :param workon: Work-on folder.
        :type workon: :class:`pathlib.Path`
        """
        commands.run(["git", "-C", os.fspath(workon), "add", "--all"])
