"""Command Line Interace fucntions."""

import click
import logging
import pathlib

from incipyt import actions, Environment, process_actions


@click.command()
@click.option("--root", type=str, default="", help="Root folder.")
def main(root):
    logging.basicConfig(level="INFO")
    process_actions(
        pathlib.Path().joinpath(root),
        Environment(),
        [actions.Git(), actions.Venv(), actions.Setuptools()],
    )
