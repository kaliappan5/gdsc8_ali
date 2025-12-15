import traceback
from importlib.metadata import version as meta_version

import typer
from rich import print

from alina.services.utils.aws import aws_signed_request
from alina.services.utils.bedrock import get_models
from alina.services.utils.mistral import list_models
from alina.shared.config import Configuration

app = typer.Typer()

configuration = Configuration()


def get_health_status(state: bool) -> str:
    if state:
        return "🟢 [bold green]Healthy[/bold green]"
    return "❌ [bold red]Unhealthy[/bold red]"


def get_aws_status() -> bool:
    try:
        response = aws_signed_request(path="health", method="GET")
        return bool(response) and response.status_code == 200
    except Exception as e:
        print(traceback.format_exc())
        return False


def print_aws_status() -> None:
    print(f"AWS Base URL: [grey]{configuration.AWS_BASE_URL}[/grey]")
    print(f"AWS Status: {get_health_status(get_aws_status())}")


def print_mistral_status() -> None:
    try:
        models = list_models()
        print(f"Mistral Status: {get_health_status(True)}")
        print("Available Mistral Models:")
        for model in sorted(models):
            print(f" - {model}")
    except Exception as e:
        print(f"Mistral Status: {get_health_status(False)}")
        print(f"[red]{e}[/red]")


def print_bedrock_status() -> None:
    if (
        not configuration.BEDROCK_ACCESS_KEY_ID
        or not configuration.BEDROCK_SECRET_ACCESS_KEY
        or not configuration.BEDROCK_REGION
    ):
        print("Amazon Bedrock Status: [cyan]Not Configured[/cyan]")
        return
    try:
        models = get_models()
        print(f"Amazon Bedrock Status: {get_health_status(True)}")
        if configuration.BEDROCK_MODEL_ID in models:
            print(
                f"Selected Bedrock Model ID: [green]{configuration.BEDROCK_MODEL_ID}[/green]"
            )
        else:
            print(
                f"Selected Bedrock Model ID ({configuration.BEDROCK_MODEL_ID}): [red]Not Available[/red]"
            )
            print("Available Bedrock Models:")
            for model in sorted(models):
                print(f" - {model}")

    except Exception as e:
        print(f"Amazon Bedrock Status: {get_health_status(False)}")
        print(f"[red]{e}[/red]")


@app.command()
def status():
    """Get system status."""
    print(f"Alina version: {meta_version('alina')}")
    print()
    print_aws_status()
    print()
    print_mistral_status()
    print()
    print_bedrock_status()
