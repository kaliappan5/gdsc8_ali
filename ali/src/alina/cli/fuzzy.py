import json
import random

import typer
from typing_extensions import Annotated

from alina.shared.database import save_suggestions
from alina.shared.workspace import Workspace

app = typer.Typer()

LIMIT_OF_TRAININGS = 4
LIMIT_OF_JOBS = 20
LIMIT_OF_TRAININGS_PER_JOB = 30


@app.command()
def fuzzy(
    submission_id: Annotated[int, typer.Option("--submission")],
    seed: Annotated[str, typer.Option("--seed")],
):
    random.seed(seed)
    workspace = Workspace()
    submission_file = workspace.get_submission_file(submission_id)
    with open(submission_file, "r", encoding="utf-8") as file:
        suggestions = json.load(file)

    for suggestion in suggestions:
        if suggestion["predicted_type"] == "trainings_only":
            if len(suggestion["trainings"]) > LIMIT_OF_TRAININGS:
                suggestion["trainings"] = random.sample(
                    suggestion["trainings"], LIMIT_OF_TRAININGS
                )
        elif suggestion["predicted_type"] == "jobs+trainings":
            if len(suggestion["jobs"]) > LIMIT_OF_JOBS:
                suggestion["jobs"] = random.sample(suggestion["jobs"], LIMIT_OF_JOBS)
                for job in suggestion["jobs"]:
                    if (
                        len(job.get("suggested_trainings", []))
                        > LIMIT_OF_TRAININGS_PER_JOB
                    ):
                        job["suggested_trainings"] = random.sample(
                            job["suggested_trainings"], LIMIT_OF_TRAININGS_PER_JOB
                        )

    save_suggestions(suggestions)
