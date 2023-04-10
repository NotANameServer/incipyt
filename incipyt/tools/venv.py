import os

from incipyt import commands, signals, tools
from incipyt._internal.templates import FormatterEnviron


class Venv(tools.Tool):
    """Scripts to add virtualenv to :class:`incipyt.project._Structure`."""

    def add_to_structure(self):
        """Add venv configuration to `project.structure`, do nothing."""
        signals.vcs_ignore.emit(pattern="{VENV_FOLDER}/")

    def pre(self, workon):
        """Run `python -m venv .env`.

        :param workon: Work-on folder.
        :type workon: :class:`pathlib.Path`
        """
        env_path = workon / FormatterEnviron().format("{VENV_FOLDER}")
        commands.venv([os.fspath(env_path)])
        commands.setenv_python_cmd(
            env_path.resolve() / ("Scripts" if os.name == "nt" else "bin") / "python"
        )
        commands.pip_install(["pip>=21.3.0"])
