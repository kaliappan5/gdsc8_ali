import json
import logging

import typer
from pydantic import BaseModel, Field
from strands.types.content import ContentBlock, Message

from alina.services.utils import ai
from alina.shared.workspace import Workspace

app = typer.Typer()


@app.command()
def experiment():
    workspace = Workspace()

    source_file = workspace.get_submission_file(108)
    with open(source_file, "r", encoding="utf-8") as file:
        suggestions = json.load(file)

    for suggestion in suggestions:
        persona_id_string = suggestion["persona_id"]
        persona_id = int(persona_id_string.split("_")[1])
        if suggestion["predicted_type"] == "trainings_only":
            training_ids = [int(tid[2:]) for tid in suggestion["trainings"]]
            for training_id in training_ids:
                if (
                    training_id + 3 not in training_ids
                    and training_id + 6 in training_ids
                ):
                    logging.info(
                        f"Suggestion for persona {persona_id} seems to miss tr{training_id + 3}"
                    )
