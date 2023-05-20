import logging
import os
import pathlib
import sys
import warnings

import click
import click.core

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from incipyt import project, tools

logger = logging.getLogger(__name__)
DEFAULT_LOGGING_LEVEL = logging.WARNING
DEFAULT_FORMAT = "[%(levelname)s] %(message)s"
DEBUG_FORMAT = "%(asctime)s [%(levelname)s] <%(funcName)s> %(message)s"
OS_ENVIRON_PREFIX = "INCIPYT_"
APP_DIR = pathlib.Path(click.get_app_dir("incipyt"))


class IncipytCommand(click.Command):
    def format_help(self, ctx, formatter):
        self.format_usage(ctx, formatter)
        self.format_help_text(ctx, formatter)
        self.format_options(ctx, formatter)
        self.format_variables(ctx, formatter)  # incipyt custom
        self.format_epilog(ctx, formatter)

    def format_variables(self, ctx, formatter) -> None:
        with formatter.section("Variables"):
            formatter.write_dl(
                [
                    (f"-o {var.name}={var.default!r}", var.help)
                    for var in project.variables.values()
                    if var.prompt
                ]
            )


def choice_tool(_ctx, _param, _choice):
    return getattr(tools, _choice) if _choice else (lambda *args: None)


@click.command(
    cls=IncipytCommand, help="incipyt is a command-line tool that bootstraps a Python project."
)
@click.argument(
    "folder",
    required=True,
    default=pathlib.Path(),
    type=click.Path(file_okay=False, path_type=pathlib.Path),
    callback=lambda _ctx, _param, _path: pathlib.Path(_path),
)
@click.option("-v", "--verbose", count=True)
@click.option("-s", "--silent", count=True)
@click.option(
    "-c",
    "--config",
    default=APP_DIR / "config.toml",
    type=click.Path(exists=False, dir_okay=False, path_type=pathlib.Path),
    help="Path of the configuration file.",
    show_default=True,
)
@click.version_option()
@click.option(
    "--license",
    required=True,
    default="Copyright",
    type=click.Choice(tools.license.classifiers, case_sensitive=False),
    help="Software license.",
    prompt=True,
)
@click.option(
    "--vcs",
    required=True,
    show_default=True,
    default="Git",
    type=click.Choice(["", "Git"], case_sensitive=False),
    callback=choice_tool,
    help="Version Control System, if any, to use.",
)
@click.option(
    "--env",
    required=True,
    show_default=True,
    default="Venv",
    type=click.Choice(["", "Venv"], case_sensitive=False),
    callback=choice_tool,
    help="Wether to use a virtual environment and which one.",
)
@click.option(
    "--build",
    required=True,
    show_default=True,
    default="Setuptools",
    type=click.Choice(["Setuptools", "Flit", "Hatch", "PDM", "Poetry"], case_sensitive=False),
    callback=choice_tool,
    help="Build system to use for building wheel and source distributions.",
)
# Other options:
@click.option(
    "--check-build",
    is_flag=True,
    help="Build the package after initialization of all files and folders.",
)
@click.option(
    "--option",
    "-o",
    "options",
    multiple=True,
    metavar="KEY=VALUE",
    help="Additionnal key=value pair for the environment, see variables below.",
)
@click.pass_context
def main(ctx, folder, verbose, silent, config, vcs, env, build, check_build, options, **kwargs):
    log_level = DEFAULT_LOGGING_LEVEL - verbose * 10 + silent * 10
    setup_logging(max(logging.NOTSET, min(log_level, logging.CRITICAL)))

    if not config.exists():
        if ctx.get_parameter_source("config") == click.core.ParameterSource.DEFAULT:
            config.parent.mkdir(exist_ok=True)
            config.touch()
        else:
            raise click.BadArgumentUsage(f"CONFIG {config.resolve()} does not exists.")
    try:
        with config.open("rb") as config_file:
            feed_environ(tomllib.load(config_file), options, os.environ, **kwargs)
    except ValueError as exc:
        raise click.BadArgumentUsage(exc.args[0]) from exc

    tools_to_install = [tool for tool in [vcs(), tools.License(), env(), build()] if tool]

    if folder == pathlib.Path():
        if any(folder.resolve().iterdir()):
            raise click.BadArgumentUsage(f"FOLDER {folder.resolve()} is not empty.")
        project.environ.suggest("PROJECT_NAME", folder.resolve().name)
    else:
        if (folder.is_absolute() and folder.is_dir() and any(folder.iterdir())) or (
            ("." / folder).is_dir() and any(("." / folder).resolve().iterdir())
        ):
            raise click.BadArgumentUsage(f"FOLDER {folder} is not empty.")
        project.environ.suggest("PROJECT_NAME", folder.name)

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


def feed_environ(config_options=None, cli_options=None, osenviron=None, **kwargs):
    project.environ.clear()

    config_options = config_options or {}
    cli_options = cli_options or {}
    osenviron = osenviron or {}

    project.environ.feed_cli(dict([option.split("=", 1) for option in cli_options]))
    project.environ.feed_cli({key.upper(): value for key, value in kwargs.items()})

    project.environ.feed_config(config_options)

    project.environ.feed_osenviron(
        {
            key[len(OS_ENVIRON_PREFIX) :]: value
            for key, value in osenviron.items()
            if key.startswith(OS_ENVIRON_PREFIX)
        },
        prompt=False,
    )
    project.environ.feed_osenviron(
        {
            key: value
            for key, value in osenviron.items()
            if not key.startswith(OS_ENVIRON_PREFIX) and key in project.variables
        },
        prompt=True,
    )

    project.environ.feed_default(
        {var.name: var.default for var in project.variables.values() if not var.prompt},
        prompt=False,
    )
    project.environ.feed_default(
        {
            var.name: var.default
            for var in project.variables.values()
            if var.prompt and var.default
        },
        prompt=True,
    )


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


if __name__ == "__main__":
    # Remove '' and current working directory from the first entry of
    # sys.path, if present to avoid using current directory in incipyt
    # commands, when invoked as python -m incipyt <command>
    if sys.path[0] in ("", os.getcwd()):  # noqa: PTH109
        sys.path.pop(0)
    sys.exit(main())
