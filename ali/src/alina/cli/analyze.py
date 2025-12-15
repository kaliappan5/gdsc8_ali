import asyncio
import logging
from functools import partial
from pathlib import Path
from typing import Any, Callable
from typing import Coroutine as CoroutineType
from typing import TypeVar

import typer
from asyncer import syncify
from typing_extensions import Annotated, Optional

from alina.services.analysis.ai.job import AIJobAnalyzer
from alina.services.analysis.ai.training import AITrainingAnalyzer
from alina.services.analysis.mock.job import MockJobAnalyzer
from alina.services.analysis.mock.training import MockTrainingAnalyzer
from alina.services.utils.ai import AIProvider, get_ai_manager
from alina.shared.database import save_job_analysis, save_training_analysis
from alina.shared.workspace import Workspace

app = typer.Typer()

T = TypeVar("T")


async def analyze_markdown_folder(
    path: Path, analyze_function: Callable[[Path], CoroutineType[Any, Any, T]]
) -> list[T]:
    """Analyze all markdown files in the given folder."""
    if not path.exists() or not path.is_dir():
        logging.error(f"The path {path} does not exist or is not a directory.")
        raise typer.Exit(code=1)

    logging.info(f"Analyzing Markdown files in {path}")
    results = []

    async def record_result(p: Path):
        result = await analyze_function(p)
        results.append(result)

    all_files = list(path.glob("*.md"))
    logging.info(f"Found {len(all_files)} markdown files to analyze.")

    chunk_size = 10
    for i in range(0, len(all_files), chunk_size):
        chunk = all_files[i : i + chunk_size]
        async with asyncio.TaskGroup() as tg:
            for md_file in chunk:
                tg.create_task(record_result(md_file))
        logging.info(
            f"Processed files {i + 1} to {min(i + chunk_size, len(all_files))}"
        )
        await asyncio.sleep(0.5)
    return results


@app.command()
@partial(syncify, raise_sync_error=False)
async def analyze(
    ai: Optional[Annotated[AIProvider, typer.Option("--ai")]] = None,
    jobs_only: Annotated[bool, typer.Option("--jobs-only")] = False,
    trainings_only: Annotated[bool, typer.Option("--trainings-only")] = False,
    only_element: Annotated[str, typer.Option("--only")] = "",
):
    """Analyze input data"""
    path = Workspace().get_data_folder()
    if not path.exists() or not path.is_dir():
        logging.error(f"The path {path} does not exist or is not a directory.")
        raise typer.Exit(code=1)

    if jobs_only and trainings_only:
        logging.error("Cannot specify both --jobs-only and --trainings-only.")
        raise typer.Exit(code=1)

    if ai:
        ai_manager = get_ai_manager(ai)
        job_analyzer = AIJobAnalyzer(ai_manager)
        training_analyzer = AITrainingAnalyzer(ai_manager)
    else:
        job_analyzer = MockJobAnalyzer()
        training_analyzer = MockTrainingAnalyzer()
    if only_element:
        # Analyze only the specified element
        if not only_element.endswith(".md"):
            only_element += ".md"
        if only_element.startswith("j"):
            element_path = path / "jobs" / only_element
            if not element_path.exists():
                logging.error(f"The specified job file {element_path} does not exist.")
                raise typer.Exit(code=1)
            analysis_result = await job_analyzer.analyze(element_path)
            print(analysis_result)
        elif only_element.startswith("tr"):
            element_path = path / "trainings" / only_element
            if not element_path.exists():
                logging.error(
                    f"The specified training file {element_path} does not exist."
                )
                raise typer.Exit(code=1)
            analysis_result = await training_analyzer.analyze(element_path)
            print(analysis_result)
        else:
            logging.error(
                "Invalid value for --only. Must start with 'j' for jobs or 'tr' for trainings."
            )
            raise typer.Exit(code=1)
    else:
        # Analyze all elements
        logging.info(f"Analyzing input data in {path}")
        if not trainings_only:
            job_results = await analyze_markdown_folder(
                path / "jobs",
                lambda p: job_analyzer.analyze(p),
            )
            save_job_analysis(job_results)

        if not jobs_only:
            training_results = await analyze_markdown_folder(
                path / "trainings",
                lambda p: training_analyzer.analyze(p),
            )
            save_training_analysis(training_results)
