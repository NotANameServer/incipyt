"""Functions to call system programs and python modulse."""

import logging
import os
import subprocess

from incipyt import project

from incipyt._internal.templates import Formattable
from incipyt._internal.utils import EnvValue

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
    assert python_path.is_absolute(), f"{python_path} is not absolute."
    project.environ["PYTHON_CMD"] = EnvValue(os.fspath(python_path), update=True)


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
    return python_m(["pip", "--verbose"] + args, **kwargs)


def pip_install(args, **kwargs):
    r"""Run a pip install command after substitution using the environ.

    :param args: List of the command elements, excluding `python -m pip`.
    :type args: :class:`list`
    :param \**kwargs: Other options forwarded to `subprocess.run`
    :return: Represents a process that has finished
    :rtype: :class:`subprocess.CompletedProcess`
    """
    return pip(["install", "--upgrade", "--upgrade-strategy", "eager"] + args, **kwargs)


def venv(args, **kwargs):
    r"""Run a venv command after substitution using the environ.

    :param args: List of the command elements, excluding `python -m venv`.
    :type args: :class:`list`
    :param \**kwargs: Other options forwarded to `subprocess.run`
    :return: Represents a process that has finished
    :rtype: :class:`subprocess.CompletedProcess`
    """
    return python_m(["venv"] + args, **kwargs)
