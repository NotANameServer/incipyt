import logging
import os
import shutil
import sys

import click

from incipyt import project, signals, tools
from incipyt._internal.dumpers import TextFile
from incipyt.commands import git, git_get_config

logger = logging.getLogger(__name__)


class Git(tools.Tool):
    """Scripts to add Git to :class:`incipyt.project._Structure`."""

    def __init__(self):
        if not shutil.which("git"):
            logger.error("%r is missing from the PATH. Abort.", "git")
            sys.exit(1)

        signals.vcs_ignore.connect(self._slot)

    def add_to_structure(self):
        """Add git configuration to `project.structure`.

        Register git related project URLs.

        URLs:
            - Repository: {REPOSITORY}
            - Issue: {REPOSITORY}/issues
            - Documentation: {REPOSITORY}/wiki
        """
        project.structure.use_template("python.gitignore", ".gitignore")
        signals.project_url.emit(url_kind="Documentation", url_value="{REPOSITORY}/wiki")
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
        git(["init", os.fspath(workon)])
        git_name = git_get_config("user.name", workon=workon)
        if git_name:
            project.environ.suggest("AUTHOR_NAME", git_name)
        git_email = git_get_config("user.email", workon=workon)
        if git_email:
            project.environ.suggest("AUTHOR_EMAIL", git_email)

    def post(self, workon):
        """Check config name+email and then run `git add --all`.

        :param workon: Work-on folder.
        :type workon: :class:`pathlib.Path`
        """
        env_name = project.environ["AUTHOR_NAME"]
        git_name = git_get_config("user.name", workon=workon)
        prompt = f"Git user name is {git_name!r}, use {env_name!r} instead?"
        if env_name != git_name and click.confirm(prompt, default=None):
            git(["config", "user.name", env_name], workon=workon)

        env_email = project.environ["AUTHOR_EMAIL"]
        git_email = git_get_config("user.email", workon=workon)
        prompt = f"Git user email is {git_email!r}, use {env_email!r} instead?"
        if env_email != git_email and click.confirm(prompt, default=None):
            git(["config", "user.email", env_email], workon=workon)

        git(["add", "--all"], workon=workon)
