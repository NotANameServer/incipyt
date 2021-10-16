from incipyt import actions, hooks, project
from incipyt._internal import templates
from incipyt._internal.dumpers import Requirement


class Git(actions._Action):
    """Action to add Git to :class:`incipyt.project._Structure`."""

    def __init__(self):
        hooks.VCSIgnore.register(self._hook)

    def add_to_structure(self):
        """Add git configuration to `project.structure`.

        Register git related project URLs:
        - Repository: {REPOSITORY}
        - Issue: {REPOSITORY}/issues
        - Documentation: {REPOSITORY}/wiki
        """
        hook_url = hooks.ProjectURL()
        hook_url("Repository", templates.Requires("{REPOSITORY}"))
        hook_url("Issue", templates.Requires("{REPOSITORY}/issues"))
        hook_url("Documentation", templates.Requires("{REPOSITORY}/wiki"))

    def _hook(self, value):
        gitignore = project.structure.get_configuration(Requirement(".gitignore"))
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
