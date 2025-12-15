import typer
from typing_extensions import Annotated, Optional

from alina.models.referential import UserIntent
from alina.models.suggestion import (
    JobsAndTrainingsSuggestionResult,
    JobSuggestionResult,
    TrainingsOnlySuggestionResult,
)
from alina.services.analysis.ai.suggest import AISuggestionAnalyzer
from alina.services.analysis.base.suggest import BaseSuggestionAnalyzer
from alina.services.analysis.mock.suggest import MockSuggestionAnalyzer
from alina.services.utils.ai import AIProvider
from alina.services.utils.persona_range import PersonaRange, parse_persona_range
from alina.shared.database import (
    clear_in_progress_suggestions,
    read_in_progress_suggestions,
    read_jobs_analysis,
    read_persona_analysis,
    read_trainings_analysis,
    save_in_progress_suggestions,
    save_suggestions,
)
from alina.shared.workspace import Workspace

app = typer.Typer()
workspace = Workspace()


def compute_persona_recommendations(
    suggestion_analyzer: BaseSuggestionAnalyzer,
    persona_id: int,
    skip_jobs: bool = False,
    skip_trainings: bool = False,
):
    persona_id_string = f"persona_{persona_id:03d}"
    print(f"Computing recommendations for {persona_id_string}")
    persona_interview_file = workspace.get_interview_file(persona_id)
    if not persona_interview_file.exists():
        raise FileNotFoundError(
            f"Interview file for {persona_id_string} not found at {persona_interview_file}"
        )
    with open(persona_interview_file, "r", encoding="utf-8") as f:
        interview_content = f.read()

    persona_analysis = read_persona_analysis(persona_id_string)
    if not persona_analysis:
        raise ValueError(f"Persona analysis for {persona_id_string} not found.")

    if skip_jobs and persona_analysis.intent == UserIntent.JOBS_AND_TRAININGS:
        return JobsAndTrainingsSuggestionResult(
            persona_id_string, jobs=[JobSuggestionResult("j0", [])]
        )
    if skip_trainings and persona_analysis.intent == UserIntent.ONLY_TRAININGS:
        return TrainingsOnlySuggestionResult(persona_id_string, trainings=["tr0"])

    return suggestion_analyzer.analyze(persona_analysis, interview_content)


@app.command()
def suggest(
    ai: Optional[Annotated[AIProvider, typer.Option("--ai")]] = None,
    persona_range: Annotated[
        PersonaRange, typer.Option("--persona", parser=parse_persona_range)
    ] = PersonaRange(),
    skip_jobs: Annotated[bool, typer.Option("--skip-jobs")] = False,
    skip_trainings: Annotated[bool, typer.Option("--skip-trainings")] = False,
):
    """Suggest job/training matches for each persona."""

    jobs = read_jobs_analysis()
    trainings = read_trainings_analysis()

    in_progress_folder = workspace.get_in_progress_suggestion_folder()
    if not in_progress_folder.exists():
        in_progress_folder.mkdir(parents=True, exist_ok=True)

    if ai:
        suggestion_analyzer = AISuggestionAnalyzer(jobs, trainings, ai)
    else:
        suggestion_analyzer = MockSuggestionAnalyzer(jobs, trainings)

    results = []
    for persona_id in persona_range.range():
        persona_suggestions_from_file = read_in_progress_suggestions(persona_id)
        if persona_suggestions_from_file:
            results.append(persona_suggestions_from_file)
            continue
        persona_suggestions = compute_persona_recommendations(
            suggestion_analyzer, persona_id, skip_jobs, skip_trainings
        )
        save_in_progress_suggestions(persona_id, persona_suggestions)
        results.append(persona_suggestions)

    if persona_range.full_range:
        save_suggestions(results)
    clear_in_progress_suggestions()
