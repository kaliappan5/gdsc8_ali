import asyncio
import logging
from functools import partial

import typer
from asyncer import syncify
from typing_extensions import Annotated, Optional

from alina.services.analysis.ai.persona import AIPersonaAnalyzer
from alina.services.analysis.mock.persona import MockPersonaAnalyzer
from alina.services.utils.ai import AIProvider
from alina.services.utils.persona_range import PersonaRange, parse_persona_range
from alina.shared.database import (
    read_manual_intents,
    read_personas_analysis,
    save_personas_analysis,
)
from alina.shared.workspace import Workspace

app = typer.Typer()


@app.command()
@partial(syncify, raise_sync_error=False)
async def presuggest(
    ai: Optional[Annotated[AIProvider, typer.Option("--ai")]] = None,
    persona_range: Annotated[
        PersonaRange, typer.Option("--persona", parser=parse_persona_range)
    ] = PersonaRange(),
):
    """Preprocess suggestions for each persona."""

    workspace = Workspace()
    personas_to_process = persona_range.range()
    chunk_size = 5
    results = read_personas_analysis()
    if results is None:
        results = []
    manual_intents = read_manual_intents()

    async def record_result(pid: int):
        if ai:
            analyzer = AIPersonaAnalyzer(ai)
        else:
            analyzer = MockPersonaAnalyzer()
        pid_string = f"persona_{pid:03d}"
        manual_intent = manual_intents.get(pid_string)
        files = []
        files.append(workspace.get_interview_file(pid))
        if workspace.get_interview_job_file(pid).exists():
            files.append(workspace.get_interview_job_file(pid))
        if workspace.get_interview_training_file(pid).exists():
            files.append(workspace.get_interview_training_file(pid))
        result = await analyzer.analyze(pid_string, files, manual_intent)
        for i, existing_result in enumerate(results):
            if existing_result.id == pid_string:
                results[i] = result
                return
        results.append(result)

    for i in range(0, len(personas_to_process), chunk_size):
        chunk = personas_to_process[i : i + chunk_size]
        async with asyncio.TaskGroup() as tg:
            for persona_id in chunk:
                tg.create_task(record_result(persona_id))
        logging.info(
            f"Processed files {i + 1} to {min(i + chunk_size, len(personas_to_process))}"
        )
        save_personas_analysis(results)
        await asyncio.sleep(0.5)
