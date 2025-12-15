import asyncio
from pathlib import Path
from typing import Optional

from alina.models.referential import ManualUserIntent, PersonaReferential

from ..base.persona import BasePersonaAnalyzer


class MockPersonaAnalyzer(BasePersonaAnalyzer):
    async def analyze(
        self, id: str, paths: list[Path], manual_intent: Optional[ManualUserIntent]
    ) -> PersonaReferential:
        print(f"Mock analyzing persona data at {id}")
        await asyncio.sleep(0.1 + (len(paths[0].name) % 5) * 0.1)
        return PersonaReferential(id=id, age=30, city="MockCity")
