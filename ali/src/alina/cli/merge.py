import json

import typer
from typing_extensions import Annotated

from alina.shared.database import save_suggestions
from alina.shared.workspace import Workspace

app = typer.Typer()


@app.command()
def merge(
    jobs_submission: Annotated[int, typer.Option("--jobs")],
    trainings_submission: Annotated[int, typer.Option("--trainings")],
):
    """Merge two submissions into one (one for jobs, one for trainings)."""

    workspace = Workspace()
    job_submission = workspace.get_submission_file(jobs_submission)
    training_submission = workspace.get_submission_file(trainings_submission)
    if not job_submission.exists():
        print(f"Job submission file {job_submission} does not exist.")
        return
    if not training_submission.exists():
        print(f"Training submission file {training_submission} does not exist.")
        return
    with open(job_submission, "r", encoding="utf-8") as f:
        job_data = json.load(f)

    training_dict = {}
    with open(training_submission, "r", encoding="utf-8") as f:
        for entry in json.load(f):
            persona_id = entry["persona_id"]
            training_dict[persona_id] = entry

    merged_results = []
    for job_entry in job_data:
        persona_id = job_entry["persona_id"]
        predicted_type = job_entry["predicted_type"]
        if predicted_type == "awareness" or predicted_type == "jobs+trainings":
            merged_results.append(job_entry)
        elif predicted_type == "trainings_only":
            if persona_id in training_dict:
                merged_results.append(training_dict[persona_id])
            else:
                print(
                    f"Warning: No training data found for persona_id {persona_id}, skipping."
                )
    save_suggestions(merged_results)
