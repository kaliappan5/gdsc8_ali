from abc import ABC, abstractmethod
from enum import Enum


class Role(Enum):
    PERSONA = "persona"
    USER = "user"


class ConversationMessage:
    role: Role
    content: str

    def __init__(self, role: Role, content: str):
        self.role = role
        self.content = content


class Conversation:
    persona_identifier: str
    handler: str
    messages: list[ConversationMessage]
    week_counter: int | None = None

    def __init__(self, persona_identifier: str, handler: str):
        self.persona_identifier = persona_identifier
        self.handler = handler
        self.messages = []


class BasePersonaChatter(ABC):
    """
    Abstract class for persona chatting services.
    """

    @abstractmethod
    def start_conversation(
        self, persona_identifier: int, first_message: str
    ) -> Conversation:
        pass

    @abstractmethod
    def send_message(self, conversation: Conversation, message: str) -> None:
        pass
