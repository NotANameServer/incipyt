"""Functions to call system programs and python modulse."""

import logging
import os
import subprocess

from incipyt import project
from incipyt._internal.templates import Formattable

logger = logging.getLogger(__name__)


def run(args, check=True, **kwargs):
    r"""Run a command after substitution using the environ.

    :param args: List of the command elements.
    :type args: :class:`list`
    :param \**kwargs: Other options forwarded to `subprocess.run`
    :return: Represents a process that has finished
    :rtype: :class:`subprocess.CompletedProcess`
    """
    formatted = [arg.format() if isinstance(arg, Formattable) else arg for arg in args]
    logger.info(" ".join(formatted))
    result = subprocess.run(formatted, capture_output=True, check=False, **kwargs)
    logger.info(result.stdout.decode())
    if check and result.returncode:
        logger.error(result.stderr.decode())
        raise subprocess.CalledProcessError(
            result.returncode, result.args, output=result.stdout, stderr=result.stderr
        )
    return result


def setenv_python_cmd(python_path):
    """Set PYTHON_CMD environment variable.

    :param python_path: List of the command elements.
    :type python_path: :class:`pathlib.Path`
    """
    if not python_path.is_absolute():
        raise AssertionError(f"{python_path} is not absolute.")
    del project.environ["PYTHON_CMD"]
    project.environ.inject("PYTHON_CMD", os.fspath(python_path))


def python_m(args, **kwargs):
    r"""Run a python module after substitution using the environ.

    :param args: List of the command elements, excluding `python -m`.
    :type args: :class:`list`
    :param \**kwargs: Other options forwarded to `subprocess.run`
    :return: Represents a process that has finished
    :rtype: :class:`subprocess.CompletedProcess`
    """
    return run([project.environ["PYTHON_CMD"], "-m", *args], **kwargs)


def build(args, **kwargs):
    r"""Run a python build after substitution using the environ.

    :param args: List of the command elements, excluding `python -m build`.
    :type args: :class:`list`
    :param \**kwargs: Other options forwarded to `subprocess.run`
    :return: Represents a process that has finished
    :rtype: :class:`subprocess.CompletedProcess`
    """
    return python_m(["build", *args], **kwargs)


def pip(args, **kwargs):
    r"""Run a pip command after substitution using the environ.

    :param args: List of the command elements, excluding `python -m pip`.
    :type args: :class:`list`
    :param \**kwargs: Other options forwarded to `subprocess.run`
    :return: Represents a process that has finished
    :rtype: :class:`subprocess.CompletedProcess`
    """
    return python_m(["pip", "--verbose", *args], **kwargs)


def pip_install(args, **kwargs):
    r"""Run a pip install command after substitution using the environ.

    :param args: List of the command elements, excluding `python -m pip`.
    :type args: :class:`list`
    :param \**kwargs: Other options forwarded to `subprocess.run`
    :return: Represents a process that has finished
    :rtype: :class:`subprocess.CompletedProcess`
    """
    return pip(["install", "--upgrade", "--upgrade-strategy", "eager", *args], **kwargs)


def venv(args, **kwargs):
    r"""Run a venv command after substitution using the environ.

    :param args: List of the command elements, excluding `python -m venv`.
    :type args: :class:`list`
    :param \**kwargs: Other options forwarded to `subprocess.run`
    :return: Represents a process that has finished
    :rtype: :class:`subprocess.CompletedProcess`
    """
    return python_m(["venv", *args], **kwargs)


def git(args, workon=None, **kwargs):
    r"""Run a git command inside of the ``workon`` dir.

    :param args: List of the command elements, excluding `git`.
    :type args: :class:`list`
    :param workon: Directory where to run the command, instead of .
    :type workon: :class:`pathlib.Path`
    :param \**kwargs: Other options forwarded to `subprocess.run`
    :return: Represents a process that has finished
    :rtype: :class:`subprocess.CompletedProcess`
    """
    return run(["git", "-C", os.fspath(workon), *args] if workon else ["git", *args], **kwargs)


def git_get_config(config, workon=None):
    r"""Retrieve the value of ``git config <config>``.

    :param config: The config name to retrieve
    :type args: :class:`str`
    :param workon: Directory where to run the command, instead of .
    :type workon: :class:`pathlib.Path`
    :return: The
    :rtype: :class:`str` | None
    """
    cmd = git(["config", config], workon=workon, check=False)
    if cmd.returncode == 0:
        return cmd.stdout.decode().strip() or None
    return None
