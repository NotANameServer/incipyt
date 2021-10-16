import logging
import os
import pathlib
import sys

import click

from incipyt import actions, project

logger = logging.getLogger(__name__)


@click.command(help="incipyt is a command-line tool that bootstraps a Python project.")
@click.argument(
    "folder",
    required=True,
    default=pathlib.Path(),
    type=click.Path(file_okay=False),
    callback=lambda _ctx, _param, _path: pathlib.Path(_path),
)
@click.version_option()
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

    actions_todo = [actions.Git(), actions.Venv(), actions.Setuptools(check_build)]

    for action in actions_todo:
        logger.info("Add %s to project structure.", action)
        action.add_to_structure()

    logger.info("Mkdir folder for project structure on %s.", str(folder))
    project.structure.mkdir(folder)

    for action in actions_todo:
        logger.info("Running pre-action for %s.", action)
        action.pre(folder)

    logger.info("Commit project structure.")
    project.structure.commit()

    for action in actions_todo:
        logger.info("Running post-action for %s.", action)
        action.post(folder)


# Remove '' and current working directory from the first entry of sys.path, if
# present to avoid using current directory in incipyt commands, when invoked as
# python -m incipyt <command>
if sys.path[0] in ("", os.getcwd()):
    sys.path.pop(0)

if __name__ == "__main__":
    sys.exit(main())
