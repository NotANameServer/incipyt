"""Functions to call system programs and python modulse."""

import logging
import subprocess

from incipyt import project

from incipyt._internal.utils import EnvValue, formattable

logger = logging.getLogger(__name__)


def run(args, **kwargs):
    r"""Run a command after substitution using the environ.

    :param args: List of the command elements.
    :type args: :class:`list`
    :param \**kwargs: Other options forwarded to `subprocess.run`
    :return: Represents a process that has finished
    :rtype: :class:`subprocess.CompletedProcess`
    """
    formatted = [arg.format() if formattable(arg) else arg for arg in args]
    logger.info(" ".join(formatted))
    result = subprocess.run(formatted, capture_output=True, check=True, **kwargs)
    logger.info(result.stdout.decode())
    return result


def setenv_python_cmd(python_path):
    """Set PYTHON_CMD environment variable.

    :param python_path: List of the command elements.
    :type python_path: :class:`pathlib.Path`
    """
    project.environ["PYTHON_CMD"] = EnvValue(str(python_path), update=True)


def python_m(args, **kwargs):
    r"""Run a python module after substitution using the environ.

    :param args: List of the command elements, excluding `python -m`.
    :type args: :class:`list`
    :param \**kwargs: Other options forwarded to `subprocess.run`
    :return: Represents a process that has finished
    :rtype: :class:`subprocess.CompletedProcess`
    """
    # from incipyt._internal.templates import StringTemplate

    return run([project.environ["PYTHON_CMD"], "-m"] + args, **kwargs)


def build(args, **kwargs):
    r"""Run a python build after substitution using the environ.

    :param args: List of the command elements, excluding `python -m build`.
    :type args: :class:`list`
    :param \**kwargs: Other options forwarded to `subprocess.run`
    :return: Represents a process that has finished
    :rtype: :class:`subprocess.CompletedProcess`
    """
    return python_m(["build"] + args, **kwargs)


def pip(args, **kwargs):
    r"""Run a pip command after substitution using the environ.

    :param args: List of the command elements, excluding `python -m pip`.
    :type args: :class:`list`
    :param \**kwargs: Other options forwarded to `subprocess.run`
    :return: Represents a process that has finished
    :rtype: :class:`subprocess.CompletedProcess`
    """
    return python_m(["pip"] + args, **kwargs)


def venv(args, **kwargs):
    r"""Run a venv command after substitution using the environ.

    :param args: List of the command elements, excluding `python -m venv`.
    :type args: :class:`list`
    :param \**kwargs: Other options forwarded to `subprocess.run`
    :return: Represents a process that has finished
    :rtype: :class:`subprocess.CompletedProcess`
    """
    return python_m(["venv"] + args, **kwargs)
