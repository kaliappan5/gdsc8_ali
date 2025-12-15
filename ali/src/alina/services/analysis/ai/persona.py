from pathlib import Path
from typing import Optional, Sequence, Tuple

from pydantic import BaseModel, Field
from strands.types.content import ContentBlock, Message

from alina.models.referential import (
    DOMAINS,
    EDUCATION_LEVELS,
    SKILL_LEVELS,
    JobReferential,
    ManualUserIntent,
    PersonaReferential,
    TrainingReferential,
    UserIntent,
)
from alina.services.utils.ai import AIProvider, get_ai_manager
from alina.shared.database import read_jobs_analysis, read_trainings_analysis

from ..base.persona import BasePersonaAnalyzer


class AIPersonaAnalyzer(BasePersonaAnalyzer):
    jobs: Sequence[JobReferential]
    trainings: Sequence[TrainingReferential]

    def __init__(self, ai_provider: AIProvider):
        super().__init__()
        ai_manager = get_ai_manager(ai_provider)
        self.agent = ai_manager.build_agent(
            system_prompt="""
            You are an expert career advisor, specializing in understanding personas based on interview data.
            Given the interview data, your task is to extract relevant information about the persona, focusing on accuracy.
            Do not make assumptions beyond the provided data.
            """
        )
        self.jobs = read_jobs_analysis()
        self.trainings = read_trainings_analysis()

    async def analyze(
        self, id: str, paths: list[Path], manual_intent: Optional[ManualUserIntent]
    ) -> PersonaReferential:
        interview_content = ""
        for path in paths:
            with open(path, "r", encoding="utf-8") as file:
                interview_content += file.read()
                interview_content += "\n\n"
        self.agent.messages.append(
            Message(
                role="user",
                content=[
                    ContentBlock(text="Interview content:"),
                    ContentBlock(text=interview_content),
                ],
            )
        )

        if manual_intent:
            # We do not care for accuracy, just trying to flag too young personas
            if manual_intent == ManualUserIntent.AWARENESS_TOO_YOUNG:
                age = 15
                intent = UserIntent.AWARENESS
            else:
                age = 21
                if manual_intent == ManualUserIntent.AWARENESS_INFO:
                    intent = UserIntent.AWARENESS
                elif manual_intent == ManualUserIntent.JOBS_AND_TRAININGS:
                    intent = UserIntent.JOBS_AND_TRAININGS
                else:  # manual_intent == ManualUserIntent.TRAININGS_ONLY
                    intent = UserIntent.ONLY_TRAININGS
        else:
            age = self._get_age()
            intent = self._get_intent()

        if age < 16:
            # No persona analysis for minors
            return PersonaReferential(id=id, age=age)

        if intent == UserIntent.AWARENESS:
            # For awareness-only personas, we do not need to move further
            return PersonaReferential(id=id, age=age, intent=intent)

        city, willing_to_relocate = self._get_city_constraint()
        education_level = self._get_education_level()
        domain = self._get_domain(intent)

        if intent == UserIntent.JOBS_AND_TRAININGS:
            job_experience, job_description, current_skills, training_description = (
                self._get_job_description()
            )
            growth_skills = None
            new_skills = None
        else:  # intent == UserIntent.ONLY_TRAININGS
            job_description = None
            job_experience = None
            current_skills, growth_skills, new_skills, training_description = (
                self._get_training_description()
            )

        return PersonaReferential(
            id=id,
            age=age,
            intent=intent,
            city=city,
            willing_to_relocate=willing_to_relocate,
            education_level=education_level,
            domain=domain,
            job_experience=job_experience,
            job_description=job_description,
            training_description=training_description,
            current_skills=current_skills,
            growth_skills=growth_skills,
            new_skills=new_skills,
        )

    def _get_age(self) -> int:
        class AgeModel(BaseModel):
            age: int = Field(0, description="The age of the person in years.")

        age_result = self.agent.structured_output(output_model=AgeModel)
        return age_result.age

    def _get_intent(self) -> UserIntent:
        class IntentModel(BaseModel):
            intent: UserIntent = Field(
                UserIntent.AWARENESS,
                description="""
                    Get user intent based on interview content.
                    Personas may seek trainings either as a standalone goal (ONLY_TRAININGS) or as preparation for a job (JOBS_AND_TRAININGS).
                    Possible values are:
                    - JOBS_AND_TRAININGS: wants job suggestions (and usually trainings too)
                    - ONLY_TRAININGS: wants only training suggestions (not jobs)
                    - AWARENESS: learn about career options without specific job/training suggestions
                    If the person is vague, unsure, or just exploring, choose AWARENESS.
                """,
            )

        awareness_result = self.agent.structured_output(output_model=IntentModel)
        return awareness_result.intent

    def _get_city_constraint(self) -> Tuple[Optional[str], bool]:
        possible_cities = ", ".join(sorted({job.city for job in self.jobs if job.city}))

        class CityModel(BaseModel):
            city: Optional[str] = Field(
                None,
                description=f"""
                    The city where the person wants to find jobs.
                    If no city is mentioned, return null.
                    Choose from the following possible cities: {possible_cities}
                """,
            )
            willing_to_relocate: bool = Field(
                False,
                description="""
                    Whether the person is willing to relocate for a job.
                    Return true or false.
                """,
            )

        city_result = self.agent.structured_output(output_model=CityModel)
        return city_result.city, city_result.willing_to_relocate

    def _get_education_level(self) -> Optional[int]:
        class EducationModel(BaseModel):
            education_level: Optional[int] = Field(
                None,
                description=f"""
                    The highest education level attained by the person.
                    Possible values are:
                        {"\n".join(f'"{level}": {value}' for level, value in EDUCATION_LEVELS.items())}
                    If no education level is mentioned, return null.
                """,
            )

        education_result = self.agent.structured_output(output_model=EducationModel)
        return education_result.education_level

    def _get_domain(self, intent: UserIntent) -> Optional[int]:
        class DomainModel(BaseModel):
            domain: Optional[int] = Field(
                None,
                description=f"""
                    The domain of expertise or interest of the person, i.e. their professional field.
                    If this person wants to explore jobs, it is in this domain.
                    If this person is looking for trainings, it is to build skills in this domain.
                    Possible values are:
                        {"\n".join(f'"{level}": {value}' for level, value in DOMAINS.items())}
                    If no domain is mentioned, return null.
                    If several domains are mentioned, return the most relevant one.
                """,
            )

        if intent == UserIntent.JOBS_AND_TRAININGS:
            intent_prompt = "Based on our information, this person is looking for jobs (and possibly for trainings)"
        else:
            intent_prompt = (
                "Based on our information, this person is looking only for trainings"
            )
        domain_result = self.agent.structured_output(
            output_model=DomainModel, prompt=intent_prompt
        )
        return domain_result.domain

    def _get_training_description(
        self,
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        class TrainingDescriptionModel(BaseModel):
            current_skills: Optional[str] = Field(
                None,
                description=f"""
                    Provide a list of the person's current skills relevant to trainings, based on the interview content.
                    The level in each skill should be inferred from the interview, but do not invent skills not mentioned.
                    Skill levels are: {",".join(f'{value} ({level})' for level, value in SKILL_LEVELS.items() if level > 0)})
                    If the person does not mention any current skills, return null.
                """,
            )
            growth_skills: Optional[str] = Field(
                None,
                description=f"""
                    Provide a list of the person's target skills they wish to develop through trainings, based on the interview content.
                    We assume that the person wants to go from one level to the next in each skill they wish to develop.
                    You should only mention skills that the person already have at least at level 1.
                    If the person does not mention any skills to grow, return null.
                """,
            )
            new_skills: Optional[str] = Field(
                None,
                description=f"""
                    Provide a list of the new skills the person wishes to acquire through trainings, based on the interview content.
                    These are skills that the person does not currently possess.
                    This attribute is separate from 'growth_skills' which focuses on improving existing skills.
                    If the person does not mention any new skills, return null.
                """,
            )
            training_description: Optional[str] = Field(
                None,
                description="""
                    If this person mentions any trainings they are interested in as part of their search, provide a brief description.
                """,
            )

        training_result = self.agent.structured_output(
            output_model=TrainingDescriptionModel,
            prompt="""
                Other persona attributes (name, age, city, willing to relocate...) have already been extracted.
                We already know this person is looking only for trainings, not for jobs.
                Focus only on extracting the trainings description and current skills from the interview content.
                IMPORTANT: Always write your text in English, regardless of the interview language.
                IMPORTANT: Do not say "the interview...", just respond with the extracted information.
            """,
        )
        return (
            training_result.current_skills,
            training_result.growth_skills,
            training_result.new_skills,
            training_result.training_description,
        )

    def _get_job_description(
        self,
    ) -> Tuple[Optional[int], Optional[str], Optional[str], Optional[str]]:
        class JobDescriptionModel(BaseModel):
            experience_years: Optional[int] = Field(
                None,
                description="""
                    The number of years of professional experience the person has.
                    If no experience is mentioned, return null.
                """,
            )
            current_skills: Optional[str] = Field(
                None,
                description=f"""
                    Provide a list of the person's current skills relevant to jobs, based on the interview content.
                    The level in each skill should be inferred from the interview, but do not invent skills not mentioned.
                    Skill levels are: {",".join(f'{value} ({level})' for level, value in SKILL_LEVELS.items() if level > 0)})
                    If the person does not mention any current skills, return null.
                """,
            )
            description: Optional[str] = Field(
                None,
                description="""
                    Provide a brief description of the person's job preferences and aspirations based on the interview content.
                    This should include the types of roles they are interested in.
                    If the person does not mention any job preferences, return null.
                """,
            )
            training_description: Optional[str] = Field(
                None,
                description="""
                    If this person mentions any trainings they are interested in as part of their job search, provide a brief description.
                    Do not include this information in the 'description' field.
                    If no trainings are mentioned, return null.
                """,
            )

        job_result = self.agent.structured_output(
            output_model=JobDescriptionModel,
            prompt="""
                Other persona attributes (name, age, city, willing to relocate...) have already been extracted.
                We alrady know this person is looking for jobs (and possibly trainings).
                Focus only on extracting the job description and current skills from the interview content.
                IMPORTANT: Always write your text in English, regardless of the interview language.  
                IMPORTANT: Do not say "the interview...", just respond with the extracted information.
            """,
        )
        return (
            job_result.experience_years,
            job_result.description,
            job_result.current_skills,
            job_result.training_description,
        )
