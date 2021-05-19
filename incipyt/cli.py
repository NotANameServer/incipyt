"""Command Line Interace functions."""

import click
import logging
import pathlib

from incipyt import actions, Environment, process_actions


@click.command(help="incipyt is a command-line tool that bootstraps a Python project.")
@click.argument(
    "folder",
    required=True,
    default=pathlib.Path(),
    type=click.Path(file_okay=False, path_type=pathlib.Path),
)
@click.option(
    "--yes",
    is_flag=True,
    help="Do not ask confirmation for variables with a default value.",
)
@click.option(
    "--check-build",
    is_flag=True,
    help="Build the package after initialization of all files and folders.",
)
def main(folder, yes, check_build):
    logging.basicConfig(level="INFO")

    env = Environment(auto_confirm=yes)
    if folder == pathlib.Path():
        if any(folder.resolve().iterdir()):
            raise click.BadArgumentUsage(f"FOLDER {folder.resolve()} is not empty.")
        env.push("PROJECT_NAME", folder.resolve().name)
    else:
        if folder.is_absolute() and folder.is_dir() and any(folder.iterdir()):
            raise click.BadArgumentUsage(f"FOLDER {folder} is not empty.")
        elif ("." / folder).is_dir() and any(("." / folder).resolve().iterdir()):
            raise click.BadArgumentUsage(f"FOLDER {folder} is not empty.")
        env.push("PROJECT_NAME", folder.name)

    process_actions(
        folder, env, [actions.Git(), actions.Venv(), actions.Setuptools(check_build)]
    )
