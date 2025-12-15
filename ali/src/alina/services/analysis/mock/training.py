import asyncio
from pathlib import Path

from alina.models.referential import TrainingReferential

from ..base.training import BaseTrainingAnalyzer


class MockTrainingAnalyzer(BaseTrainingAnalyzer):
    async def analyze(self, path: Path) -> TrainingReferential:
        online = len(path.name) % 2 == 0
        await asyncio.sleep(0.1 + (len(path.name) % 5) * 0.1)
        return TrainingReferential(
            id=path.stem,
            online=online,
            locale="en-US",
            duration_weeks=4,
            certification=True,
            domain=2,
            skills_description="Mock skills description",
            level_change="0 to 1",
            city="Mock City" if online else None,
            target_job="Data Analyst",
        )
