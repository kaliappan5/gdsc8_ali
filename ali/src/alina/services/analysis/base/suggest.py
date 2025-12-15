from abc import ABC, abstractmethod
from typing import Sequence

from alina.models.referential import (
    JobReferential,
    PersonaReferential,
    TrainingReferential,
)
from alina.models.suggestion import BaseSuggestionResult


class BaseSuggestionAnalyzer(ABC):
    """
    Abstract class for suggesting jobs and trainings based on analysis.
    """

    jobs: Sequence[JobReferential]
    trainings: Sequence[TrainingReferential]

    def __init__(
        self, jobs: Sequence[JobReferential], trainings: Sequence[TrainingReferential]
    ):
        self.jobs = jobs
        self.trainings = trainings

    @abstractmethod
    def analyze(
        self, persona: PersonaReferential, interview_content: str
    ) -> BaseSuggestionResult:
        pass
