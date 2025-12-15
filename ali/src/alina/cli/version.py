from importlib.metadata import version as meta_version

import typer

app = typer.Typer()


@app.command()
def version():
    """Show the version of the application."""
    typer.echo(f"Alina version {meta_version('alina')}")
