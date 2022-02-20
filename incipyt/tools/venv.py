import os

from incipyt import tools, signals, project
from incipyt._internal import templates


class Venv(tools.Tool):
    """Scripts to add virtualenv to :class:`incipyt.project._Structure`."""

    def add_to_structure(self):
        """Add venv configuration to `project.structure`, do nothing."""
        signals.vcs_ignore.emit(pattern=templates.Transform(".env"))

    def pre(self, workon):
        """Run `python -m venv .env`.

        :param workon: Work-on folder.
        :type workon: :class:`pathlib.Path`
        """
        env_path = workon / ".env"
        py_path = env_path / ("Scripts" if os.name == "nt" else "bin") / "python"
        project.run(
            [
                project.python.string_template,
                "-m",
                "venv",
                "--upgrade-deps",
                str(env_path),
            ]
        )
        project.environ[project.python.variable] = project.EnvValue(
            str(py_path), update=True
        )
