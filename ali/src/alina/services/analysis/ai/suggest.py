from enum import Enum
from typing import Optional, Sequence

from pydantic import BaseModel, Field
from strands.types.content import ContentBlock, Message

from alina.models.referential import (
    DOMAINS,
    HIGH_LEVEL_DOMAINS,
    SKILL_LEVELS,
    JobReferential,
    PersonaReferential,
    TrainingReferential,
    UserIntent,
)
from alina.models.suggestion import (
    AwarenessSuggestionResult,
    BaseSuggestionResult,
    JobsAndTrainingsSuggestionResult,
    JobSuggestionResult,
    PredictedItems,
    TrainingsOnlySuggestionResult,
)
from alina.services.utils.ai import AIProvider, get_ai_manager

from ..base.suggest import BaseSuggestionAnalyzer, BaseSuggestionResult


def format_level_change(level: int) -> str:
    if level in SKILL_LEVELS and level + 1 in SKILL_LEVELS:
        return (
            f"{SKILL_LEVELS[level]} ({level}) → {SKILL_LEVELS[level + 1]} ({level + 1})"
        )
    return "Unknown"


class AISuggestionAnalyzer(BaseSuggestionAnalyzer):
    def __init__(
        self,
        jobs: Sequence[JobReferential],
        trainings: Sequence[TrainingReferential],
        ai_provider: AIProvider,
    ):
        super().__init__(jobs, trainings)
        ai_manager = get_ai_manager(ai_provider)
        self.agent = ai_manager.build_agent(
            system_prompt="""
            You are an expert career advisor specializing in job and training recommendations.
            You will be provided with information about a person's background, interests, and skill levels.
            Based on this information, you will suggest suitable job opportunities and training programs that align with the person's career goals.
            All people you assist are looking to improve their career prospects and skill sets, and are based in Brazil.
            """
        )

    def analyze(
        self, persona: PersonaReferential, interview_content: str
    ) -> BaseSuggestionResult:
        if persona.age < 16:
            return AwarenessSuggestionResult(persona.id, PredictedItems.TOO_YOUNG)
        if persona.intent == UserIntent.AWARENESS:
            return AwarenessSuggestionResult(persona.id, PredictedItems.INFO)
        elif persona.intent == UserIntent.ONLY_TRAININGS:
            return self._recommend_trainings_only(persona)
        else:
            return self._recommend_jobs_and_trainings(persona)

    def _get_related_domains(self, domain: int | None) -> list[int]:
        if domain is None:
            return list(DOMAINS.keys())
        for domain_group in HIGH_LEVEL_DOMAINS:
            if domain in domain_group:
                return domain_group
        return list(DOMAINS.keys())

    def _recommend_trainings_only(
        self, persona: PersonaReferential
    ) -> TrainingsOnlySuggestionResult:
        related_domains = self._get_related_domains(persona.domain)
        all_training_ids = []
        for related_domain in related_domains:
            filtered_trainings = [
                training
                for training in self.trainings
                if training.domain == related_domain
            ]
            if not filtered_trainings:
                continue

            training_ids = self._get_standalone_learnings(
                persona, filtered_trainings, persona.domain != related_domain
            )
            print(
                f"{len(training_ids)} trainings after filtering by domain and AI recommendation (domain {persona.domain}, but {related_domain} considered)"
            )
            all_training_ids.extend(training_ids)

        # At the end, we are asking again to filter out the result
        all_training_ids = self._get_standalone_learnings(
            persona,
            [
                training
                for training in self.trainings
                if training.id in all_training_ids
            ],
            False,
        )
        print(f"{len(all_training_ids)} trainings after final AI recommendation")
        return TrainingsOnlySuggestionResult(persona.id, all_training_ids)

    def _recommend_jobs_and_trainings(
        self, persona: PersonaReferential
    ) -> JobsAndTrainingsSuggestionResult:
        if persona.city and not persona.willing_to_relocate:
            filtered_jobs = [
                job for job in self.jobs if job.city == persona.city or job.remote
            ]
        else:
            filtered_jobs = self.jobs

        print(len(filtered_jobs), "jobs after filtering by city")
        if not filtered_jobs:
            return JobsAndTrainingsSuggestionResult(persona.id, [])

        education_level = persona.education_level
        if education_level:
            filtered_jobs = [
                job
                for job in filtered_jobs
                if job.education_level is None or job.education_level <= education_level
            ]
            print(
                f"{len(filtered_jobs)} jobs after filtering by city and education level ({education_level})"
            )
            if not filtered_jobs:
                return JobsAndTrainingsSuggestionResult(persona.id, [])

        if persona.job_experience is not None:
            filtered_jobs = [
                job
                for job in filtered_jobs
                if job.experience is None or job.experience <= persona.job_experience
            ]
            print(
                f"{len(filtered_jobs)} jobs after filtering by city, education level, and experience"
            )
            if not filtered_jobs:
                return JobsAndTrainingsSuggestionResult(persona.id, [])

        filtered_jobs = self._get_recommended_jobs(persona, filtered_jobs)
        job_suggestions = []
        for job in filtered_jobs:
            suggested_trainings = self._get_recommended_trainings_for_job(persona, job)
            job_suggestions.append(
                JobSuggestionResult(
                    job_id=job.id, suggested_trainings=[*suggested_trainings]
                )
            )
        return JobsAndTrainingsSuggestionResult(persona.id, job_suggestions)

    def _get_recommended_trainings_for_job(
        self,
        persona: PersonaReferential,
        job: JobReferential,
    ) -> list[str]:
        related_domains = self._get_related_domains(persona.domain)
        filtered_trainings = [
            training
            for training in self.trainings
            if training.domain in related_domains
        ]
        if not filtered_trainings:
            return []

        class LearningsModel(BaseModel):
            recommended_learnings: list[str] = Field(
                [],
                description=f"""
                    List of training IDs from the following that are most applicable to the person's interests and background:
                    {', '.join([f"\"{training.id}\"" for training in filtered_trainings])}
                    Choose the most relevant trainings that would help the person improve their skills and achieve their career goals.
                    If several trainings improve the same skill, choose the most relevant one.
                """,
            )

        trainings_description_prompt = self._describe_trainings(filtered_trainings)
        job_requirement_prompt = ", ".join(
            [
                f"{skill.skill} ({SKILL_LEVELS[skill.level]}, level {skill.level})"
                for skill in job.skills
                if skill.required
            ]
        )
        trainings_prompt = f"""
            Consider the person's interests, background, and skill levels when making your recommendations.
            ---
            Skills that the person has: {persona.current_skills}
            Skills required for the job {job_requirement_prompt}
            Learning interests: {persona.training_description}
            ---
            Available trainings:
            {trainings_description_prompt}
            ---
            IMPORTANT:
            Only recommend trainings that correspond to skills required for the job.
            If the person does not have the required skill level, recommend trainings to help them reach the required level.
            It can be several trainings for the same skill if needed.
            If the person is not interested in any of the trainings, return an empty list.
            Do not include unrelated trainings.
            Do not omit required trainings.
            Keep the list concise and complete.
        """
        learnings_result = self.agent.structured_output(
            output_model=LearningsModel, prompt=trainings_prompt
        )
        return learnings_result.recommended_learnings

    def _get_recommended_jobs(
        self,
        persona: PersonaReferential,
        jobs: Sequence[JobReferential],
    ) -> list[JobReferential]:
        related_domains = self._get_related_domains(persona.domain)
        filtered_jobs = [job for job in jobs if job.domain in related_domains]
        if not filtered_jobs:
            # Fallback to all jobs if none in related domains
            filtered_jobs = jobs

        class JobsModel(BaseModel):
            recommended_jobs: list[str] = Field(
                [],
                description=f"""
                    List of job IDs from the following that are most applicable:
                    {', '.join([f"\"{job.id}\"" for job in filtered_jobs])}
                    Choose the most relevant jobs that would suit the person's career goals.
                """,
            )

        jobs_description_prompt = "\n".join(
            [
                f'- "{job.id}": (Domain {DOMAINS[job.domain]}) {job.description}'
                for job in filtered_jobs
            ]
        )
        jobs_prompt = f"""
            Consider the person's interests, background, and skill levels when making your recommendations.
            ---
            Person's job wishes: {persona.job_description}
            Current skills: {persona.current_skills}
            ---
            Available jobs:
            {jobs_description_prompt}
        """
        jobs_result = self.agent.structured_output(
            output_model=JobsModel, prompt=jobs_prompt
        )
        return [job for job in jobs if job.id in jobs_result.recommended_jobs]

    def _get_standalone_learnings(
        self,
        persona: PersonaReferential,
        trainings: Sequence[TrainingReferential],
        different_domain: bool,
    ) -> list[str]:
        class LearningsModel(BaseModel):
            recommended_learnings: list[str] = Field(
                [],
                description=f"""
                    List of training IDs from the following that are most applicable to the person's interests and background:
                    {', '.join([f"\"{training.id}\"" for training in trainings])}
                    Choose the most relevant trainings that would help the person improve their skills and achieve their career goals.
                """,
            )

        trainings_description_prompt = self._describe_trainings(trainings)
        trainings_prompt = f"""
            ROLE:
            Consider the person's interests, background, and skill levels when making your recommendations.
            ---
            TRAINING REQUEST:
             - Skills that the person has: {persona.current_skills}
             - {"IMPORTANT" if persona.growth_skills else ""} Skills that the person wants to improve: {persona.growth_skills}
             - {"IMPORTANT" if persona.new_skills else ""} Skills that the person wants to acquire: {persona.new_skills}
            - Learning interests: {persona.training_description}
            ---
            AVAILABLE TRAININGS:
            {trainings_description_prompt}
            ---
            SKILL LEVELS:
                {"\n".join(f'"{level}": {name}' for level, name in SKILL_LEVELS.items())}
            ---
            RULES:
            If the person is not interested in any of the trainings, return an empty list.
            Recommend only the next level above the current one.
            If the persona has no prior level, recommend only Básico (level 1) trainings.
            Do not suggest multiple levels at once.
            The person should match the skills required for the training. If they have an higher level, they should not attend the training.
            Skills improved by the training should match the person's growth or new skills.
            {"Trainings are from a different domain than the person's main interest, so be mindful of that." if different_domain else ""}
        """
        learnings_result = self.agent.structured_output(
            output_model=LearningsModel, prompt=trainings_prompt
        )
        return learnings_result.recommended_learnings

    def _describe_training(self, training: TrainingReferential) -> str:
        return "\n".join(
            [
                f'- "{training.id}":',
                f"    Target jobs: {training.target_job}",
                f"    Skills improved by training ({training.level_change}): {training.skills_description}",
            ]
        )

    def _describe_trainings(self, trainings: Sequence[TrainingReferential]) -> str:
        return "\n".join([self._describe_training(training) for training in trainings])
