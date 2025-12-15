from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field
from strands.agent import Agent

from alina.models.referential import DOMAINS, SKILL_LEVELS, TrainingReferential
from alina.services.utils.ai import AIManager
from alina.shared.config import Configuration

from ..base.training import BaseTrainingAnalyzer

configuration = Configuration()


class TrainingInfo(BaseModel):
    """Structured description of a training description."""

    city: Optional[str] = Field(
        None,
        description="""
            City where the job is held (can be null if not mentioned).
            Remote is not a city; if the job is fully remote, this field should be null.
            "Brasil" and "Brazil" are not valid cities and should be null as well.
        """,
    )
    online: bool = Field(
        False,
        description="Whether the training can be attended online (False if not mentioned)",
    )
    locale: str = Field(
        "en-US",
        description="Locale of the training (default: en-US)",
    )
    duration_weeks: int = Field(
        0,
        description="Duration of the training in weeks (default: 0)",
    )
    certification: bool = Field(
        False,
        description="Whether the training offers certification (default: False)",
    )
    domain: int = Field(
        0,
        description=f"""
            Domain or field of the training.
            Possible values are:
                {"\n".join(f'"{level}": {value}' for level, value in DOMAINS.items())}
        """,
    )
    skills_description: str = Field(
        "",
        description=f"""
            The skills that this training aims to teach or improve.
            It should be skills relevant to the training content. Avoid generic terms like 'Communication' or 'Management'.
            The level change is already known from another field, so focus on the skills themselves (do not mention the level change).
        """,
    )
    target_job: str = Field(
        "",
        description="""
            The type of job that the training prepares for (e.g. Data Scientist, Web Developer)
            When the job is generic, make sure to include the domain (if mentionned) so that it is clear what kind of job it is.
            For example, in industry sectors, use "Data Analyst in Finance" instead of just "Data Analyst".
        """,
    )


TRAINING_ANALYSIS_SYSTEM_PROMPT = """
    You are given training descriptions for a Brazilian audience.
    Provide concise and accurate information based on the provided description.
    IMPORTANT: Always write your text in English, regardless of the job description language.
"""


class AITrainingAnalyzer(BaseTrainingAnalyzer):
    agent: Agent

    def __init__(self, ai_manager: AIManager):
        super().__init__()
        self.agent = ai_manager.build_agent(TRAINING_ANALYSIS_SYSTEM_PROMPT)

    async def analyze(self, path: Path) -> TrainingReferential:
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()

        training_id = int(path.stem[2:])
        training_level = training_id % 3
        training_level_change = f"{SKILL_LEVELS.get(training_level, "Unknown Level")} ({training_level}) to {SKILL_LEVELS.get(min(training_level + 1, 3), "Unknown Level")} ({training_level+1})"
        training_prompt = f"""
            # Training Metadata
            - This training improves a set of skills from {training_level_change}.
            - You should only list skills that are relevant to this level change, not all skills mentioned in the description.
            
            # Training Description
            {content}
        """
        training_info = await self.agent.structured_output_async(
            output_model=TrainingInfo, prompt=training_prompt
        )
        return TrainingReferential(
            id=path.stem,
            **training_info.model_dump(),
            level_change=training_level_change,
        )
