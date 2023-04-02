import logging
import os
import pathlib
import sys
import warnings

import click

from incipyt import project, tools
from incipyt._internal.utils import EnvValue

logger = logging.getLogger(__name__)
DEFAULT_LOGGING_LEVEL = logging.WARNING
DEFAULT_FORMAT = "[%(levelname)s] %(message)s"
DEBUG_FORMAT = "%(asctime)s [%(levelname)s] <%(funcName)s> %(message)s"


def choice_callback(_ctx, _param, _choice):
    return getattr(tools, _choice) if _choice else (lambda *args: None)


@click.command(help="incipyt is a command-line tool that bootstraps a Python project.")
@click.argument(
    "folder",
    required=True,
    default=pathlib.Path(),
    type=click.Path(file_okay=False),
    callback=lambda _ctx, _param, _path: pathlib.Path(_path),
)
@click.option("-v", "--verbose", count=True)
@click.option("-s", "--silent", count=True)
@click.version_option()
@click.option(
    "--vcs",
    required=True,
    show_default=True,
    default="Git",
    type=click.Choice(["", "Git"], case_sensitive=False),
    callback=choice_callback,
    help="Version Control System, if any, to use.",
)
@click.option(
    "--env",
    required=True,
    show_default=True,
    default="Venv",
    type=click.Choice(["", "Venv"], case_sensitive=False),
    callback=choice_callback,
    help="Wether to use a virtual environment and which one.",
)
@click.option(
    "--build",
    required=True,
    show_default=True,
    default="Setuptools",
    type=click.Choice(["Setuptools", "Flit", "Hatch", "PDM", "Poetry"], case_sensitive=False),
    callback=choice_callback,
    help="Build system to use for building wheel and source distributions.",
)
@click.option(
    "--check-build",
    is_flag=True,
    help="Build the package after initialization of all files and folders.",
)
@click.option(
    "--license",
    required=True,
    default="Copyright",
    type=click.Choice(tools.license.classifiers, case_sensitive=False),
    help="Software license",
    prompt=True,
)
def main(folder, verbose, silent, vcs, env, build, check_build, license):  # noqa: A002
    log_level = DEFAULT_LOGGING_LEVEL - verbose * 10 + silent * 10
    setup_logging(max(logging.NOTSET, min(log_level, logging.CRITICAL)))

    if folder == pathlib.Path():
        if any(folder.resolve().iterdir()):
            raise click.BadArgumentUsage(f"FOLDER {folder.resolve()} is not empty.")
        project.environ["PROJECT_NAME"] = folder.resolve().name
    else:
        if (folder.is_absolute() and folder.is_dir() and any(folder.iterdir())) or (
            ("." / folder).is_dir() and any(("." / folder).resolve().iterdir())
        ):
            raise click.BadArgumentUsage(f"FOLDER {folder} is not empty.")
        project.environ["PROJECT_NAME"] = folder.name

    project.environ["LICENSE"] = EnvValue(license, confirmed=True)

    tools_to_install = [
        tool for tool in [tools.License(), vcs(), env(), build(check_build)] if tool
    ]

    for tool in tools_to_install:
        logger.info("Using %s", tool)
        tool.add_to_structure()

    logger.info("The project will be created at %s", folder.resolve())
    project.structure.mkdir(folder)

    for tool in tools_to_install:
        logger.info("Running pre-script for %s...", tool)
        tool.pre(folder)

    logger.info("Commit project structure.")
    project.structure.commit()

    for tool in tools_to_install:
        logger.info("Running post-script for %s...", tool)
        tool.post(folder)

    logger.info("All done.")


class ColoredFormatter(logging.Formatter):
    """Classic formatter with colored [LEVEL]."""

    colors = {10: (34, 49), 20: (32, 49), 30: (33, 49), 40: (31, 49), 50: (37, 41)}

    def format(self, record):  # noqa: A003
        fg, bg = type(self).colors.get(record.levelno, (32, 49))
        record.levelname = f"\033[1;{fg}m\033[1;{bg}m{record.levelname}\033[0m"
        return super().format(record)


def supports_color(stream):
    """Determine if the given stream support colors."""
    platform_is_supported = True
    stream_is_a_tty = hasattr(stream, "isatty") and stream.isatty()
    return (platform_is_supported or "ANSICON" in os.environ) and stream_is_a_tty


def setup_logging(verbosity):
    """Set up the root logger.

    Replace the current root logger handlers by a new
    :class:`logging.StreamHandler` with the correct level and formatter.

    When the requested :param verbosity: is more verbose than
    :data:`logging.DEBUG` then the python warnings are logged too.

    :param verbosity int: the verbosity level to use on the root logger
    """
    root_logger = logging.getLogger("" if __name__ == "__main__" else __package__)
    stdout = logging.StreamHandler()
    f_cls = ColoredFormatter if supports_color(stdout.stream) else logging.Formatter
    f_format = DEFAULT_FORMAT if verbosity > logging.DEBUG else DEBUG_FORMAT
    stdout.formatter = f_cls(f_format)
    root_logger.handlers.clear()
    root_logger.handlers.append(stdout)
    root_logger.level = max(verbosity, logging.DEBUG)
    logger.level = root_logger.level - 10
    if verbosity < logging.DEBUG:
        logging.captureWarnings(capture=True)
        warnings.filterwarnings("default")


# Remove '' and current working directory from the first entry of sys.path, if
# present to avoid using current directory in incipyt commands, when invoked as
# python -m incipyt <command>
if sys.path[0] in ("", os.getcwd()):  # noqa: PTH109
    sys.path.pop(0)

if __name__ == "__main__":
    sys.exit(main())
