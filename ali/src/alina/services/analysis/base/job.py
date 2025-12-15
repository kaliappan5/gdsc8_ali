from abc import ABC, abstractmethod
from pathlib import Path

from alina.models.referential import JobReferential


class BaseJobAnalyzer(ABC):
    """
    Abstract class for analyzing job data.
    """

    @abstractmethod
    async def analyze(self, path: Path) -> JobReferential:
        pass
