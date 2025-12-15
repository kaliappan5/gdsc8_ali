from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field
from strands.agent import Agent

from alina.models.referential import (
    DOMAINS,
    EDUCATION_LEVELS,
    SKILL_LEVELS,
    JobReferential,
    JobSkillRequirementLevel,
)
from alina.services.utils.ai import AIManager
from alina.shared.config import Configuration

from ..base.job import BaseJobAnalyzer

configuration = Configuration()


class JobSkillRequirementLevelInfo(BaseModel):
    skill: str = Field(
        "",
        description="""
            A skill that the job requires, in English (e.g. Programming, Data Analysis).
            It should be a specific skill relevant to the job content. Avoid generic terms like 'Communication' or 'Management'.
            Each job may require multiple skills, so accuracy is important.
        """,
    )
    level: int = Field(
        1,
        description=f"""
            The required skill level for the job.
            Possible values are:
                {"\n".join(f'"{level}": {name}' for level, name in SKILL_LEVELS.items() if level > 0)}
        """,
    )
    required: bool = Field(
        True,
        description="Whether the skill is required (True) or just desired (False) for the job",
    )


class JobInfo(BaseModel):
    """Structured description of a job description."""

    city: Optional[str] = Field(
        None,
        description="""
            City where the job is located (can be null if not mentioned).
            Remote is not a city; if the job is fully remote, this field should be null.
            "Brasil" and "Brazil" are not valid cities and should be null as well.
        """,
    )
    remote: bool = Field(
        False,
        description="Whether the job can be attended remotely (False if not mentioned)",
    )
    domain: int = Field(
        0,
        description=f"""
            Domain or field of the job.
            Possible values are:
                {"\n".join(f'"{level}": {value}' for level, value in DOMAINS.items())}
        """,
    )
    education_level: Optional[int] = Field(
        None,
        description=f"""
            Brazilian education level associated with the job (from 1 to 12), can be null if not mentioned
            Possible values are:
                {"\n".join(f'"{level}": {name}' for level, name in EDUCATION_LEVELS.items())}
        """,
    )
    languages: list[str] = Field(
        [],
        description="List of required languages as 2-letter ISO code for the job (empty if not mentioned)",
    )
    experience: int = Field(
        0,
        description="Required experience in years for the job (default: 0 if not mentioned)",
    )
    description: str = Field(
        "",
        description="Short description of the job (main responsibilities and tasks).",
    )
    skills: list[JobSkillRequirementLevelInfo] = Field(
        [],
        description="""
            List of expected skills for the job with their required levels.
            Each skill should be specific and relevant to the job content. Avoid generic terms.
        """,
    )


JOB_ANALYSIS_SYSTEM_PROMPT = f"""
    You are given job descriptions for a Brazilian job board.
    Provide concise and accurate information based on the provided description.
    IMPORTANT: Always write your text in English, regardless of the job description language.
"""


class AIJobAnalyzer(BaseJobAnalyzer):
    agent: Agent

    def __init__(self, ai_manager: AIManager):
        super().__init__()
        self.agent = ai_manager.build_agent(JOB_ANALYSIS_SYSTEM_PROMPT)

    async def analyze(self, path: Path) -> JobReferential:
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()
        job_info = await self.agent.structured_output_async(
            output_model=JobInfo, prompt=content
        )
        return JobReferential(
            id=path.stem,
            city=job_info.city,
            remote=job_info.remote,
            domain=job_info.domain,
            education_level=job_info.education_level,
            languages=job_info.languages,
            experience=job_info.experience,
            skills=[
                JobSkillRequirementLevel(**skill.model_dump())
                for skill in job_info.skills
            ],
            description=job_info.description,
        )
