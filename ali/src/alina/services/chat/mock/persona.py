from random import randint

from rich import print
from rich.prompt import Prompt

from ..base.persona import BasePersonaChatter, Conversation, ConversationMessage, Role


class MockPersonaChatter(BasePersonaChatter):
    def start_conversation(
        self, persona_identifier: int, first_message: str
    ) -> Conversation:
        conversation = Conversation(f"#{persona_identifier}", handler="mock")
        conversation.week_counter = randint(10, 100)
        conversation.messages.append(
            ConversationMessage(role=Role.USER, content=first_message)
        )
        conversation.messages.append(
            ConversationMessage(
                role=Role.PERSONA,
                content=f"Hello! I am a mock persona with ID {persona_identifier}. How can I assist you today?",
            )
        )
        return conversation

    def send_message(self, conversation: Conversation, message: str) -> None:
        conversation.messages.append(
            ConversationMessage(role=Role.USER, content=message)
        )
        response = f"Mock response to your message: '{message}'"
        conversation.messages.append(
            ConversationMessage(role=Role.PERSONA, content=response)
        )


class UserTypingPersonaChatter(BasePersonaChatter):
    def start_conversation(
        self, persona_identifier: int, first_message: str
    ) -> Conversation:
        conversation = Conversation(f"#{persona_identifier}", handler="typing")
        conversation.week_counter = randint(10, 100)
        conversation.messages.append(
            ConversationMessage(role=Role.USER, content=first_message)
        )
        print(f"[green]Assistant:[/green] {first_message}")
        user_reply = Prompt.ask("[cyan]Person[/cyan]")
        conversation.messages.append(
            ConversationMessage(role=Role.PERSONA, content=user_reply)
        )
        return conversation

    def send_message(self, conversation: Conversation, message: str) -> None:
        conversation.messages.append(
            ConversationMessage(role=Role.USER, content=message)
        )
        print(f"[green]Assistant:[/green] {message}")
        user_reply = Prompt.ask("[cyan]Person[/cyan]")
        conversation.messages.append(
            ConversationMessage(role=Role.PERSONA, content=user_reply)
        )
