from incipyt import actions, hooks
from incipyt._internal import templates
from incipyt._internal.dumpers import Requirement
from incipyt.os import EnvValue


class Git(actions._Action):
    """Action to add Git to :class:`incipyt.os.Hierarchy`."""

    def __init__(self):
        hooks.VCSIgnore.register(self._hook)

    def add_to(self, hierarchy):
        """Add git configuration to `hierarchy`.

        Register git related project URLs:
        - Repository: {REPOSITORY}
        - Issue: {REPOSITORY}/issues
        - Documentation: {REPOSITORY}/wiki

        :param hierarchy: The actual hierarchy to update with git configuration.
        :type hierarchy: :class:`incipyt.os.Hierarchy`
        """
        hook_url = hooks.ProjectURL(hierarchy)
        hook_url("Repository", templates.Requires("{REPOSITORY}"))
        hook_url("Issue", templates.Requires("{REPOSITORY}/issues"))
        hook_url("Documentation", templates.Requires("{REPOSITORY}/wiki"))

    def _hook(self, hierarchy, value):
        gitignore = hierarchy.get_configuration(Requirement(".gitignore"))
        gitignore[None] = [value]

    def pre(self, workon, environment):
        """Run `git init`.

        Also push {AUTHOR_NAME} and {AUTHOR_EMAIL} using `git config user.*`.

        :param workon: Work-on folder.
        :type workon: :class:`pathlib.Path`
        :param environment: Environment used to do pre-action
        :type environment: :class:`incipyt.os.Environment`
        """
        environment.run(["git", "init", str(workon)])

        environment["AUTHOR_NAME"] = EnvValue(
            environment.run(["git", "-C", str(workon), "config", "user.name"]).strip(),
            update=True,
        )
        environment["AUTHOR_EMAIL"] = EnvValue(
            environment.run(["git", "-C", str(workon), "config", "user.email"]).strip(),
            update=True,
        )

    def post(self, workon, environment):
        """Run `git add --all`.

        :param workon: Work-on folder.
        :type workon: :class:`pathlib.Path`
        :param environment: Environment used to do post-action
        :type environment: :class:`incipyt.os.Environment`
        """
        environment.run(["git", "-C", str(workon), "add", "--all"])
