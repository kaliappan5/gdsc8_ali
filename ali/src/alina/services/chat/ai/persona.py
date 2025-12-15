import logging
from typing import Optional

from ...utils.aws import aws_signed_request
from ..base.persona import BasePersonaChatter, Conversation, ConversationMessage, Role


class ChatResponse:
    response: str
    conversation_id: str
    conversation_count_week: int

    def __init__(
        self, response: str, conversation_id: str, conversation_count_week: int
    ):
        self.response = response
        self.conversation_id = conversation_id
        self.conversation_count_week = conversation_count_week


def send_chat_message(
    persona_id: str,
    message: str,
    conversation_id: str | None = None,
) -> Optional[ChatResponse]:
    """Send a message to a persona and return (response_text, conversation_id).
    Returns None on failure.
    """
    payload = {
        "persona_id": persona_id,
        "message": message,
        "conversation_id": conversation_id,
    }
    try:
        resp = aws_signed_request(
            path="chat",
            method="POST",
            payload=payload,
        )
        if not resp:
            return None
        data = resp.json()
        for key in ["response", "conversation_id", "conversation_count_week"]:
            if key not in data:
                raise RuntimeError(f"Chat response missing key '{key}'")
        return ChatResponse(
            response=data["response"],
            conversation_id=data["conversation_id"],
            conversation_count_week=data["conversation_count_week"],
        )
    except Exception as e:
        logging.error(f"Error sending chat message to persona: {e}")
        return None


class AIPersonaChatter(BasePersonaChatter):
    def start_conversation(
        self, persona_identifier: int, first_message: str
    ) -> Conversation:
        persona_id_string = f"persona_{persona_identifier:03d}"
        response_tuple = send_chat_message(
            persona_id=persona_id_string,
            message=first_message,
            conversation_id=None,
        )
        if not response_tuple:
            raise RuntimeError("Failed to start conversation with persona")
        conversation = Conversation(
            persona_id_string, handler=response_tuple.conversation_id
        )
        conversation.messages.append(
            ConversationMessage(role=Role.USER, content=first_message)
        )
        conversation.messages.append(
            ConversationMessage(
                role=Role.PERSONA,
                content=response_tuple.response,
            )
        )
        return conversation

    def send_message(self, conversation: Conversation, message: str) -> None:
        conversation.messages.append(
            ConversationMessage(role=Role.USER, content=message)
        )
        response_tuple = send_chat_message(
            persona_id=conversation.persona_identifier,
            message=message,
            conversation_id=conversation.handler,
        )

        if not response_tuple:
            raise RuntimeError("Failed to send message to persona")

        conversation.messages.append(
            ConversationMessage(
                role=Role.PERSONA,
                content=response_tuple.response,
            )
        )
