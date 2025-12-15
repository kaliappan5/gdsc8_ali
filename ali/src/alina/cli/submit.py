import typer
from rich import print

from alina.services.utils.submission import make_submission, validate_submission_format
from alina.shared.database import read_last_suggestions, save_submission
from alina.shared.workspace import Workspace

app = typer.Typer()
workspace = Workspace()


@app.command()
def submit():
    """Submit the last computed suggestions for each persona."""
    suggestions = read_last_suggestions()

    submission_content = [s.to_dict() for s in suggestions]
    try:
        validate_submission_format(submission_content)
    except ValueError as e:
        typer.echo(f"❌ Submission format validation failed: {e}")
        raise typer.Exit(code=1)

    response = make_submission(submission_content)
    if response.success:
        print("✅ [bold green]Submission succeeded![/bold green]")
        if response.id:
            print(f"🆔 Submission ID: {response.id}")
        if response.message:
            print(f"💬 Message: {response.message}")
        if response.submission_count:
            print(f"📊 Total submissions: {response.submission_count}")
        save_submission(submission_content)
    else:
        print(f"❌ [bold red]Submission failed:[/bold red] {response.message}")
