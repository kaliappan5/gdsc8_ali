from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from alina.models.referential import ManualUserIntent, PersonaReferential


class BasePersonaAnalyzer(ABC):
    """
    Abstract class for analyzing persona information.
    """

    @abstractmethod
    async def analyze(
        self, id: str, paths: list[Path], manual_intent: Optional[ManualUserIntent]
    ) -> PersonaReferential:
        pass
