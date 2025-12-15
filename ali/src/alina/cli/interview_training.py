from pprint import pprint

import typer
from rich import print
from typing_extensions import Annotated

from alina.models.referential import ManualUserIntent
from alina.services.chat.ai.interview import TrainingAIInterviewer
from alina.services.chat.ai.persona import AIPersonaChatter
from alina.services.utils.ai import AIProvider
from alina.services.utils.interview import summarize, write_interview
from alina.shared.database import read_manual_intents
from alina.shared.workspace import Workspace

app = typer.Typer()


@app.command()
def interview_training(
    ai: Annotated[AIProvider, typer.Option("--ai")],
):
    manual_intents = read_manual_intents()
    workspace = Workspace()
    for persona_id_string, manual_user_intent in manual_intents.items():
        if manual_user_intent != ManualUserIntent.TRAININGS_ONLY:
            continue
        persona_id = int(persona_id_string.split("_")[1])
        conversation_file_path = workspace.get_interview_training_file(persona_id)
        if conversation_file_path.exists():
            print(
                f"Training interview for persona #{persona_id} already exists, skipping"
            )
            continue
        print(f"Interview of persona #{persona_id}")

        # First, we need to do a summary of the previous interview
        previous_interview = workspace.get_interview_file(persona_id)

        if previous_interview.exists():
            with open(previous_interview, "r", encoding="utf-8") as f:
                previous_interview_content = f.read()
        else:
            print(f"No previous interview found for persona #{persona_id}, skipping")
            continue

        previous_interview_summary = summarize(previous_interview_content, ai)

        training_interviewer = TrainingAIInterviewer(
            ai_provider=ai, summary=previous_interview_summary
        )
        persona_chatter = AIPersonaChatter()
        interview_details = training_interviewer.start_conversation()
        conversation = persona_chatter.start_conversation(
            persona_identifier=persona_id, first_message=interview_details.next_message
        )
        while conversation and len(conversation.messages) < 20:
            print(f" {len(conversation.messages) // 2} messages exchanged...")
            interview_details = training_interviewer.send_message(
                conversation.messages[-1].content
            )
            persona_chatter.send_message(conversation, interview_details.next_message)

        print(f"Interview with persona #{persona_id} completed.")
        write_interview(conversation_file_path, conversation)
