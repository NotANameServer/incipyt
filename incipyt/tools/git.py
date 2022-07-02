import logging
import os
import shutil
import sys

import click

from incipyt import commands, project, signals, tools
from incipyt._internal.dumpers import TextFile


logger = logging.getLogger(__name__)


class Git(tools.Tool):
    """Scripts to add Git to :class:`incipyt.project._Structure`."""

    def __init__(self, force_vcs_config):
        if not shutil.which("git"):
            logger.error("%r is missing from the PATH. Abort.", "git")
            sys.exit(1)

        self.force_vcs_config = force_vcs_config
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

        git_user_email_return = commands.run(
            ["git", "-C", os.fspath(workon), "config", "user.email"], check=False
        )
        if git_user_email_return.returncode == 0:
            project.environ["AUTHOR_EMAIL"] = project.EnvValue(
                git_user_email_return.stdout.decode().strip(), update=True
            )

        git_user_name_return = commands.run(
            ["git", "-C", os.fspath(workon), "config", "user.name"], check=False
        )
        if git_user_name_return.returncode == 0:
            project.environ["AUTHOR_NAME"] = project.EnvValue(
                git_user_name_return.stdout.decode().strip(), update=True
            )

    def post(self, workon):
        """Run `git add --all`.

        :param workon: Work-on folder.
        :type workon: :class:`pathlib.Path`
        """
        git_user_email_return = commands.run(
            ["git", "-C", os.fspath(workon), "config", "user.email"], check=False
        )
        git_user_email = (
            git_user_email_return.stdout.decode().strip()
            if not git_user_email_return.returncode
            else None
        )

        git_user_name_return = commands.run(
            ["git", "-C", os.fspath(workon), "config", "user.name"], check=False
        )
        git_user_name = (
            git_user_name_return.stdout.decode().strip()
            if not git_user_name_return.returncode
            else None
        )

        if (
            git_user_email != project.environ["AUTHOR_EMAIL"]
            or git_user_name != project.environ["AUTHOR_NAME"]
        ):
            git_user_formatted = (
                f"{git_user_name if git_user_name else 'UNDEFINED'} "
                f"<{git_user_email if git_user_email else 'UNDEFINED'}>"
            )
            project_user_formatted = (
                f"{project.environ['AUTHOR_NAME'] if project.environ['AUTHOR_NAME'] else 'UNDEFINED'} "
                f"<{project.environ['AUTHOR_EMAIL'] if project.environ['AUTHOR_EMAIL'] else 'UNDEFINED'}>"
            )
            if self.force_vcs_config or click.confirm(
                f'Git user is "{git_user_formatted}", use "{project_user_formatted}" instead?',
                default=None,
            ):
                if git_user_email != project.environ["AUTHOR_EMAIL"]:
                    commands.run(
                        [
                            "git",
                            "-C",
                            os.fspath(workon),
                            "config",
                            "user.email",
                            project.environ["AUTHOR_EMAIL"],
                        ]
                    )
                if git_user_name != project.environ["AUTHOR_NAME"]:
                    commands.run(
                        [
                            "git",
                            "-C",
                            os.fspath(workon),
                            "config",
                            "user.name",
                            project.environ["AUTHOR_NAME"],
                        ]
                    )

        commands.run(["git", "-C", os.fspath(workon), "add", "--all"])
