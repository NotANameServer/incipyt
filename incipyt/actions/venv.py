import os

from incipyt import actions
from incipyt import hooks

from incipyt._internal import templates


class Venv(actions._Action):
    """Action to add virtualenv to :class:`incipyt.system.Hierarchy`."""

    def add_to(self, hierarchy):
        """Add venv configuration to `hierarchy`, do nothing.

        :param hierarchy: The actual hierarchy to update with venv configuration.
        :type hierarchy: :class:`incipyt.system.Hierarchy`
        """
        hook = hooks.VCSIgnore(hierarchy)
        hook(templates.Transform(".env"))

    def pre(self, workon, environment):
        """Run `python -m venv .env`.

        :param workon: Work-on folder.
        :type workon: :class:`pathlib.Path`
        :param environment: Environment used to do pre-action
        :type environment: :class:`incipyt.system.Environment`
        """
        env_path = workon / ".env"
        py_path = env_path / ("Scripts" if os.name == "nt" else "bin") / "python"
        environment.run(
            [
                templates.Requires("{PYTHON_CMD}"),
                "-m",
                "venv",
                str(env_path),
            ]
        )
        environment.push("PYTHON_CMD", str(py_path), update=True)
