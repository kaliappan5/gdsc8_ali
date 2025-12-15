from abc import ABC
from typing import Optional


class PredictionType(str):
    AWARENESS = "awareness"
    JOBS_AND_TRAININGS = "jobs+trainings"
    TRAININGS_ONLY = "trainings_only"


class PredictedItems(str):
    TOO_YOUNG = "too_young"
    INFO = "info"


class BaseSuggestionResult(ABC):
    persona_id: str
    predicted_type: str

    def __init__(self, persona_id: str, predicted_type: str):
        self.persona_id = persona_id
        self.predicted_type = predicted_type

    def to_dict(self) -> dict:
        return {
            "persona_id": self.persona_id,
            "predicted_type": self.predicted_type,
        }


class AwarenessSuggestionResult(BaseSuggestionResult):
    predicted_items: str

    def __init__(self, persona_id: str, predicted_items: str):
        super().__init__(persona_id, predicted_type=PredictionType.AWARENESS)
        self.predicted_items = predicted_items

    def to_dict(self) -> dict:
        base_dict = super().to_dict()
        base_dict["predicted_items"] = self.predicted_items
        return base_dict


class JobSuggestionResult:
    job_id: str
    suggested_trainings: list[str]

    def __init__(self, job_id: str, suggested_trainings: list[str] = []):
        self.job_id = job_id
        self.suggested_trainings = suggested_trainings

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "suggested_trainings": self.suggested_trainings,
        }


class JobsAndTrainingsSuggestionResult(BaseSuggestionResult):
    jobs: list[JobSuggestionResult]

    def __init__(self, persona_id: str, jobs: list[JobSuggestionResult] = []):
        super().__init__(persona_id, predicted_type=PredictionType.JOBS_AND_TRAININGS)
        self.jobs = jobs

    def to_dict(self) -> dict:
        base_dict = super().to_dict()
        base_dict["jobs"] = [job.to_dict() for job in self.jobs]
        return base_dict


class TrainingsOnlySuggestionResult(BaseSuggestionResult):
    trainings: list[str]

    def __init__(self, persona_id: str, trainings: list[str] = []):
        super().__init__(persona_id, predicted_type=PredictionType.TRAININGS_ONLY)
        self.trainings = trainings

    def to_dict(self) -> dict:
        base_dict = super().to_dict()
        base_dict["trainings"] = self.trainings
        return base_dict
