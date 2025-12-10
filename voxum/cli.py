"""Typer CLI commands for Voxum."""

import logging
import sys
from pathlib import Path

import typer

from voxum import __version__
from voxum.config import get_config, ConfigError
from voxum.orchestrator import Orchestrator
from voxum.tools import drive
from voxum.watcher import start_watcher

app = typer.Typer(
    name="voxum",
    help="Voice meeting summarizer - transcribe, summarize, and deliver",
    no_args_is_help=True,
)


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the CLI."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )


@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
) -> None:
    """Voxum - Voice meeting summarizer CLI."""
    setup_logging(verbose)


@app.command()
def version() -> None:
    """Show version information."""
    typer.echo(f"Voxum v{__version__}")


@app.command()
def auth() -> None:
    """Authenticate with Google Drive (OAuth flow)."""
    typer.echo("Starting Google OAuth flow...")
    typer.echo("A browser window will open for authentication.")

    try:
        creds = drive.authenticate()
        typer.echo(typer.style("Authentication successful!", fg=typer.colors.GREEN))
        typer.echo(f"Token saved to: {drive.TOKEN_FILE}")
    except Exception as e:
        typer.echo(typer.style(f"Authentication failed: {e}", fg=typer.colors.RED))
        raise typer.Exit(1)


@app.command()
def config() -> None:
    """Show current configuration."""
    try:
        cfg = get_config()
        typer.echo("Current configuration:")
        typer.echo(f"  Google Drive Folder: {cfg.google_drive_folder_id}")
        typer.echo(f"  Client Secrets: {cfg.google_client_secrets_path}")
        typer.echo(f"  Transcription Model: {cfg.transcription_model}")
        typer.echo(f"  Summarization Model: {cfg.summarization_model}")
        typer.echo(f"  Summary Language: {cfg.summary_language}")
        typer.echo(f"  Poll Interval: {cfg.poll_interval_seconds}s")
        typer.echo(f"  Email To: {cfg.email_to}")
        typer.echo(f"  Email From: {cfg.email_from}")
    except ConfigError as e:
        typer.echo(typer.style(f"Configuration error:\n{e}", fg=typer.colors.RED))
        raise typer.Exit(1)


@app.command()
def process(
    file: Path = typer.Argument(..., help="Path to audio file to process"),
) -> None:
    """Process a local audio file through the pipeline."""
    if not file.exists():
        typer.echo(typer.style(f"File not found: {file}", fg=typer.colors.RED))
        raise typer.Exit(1)

    try:
        get_config()
    except ConfigError as e:
        typer.echo(typer.style(f"Configuration error:\n{e}", fg=typer.colors.RED))
        raise typer.Exit(1)

    typer.echo(f"Processing: {file.name}")

    orchestrator = Orchestrator()
    result = orchestrator.process_file(file)

    if result.success:
        typer.echo(typer.style("Processing complete!", fg=typer.colors.GREEN))
        if result.delivery_output:
            typer.echo(f"  Summary file: {result.delivery_output.summary_filename}")
            if result.delivery_output.drive_file_id:
                typer.echo(f"  Drive file ID: {result.delivery_output.drive_file_id}")
            if result.delivery_output.email_id:
                typer.echo(f"  Email sent: {result.delivery_output.email_id}")
    else:
        typer.echo(typer.style(f"Processing failed: {result.error}", fg=typer.colors.RED))
        raise typer.Exit(1)


@app.command()
def watch() -> None:
    """Start watching Google Drive folder for new audio files."""
    try:
        cfg = get_config()
    except ConfigError as e:
        typer.echo(typer.style(f"Configuration error:\n{e}", fg=typer.colors.RED))
        raise typer.Exit(1)

    typer.echo(f"Starting watcher for folder: {cfg.google_drive_folder_id}")
    typer.echo(f"Poll interval: {cfg.poll_interval_seconds}s")
    typer.echo("Press Ctrl+C to stop.")

    try:
        start_watcher()
    except KeyboardInterrupt:
        typer.echo("\nStopping watcher...")
        raise typer.Exit(0)


if __name__ == "__main__":
    app()
