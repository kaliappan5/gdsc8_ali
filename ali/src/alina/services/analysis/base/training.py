from abc import ABC, abstractmethod
from pathlib import Path

from alina.models.referential import TrainingReferential


class BaseTrainingAnalyzer(ABC):
    """
    Abstract class for analyzing training data.
    """

    @abstractmethod
    async def analyze(self, path: Path) -> TrainingReferential:
        pass
