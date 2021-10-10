import os

from incipyt import actions, hooks, project
from incipyt._internal import templates


class Venv(actions._Action):
    """Action to add virtualenv to :class:`incipyt.project.Hierarchy`."""

    def add_to(self, hierarchy):
        """Add venv configuration to `hierarchy`, do nothing.

        :param hierarchy: The actual hierarchy to update with venv configuration.
        :type hierarchy: :class:`incipyt.project.Hierarchy`
        """
        hook = hooks.VCSIgnore(hierarchy)
        hook(templates.Transform(".env"))

    def pre(self, workon):
        """Run `python -m venv .env`.

        :param workon: Work-on folder.
        :type workon: :class:`pathlib.Path`
        """
        env_path = workon / ".env"
        py_path = env_path / ("Scripts" if os.name == "nt" else "bin") / "python"
        project.run([project.python.requires, "-m", "venv", str(env_path)])
        project.environ[project.python.variable] = project.EnvValue(
            str(py_path), update=True
        )
