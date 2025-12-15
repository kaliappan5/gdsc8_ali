import typer
from rich import print
from typing_extensions import Annotated, Optional

from alina.services.chat.ai.interview import InitialAIInterviewer
from alina.services.chat.ai.persona import AIPersonaChatter
from alina.services.chat.base.interview import BaseInterviewer
from alina.services.chat.base.persona import BasePersonaChatter, Role
from alina.services.chat.mock.interview import MockInterviewer
from alina.services.chat.mock.persona import MockPersonaChatter
from alina.services.utils.ai import AIProvider
from alina.services.utils.persona_range import PersonaRange, parse_persona_range
from alina.shared.workspace import Workspace

app = typer.Typer()


def interview_persona(
    persona_chatter: BasePersonaChatter, interviewer: BaseInterviewer, persona_id: int
) -> None:
    print(f"Interviewing persona #{persona_id}")
    interview_details = interviewer.start_conversation()
    conversation = persona_chatter.start_conversation(
        persona_identifier=persona_id, first_message=interview_details.next_message
    )
    while conversation and len(conversation.messages) < 20:
        print(f" {len(conversation.messages) // 2} messages exchanged...")
        interview_details = interviewer.send_message(conversation.messages[-1].content)
        persona_chatter.send_message(conversation, interview_details.next_message)

    if conversation:
        print(f"Interview with persona #{persona_id} completed.")
        conversation_file_path = Workspace().get_interview_file(persona_id)
        conversation_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(conversation_file_path, "w", encoding="utf-8") as f:
            for msg in conversation.messages:
                if msg.role == Role.USER:
                    f.write(f"**Assistant:** {msg.content}\n\n")
                else:
                    f.write(f"**User:** {msg.content}\n\n")


@app.command()
def interview(
    persona: Annotated[
        PersonaRange, typer.Option("--persona", parser=parse_persona_range)
    ],
    ai: Optional[Annotated[AIProvider, typer.Option("--ai")]] = None,
):
    if persona.min_id < persona.max_id:
        print(f"Starting interview of personas #{persona.min_id} to #{persona.max_id}")

    for pid in persona.range():
        if ai:
            personna_chatter = AIPersonaChatter()
            interviewer = InitialAIInterviewer(ai)
        else:
            personna_chatter = MockPersonaChatter()
            interviewer = MockInterviewer()
        interview_persona(personna_chatter, interviewer, pid)
