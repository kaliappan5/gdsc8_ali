import typer
from rich import print
from rich.prompt import Confirm
from typing_extensions import Annotated, Optional

from alina.services.chat.ai.interview import FullAIInterviewer
from alina.services.chat.ai.persona import AIPersonaChatter
from alina.services.chat.base.interview import BaseInterviewer
from alina.services.chat.base.persona import BasePersonaChatter, Role
from alina.services.chat.mock.persona import UserTypingPersonaChatter
from alina.services.utils.ai import AIProvider
from alina.shared.workspace import Workspace

app = typer.Typer()


def interview_persona(
    persona_chatter: BasePersonaChatter,
    interviewer: BaseInterviewer,
    live: bool,
    persona_id: int,
) -> None:
    print(f"Interviewing persona #{persona_id}")
    interview_details = interviewer.start_conversation()
    conversation = persona_chatter.start_conversation(
        persona_identifier=persona_id, first_message=interview_details.next_message
    )
    print(f"> Started conversation with persona #{persona_id}")
    print(f"> Conversation id: {conversation.handler}")
    if live:
        print(f"[green]Assistant:[/green] {interview_details.next_message}")
    while conversation and len(conversation.messages) < 20:
        interview_details = interviewer.send_message(conversation.messages[-1].content)
        if live:
            print(f"[cyan]Person:[/cyan] {conversation.messages[-1].content}")
            user_confirm = Confirm.ask(
                "Should we continue the interview?", default=True
            )
            if not user_confirm:
                break
        persona_chatter.send_message(conversation, interview_details.next_message)
        if live:
            print(f"\n[green]Assistant:[/green] {interview_details.next_message}")

    if conversation:
        print(f"> Interview with persona #{persona_id} completed.")
        conversation_file_path = Workspace().get_interview_full_file(persona_id)
        conversation_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(conversation_file_path, "w", encoding="utf-8") as f:
            for msg in conversation.messages:
                if msg.role == Role.USER:
                    f.write(f"**Assistant:** {msg.content}\n\n")
                else:
                    f.write(f"**User:** {msg.content}\n\n")


@app.command()
def interview_full(
    persona: Annotated[int, typer.Option("--persona")],
    ai: Annotated[AIProvider, typer.Option("--ai")],
    live: Annotated[bool, typer.Option("--live")] = False,
):
    interviewer = FullAIInterviewer(ai)
    if live:
        personna_chatter = AIPersonaChatter()
    else:
        personna_chatter = UserTypingPersonaChatter()
    interview_persona(personna_chatter, interviewer, live, persona)
