from incipyt import hooks

from incipyt._internal import utils
from incipyt._internal.dumpers import Requirement


class Git:
    """Action to add Git to :class:`incipyt.system.Hierarchy`."""

    def __init__(self):
        hooks.VCSIgnore.register(self._hook)

    def add_to(self, hierarchy):
        """Add git configuration to `hierarchy`.

        Register git related project URLs:
        - Repository: {Repository}
        - Issue: {Repository}/issues
        - Documentation: {Repository}/wiki

        :param hierarchy: The actual hierarchy to update with git configuration.
        :type hierarchy: :class:`incipyt.system.Hierarchy`
        """
        hook_url = hooks.ProjectURL(hierarchy)
        hook_url("Repository", utils.Requires("{Repository}"))
        hook_url("Issue", utils.Requires("{Repository}/issues"))
        hook_url("Documentation", utils.Requires("{Repository}/wiki"))

    def _hook(self, hierarchy, value):
        gitignore = hierarchy.get_configuration(Requirement.make(".gitignore"))
        if None not in gitignore:
            gitignore[None] = []

        gitignore[None].append(value)

    def __str__(self):
        return "git"

    def pre(self, workon, environment):
        """Run `git init`.

        Also push {AUTHOR_NAME} and {AUTHOR_EMAIL} using `git config user.*`.

        :param workon: Work-on folder.
        :type workon: :class:`pathlib.Path`
        :param environment: Environment used to do pre-action
        :type environment: :class:`incipyt.system.Environment`
        """
        environment.run(
            [
                "git",
                "init",
                str(workon),
            ]
        )

        environment.push(
            "AUTHOR_NAME",
            environment.run(
                [
                    "git",
                    "-C",
                    str(workon),
                    "config",
                    "user.name",
                ]
            ).strip(),
            update=True,
        )
        environment.push(
            "AUTHOR_EMAIL",
            environment.run(
                [
                    "git",
                    "-C",
                    str(workon),
                    "config",
                    "user.email",
                ]
            ).strip(),
            update=True,
        )

    def post(self, workon, environment):
        """Run `git add --all`.

        :param workon: Work-on folder.
        :type workon: :class:`pathlib.Path`
        :param environment: Environment used to do post-action
        :type environment: :class:`incipyt.system.Environment`
        """
        environment.run(
            [
                "git",
                "-C",
                str(workon),
                "add",
                "--all",
            ]
        )
