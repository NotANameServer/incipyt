from incipyt import actions, hooks, project
from incipyt._internal import templates
from incipyt._internal.dumpers import Requirement


class Git(actions._Action):
    """Action to add Git to :class:`incipyt.project.Hierarchy`."""

    def __init__(self):
        hooks.VCSIgnore.register(self._hook)

    def add_to(self, hierarchy):
        """Add git configuration to `hierarchy`.

        Register git related project URLs:
        - Repository: {REPOSITORY}
        - Issue: {REPOSITORY}/issues
        - Documentation: {REPOSITORY}/wiki

        :param hierarchy: The actual hierarchy to update with git configuration.
        :type hierarchy: :class:`incipyt.project.Hierarchy`
        """
        hook_url = hooks.ProjectURL(hierarchy)
        hook_url("Repository", templates.Requires("{REPOSITORY}"))
        hook_url("Issue", templates.Requires("{REPOSITORY}/issues"))
        hook_url("Documentation", templates.Requires("{REPOSITORY}/wiki"))

    def _hook(self, hierarchy, value):
        gitignore = hierarchy.get_configuration(Requirement(".gitignore"))
        gitignore[None] = [value]

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
