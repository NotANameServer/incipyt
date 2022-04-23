import os

from incipyt import commands, signals, tools


class Venv(tools.Tool):
    """Scripts to add virtualenv to :class:`incipyt.project._Structure`."""

    def add_to_structure(self):
        """Add venv configuration to `project.structure`, do nothing."""
        signals.vcs_ignore.emit(pattern=".env")

    def pre(self, workon):
        """Run `python -m venv .env`.

        :param workon: Work-on folder.
        :type workon: :class:`pathlib.Path`
        """
        env_path = workon / ".env"
        commands.venv(["--upgrade-deps", os.fspath(env_path)])
        commands.setenv_python_cmd(
            env_path.resolve() / ("Scripts" if os.name == "nt" else "bin") / "python"
        )
