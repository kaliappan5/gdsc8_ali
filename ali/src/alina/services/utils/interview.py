from pathlib import Path

from alina.services.chat.base.interview import BaseInterviewer
from alina.services.chat.base.persona import BasePersonaChatter, Conversation, Role
from alina.services.utils.ai import AIProvider, get_ai_manager
from alina.shared.workspace import Workspace


def summarize(interview_content: str, ai: AIProvider) -> str:
    ai_manager = get_ai_manager(ai)
    agent = ai_manager.build_agent(
        system_prompt="""
        You are an expert at summarizing interview transcripts.
        Given the transcript of an interview, produce a concise summary highlighting the key points that the user gave about themselves.
    """
    )
    agent_result = agent(interview_content)
    message_blocks = agent_result.message.get("content", [])
    return "\n".join(block.get("text", "") for block in message_blocks)


def write_interview(path: Path, conversation: Conversation):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for msg in conversation.messages:
            if msg.role == Role.USER:
                f.write(f"**Assistant:** {msg.content}\n\n")
            else:
                f.write(f"**User:** {msg.content}\n\n")
