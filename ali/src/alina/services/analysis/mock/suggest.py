import asyncio
from pathlib import Path

from alina.models.referential import PersonaReferential
from alina.models.suggestion import (
    AwarenessSuggestionResult,
    BaseSuggestionResult,
    JobsAndTrainingsSuggestionResult,
    JobSuggestionResult,
    PredictedItems,
    TrainingsOnlySuggestionResult,
)

from ..base.suggest import BaseSuggestionAnalyzer, BaseSuggestionResult


class MockSuggestionAnalyzer(BaseSuggestionAnalyzer):
    def analyze(
        self, persona: PersonaReferential, interview_content: str
    ) -> BaseSuggestionResult:
        if len(interview_content) % 3 == 0:
            if len(interview_content) % 2 == 0:
                return AwarenessSuggestionResult(persona.id, PredictedItems.INFO)
            return AwarenessSuggestionResult(persona.id, PredictedItems.TOO_YOUNG)
        elif len(interview_content) % 3 == 1:
            trainings = [
                f"tr{(len(interview_content) * i) % 497 + 1}" for i in range(2)
            ]
            return TrainingsOnlySuggestionResult(persona.id, trainings)
        else:
            jobs = [f"j{(len(interview_content) * i) % 200 + 1}" for i in range(3)]
            return JobsAndTrainingsSuggestionResult(
                persona.id,
                [
                    JobSuggestionResult(
                        job_id=job_id,
                        suggested_trainings=[
                            f"tr{(len(interview_content) * i) % 497 + 1}"
                            for i in range(3)
                        ],
                    )
                    for job_id in jobs
                ],
            )
