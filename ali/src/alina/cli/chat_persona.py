import logging

import typer
from rich import print
from typing_extensions import Annotated

from alina.services.chat.ai.persona import AIPersonaChatter
from alina.services.chat.mock.persona import MockPersonaChatter

app = typer.Typer()


@app.command()
def chat_persona(
    identifier: int,
    ai: Annotated[bool, typer.Option("--ai")] = False,
):
    """Chat with personas based on the given identifier."""
    logging.info(f"Chat initiated with identifier: {identifier}")

    chatter = AIPersonaChatter() if ai else MockPersonaChatter()

    conversation = None
    while True:
        print("[bold cyan][i]You:[/i][/bold cyan] ", end="")
        user_message = input()
        if not user_message.strip():
            break
        if conversation is None:
            conversation = chatter.start_conversation(
                identifier, first_message=user_message
            )
        else:
            chatter.send_message(conversation, user_message)
        last_message = conversation.messages[-1].content
        print(f"[bold magenta][i]Persona:[/i][/bold magenta] {last_message}")
