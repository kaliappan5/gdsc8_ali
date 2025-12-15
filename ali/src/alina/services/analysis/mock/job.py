import asyncio
from pathlib import Path

from alina.models.referential import JobReferential

from ..base.job import BaseJobAnalyzer


class MockJobAnalyzer(BaseJobAnalyzer):
    async def analyze(self, path: Path) -> JobReferential:
        print(f"Mock analyzing job data at {path.stem}")
        await asyncio.sleep(0.1 + (len(path.name) % 5) * 0.1)
        # Reading the file
        with path.open("r", encoding="utf-8") as file:
            content = file.read()

        location = None
        if "recife" in content.lower():
            location = "Recife"
        elif "são paulo" in content.lower():
            location = "São Paulo"
        elif "rio de janeiro" in content.lower():
            location = "Rio de Janeiro"
        elif "porto alegre" in content.lower():
            location = "Porto Alegre"
        elif "belo horizonte" in content.lower():
            location = "Belo Horizonte"
        elif "brasília" in content.lower():
            location = "Brasília"
        elif "salvador" in content.lower():
            location = "Salvador"
        elif "fortaleza" in content.lower():
            location = "fortaleza"
        elif "curitiba" in content.lower():
            location = "curitiba"
        elif "remote" in content.lower():
            location = "Remote"

        if not location:
            print(content)
            raise ValueError("Location not found in the content.")

        return JobReferential(
            id=path.stem,
            city=location,
            remote=False,
            domain=1,
            education_level=3,
            languages=["pt"],
            experience=2,
            skills=[],
            description="Mock job description",
        )
