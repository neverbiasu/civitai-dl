"""Command-line interface for Civitai Downloader."""

import logging
import sys
import os
from importlib import import_module

import click

from civitai_dl import __version__
from civitai_dl.cli.commands.config import config
from civitai_dl.cli.commands.download import download
from civitai_dl.cli.commands.browse import browse as browse_commands
from civitai_dl.utils.logger import get_logger, setup_logging

logger = get_logger(__name__)


@click.group()
@click.version_option(version=__version__)
@click.option("--verbose", "-v", count=True, help="Increase verbosity level")
@click.option("--quiet", "-q", is_flag=True, help="Silent mode, errors only")
def cli(verbose: int = 0, quiet: bool = False) -> None:
    """Civitai Downloader - Download and manage Civitai resources."""
    # Set logging level based on options
    if quiet:
        log_level = logging.ERROR  # Only show errors in quiet mode
    else:
        # Determine level based on verbosity count
        log_levels = [logging.INFO, logging.DEBUG, logging.NOTSET]
        # Ensure index doesn't exceed available levels
        level_index = min(verbose, len(log_levels) - 1)
        log_level = log_levels[level_index]

    # Initialize logging system
    setup_logging(log_level)

    # Log appropriate message based on level
    if log_level == logging.DEBUG:
        logger.debug("Debug mode enabled")
    elif log_level == logging.INFO:
        logger.info("Verbose logging enabled")


def import_commands() -> None:
    """Dynamically import all command modules from the commands directory.

    Searches the commands directory for Python modules and imports them,
    registering any commands with matching names to the CLI.
    """
    commands_dir = os.path.join(os.path.dirname(__file__), "commands")

    try:
        for filename in os.listdir(commands_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = filename[:-3]  # Remove .py extension
                try:
                    module = import_module(f"civitai_dl.cli.commands.{module_name}")
                    if hasattr(module, module_name):
                        command = getattr(module, module_name)
                        cli.add_command(command)
                        logger.debug(f"Imported command module: {module_name}")
                    else:
                        logger.debug(f"Module {module_name} does not define a matching command")
                except ImportError as e:
                    logger.warning(f"Failed to import {module_name}: {str(e)}")
    except Exception as e:
        logger.error(f"Error scanning commands directory: {str(e)}")


# Register command groups
cli.add_command(download)
cli.add_command(config)


@cli.command()
def webui() -> None:
    """Launch the web-based user interface."""
    try:
        from civitai_dl.webui.app import create_app

        app = create_app()
        click.echo("Starting WebUI interface, access in your browser...")
        app.launch(server_name="0.0.0.0", server_port=7860)
    except ImportError as e:
        click.echo(f"Failed to start WebUI: {str(e)}", err=True)
        click.echo("Please ensure all necessary dependencies are installed (gradio)", err=True)
        sys.exit(1)


@cli.group()
def browse() -> None:
    """Browse and search models on Civitai."""


# Add commands from browse.py to the browse command group
for command in getattr(browse_commands, 'commands', {}).values():
    browse.add_command(command)


def main() -> None:
    """Main entry point for the CLI application."""
    try:
        cli()
    except Exception as e:
        logger.exception(f"Unhandled error: {str(e)}")
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
