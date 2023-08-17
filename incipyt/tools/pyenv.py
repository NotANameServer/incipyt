import logging
import os
import pathlib
import shutil
import sys

from incipyt import commands, project, signals, tools
from incipyt._internal.templates import FormatterEnviron, StringTemplate

logger = logging.getLogger(__name__)


class PyEnv(tools.Tool):
    """Scripts to add pyenv virtualenv to :class:`incipyt.project._Structure`."""

    def __init__(self):
        if not shutil.which("pyenv"):
            logger.error("%r is missing from the PATH. Abort.", "git")
            sys.exit(1)

        cmd = commands.run(["pyenv", "root"])
        pyenv_root = cmd.stdout.decode().strip()
        if not pyenv_root:
            logger.error("Pyenv root seems invalid.")
            sys.exit(1)
        project.environ.inject("PYENV_ROOT", pathlib.Path(pyenv_root))

        cmd = commands.run(["pyenv", "global"])
        global_version = cmd.stdout.decode().strip() or None
        if global_version:
            project.environ.suggest("PYENV_VERSION", global_version)

    def add_to_structure(self):
        """Add pyenv virtualenv configuration to `project.structure`, do nothing."""
        signals.vcs_ignore.emit(pattern=".python-version")

    def pre(self, workon):
        """Run `pyenv virutalenv {PYENV_VERSION} {PROJECT_NAME}`.

        :param workon: Work-on folder.
        :type workon: :class:`pathlib.Path`
        """
        commands.run(
            [
                "pyenv",
                "virtualenv",
                StringTemplate("{PYENV_VERSION}"),
                StringTemplate("{PROJECT_NAME}_{PYENV_VERSION}"),
            ]
        )
        commands.run(["pyenv", "local", StringTemplate("{PROJECT_NAME}_{PYENV_VERSION}")])
        env_path = (
            project.environ["PYENV_ROOT"]
            / "versions"
            / FormatterEnviron().format("{PYENV_VERSION}")
            / "envs"
            / FormatterEnviron().format("{PROJECT_NAME}_{PYENV_VERSION}")
        )
        commands.setenv_python_cmd(
            env_path.resolve() / ("Scripts" if os.name == "nt" else "bin") / "python"
        )
        commands.pip_install(["pip>=21.3.0"])
