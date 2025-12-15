import json
import logging
from pathlib import Path

import typer
from pydantic import BaseModel, Field
from strands.types.content import ContentBlock, Message
from typing_extensions import Annotated, Optional

from alina.models.referential import (
    ManualUserIntent,
    SkillReferential,
    TrainingReferential,
    UserIntent,
)
from alina.models.suggestion import (
    AwarenessSuggestionResult,
    JobsAndTrainingsSuggestionResult,
    JobSuggestionResult,
    PredictedItems,
    TrainingsOnlySuggestionResult,
)
from alina.services.utils.ai import AIProvider, get_ai_manager
from alina.services.utils.persona_range import PersonaRange
from alina.shared.database import (
    read_manual_intents,
    read_persona_analysis,
    read_skills,
    save_suggestions,
)
from alina.shared.workspace import Workspace

app = typer.Typer()
workspace = Workspace()


def get_interviews_content(persona_id: int) -> tuple[Optional[str], Optional[str]]:
    conversation1_file_path = workspace.get_interview_file(persona_id)
    conversation2_file_path = workspace.get_interview_training_file(persona_id)
    if not conversation1_file_path.exists() or not conversation2_file_path.exists():
        logging.warning(
            f"Interview files for persona #{persona_id} are missing, skipping"
        )
        return None, None

    with open(conversation1_file_path, "r", encoding="utf-8") as f:
        interview_content_1 = f.read()
    with open(conversation2_file_path, "r", encoding="utf-8") as f:
        interview_content_2 = f.read()
    return interview_content_1, interview_content_2


def summarize_interviews(persona_id: int, ai: AIProvider) -> Optional[str]:
    interview_content_1, interview_content_2 = get_interviews_content(persona_id)
    if not interview_content_1 or not interview_content_2:
        return None
    ai_manager = get_ai_manager(ai)
    agent = ai_manager.build_agent(
        system_prompt=f"""
        RULES:
            Based on the following interviews with a person looking for trainings, can you extract all relevant information.
            Age, location, certification, time, cost requirements ARE NOT relevant here.
            Skills (current and wishes), education, experience and interests ARE relevant.
            If multiple interviews are provided, the user is the same person in all of them, so you should group all relevant information together."""
    )
    agent.messages.append(
        Message(
            role="user",
            content=[
                ContentBlock(text="INTERVIEW 1 Content:\n"),
                ContentBlock(text=interview_content_1),
                ContentBlock(text="\n\nINTERVIEW 2 Content:\n"),
                ContentBlock(text=interview_content_2),
            ],
        )
    )
    agent_response = agent()
    message_blocks = agent_response.message.get("content", [])
    return "\n".join(block.get("text", "") for block in message_blocks)


def get_relevant_skills(
    persona_id: int,
    ai: AIProvider,
    skills: list[SkillReferential],
) -> list[int]:
    interview_content_1, interview_content_2 = get_interviews_content(persona_id)
    if not interview_content_1 or not interview_content_2:
        return []
    ai_manager = get_ai_manager(ai)

    skills_prompt = "\n".join(
        [f"- {skill.id}: {skill.name} (for jobs: {skill.jobs})" for skill in skills]
    )
    agent = ai_manager.build_agent(
        system_prompt=f"""
        RULES:
            Based on the following interview with a person looking for trainings, can you list the top 20 most relevant skills for this person?
            It can be skills that the person wants to improve, skills appicable for jobs in the domain they are interested in, or skills that would help them get started in that field.
            If you identify skills that are not in the provided list, ignore them.
            If there are less than 20 relevant skills, just list those and do NOT make up new ones.
        SKILLS:
            {skills_prompt}
        """
    )
    agent.messages.append(
        Message(
            role="user",
            content=[
                ContentBlock(text="INTERVIEW 1 Content:\n"),
                ContentBlock(text=interview_content_1),
                ContentBlock(text="\n\nINTERVIEW 2 Content:\n"),
                ContentBlock(text=interview_content_2),
            ],
        )
    )

    class SkillIdResponseModel(BaseModel):
        skill_ids: list[int] = Field(
            [], description="List of skill IDs relevant for the person"
        )

    agent_response = agent.structured_output(output_model=SkillIdResponseModel)
    return [sid for sid in set(agent_response.skill_ids)]


def get_relevant_trainings(
    ai: AIProvider,
    training_ids: list[str],
    summary_of_interviews: str,
    trainings_path: Path,
    expected_count: int,
) -> list[int]:
    ai_manager = get_ai_manager(ai)

    trainings_prompt = ""
    for tid in training_ids:
        training_file = trainings_path / f"{tid}.md"
        if training_file.exists():
            trainings_prompt += f"# TRAINING {tid[2:]}\n"
            with open(training_file, "r", encoding="utf-8") as f:
                training_content = f.read()
            trainings_prompt += training_content + "\n\n"
    if not trainings_prompt:
        return []
    agent = ai_manager.build_agent(
        system_prompt=f"""
        RULES:
            You are an expert career advisor helping people find the best trainings to improve their skills and advance their careers.
            You are given a person looking for trainings, along with their relevant information such as skills, education, experience and interests.
            List the {expected_count} most relevant trainings for this person, based on their skills, education, experience and interests.
            IMPORTANT: Only skills and background matters, location, cost and certification does NOT matter.
        """
    )
    agent.messages.append(
        Message(
            role="user",
            content=[
                ContentBlock(text="PERSON PROFILE:\n"),
                ContentBlock(text=summary_of_interviews),
                ContentBlock(text="\n\nTRAININGS:\n"),
                ContentBlock(text=trainings_prompt),
            ],
        )
    )

    class TrainingIdResponseModel(BaseModel):
        training_ids: list[int] = Field(
            [], description="List of training IDs relevant for the person"
        )

    agent_response = agent.structured_output(output_model=TrainingIdResponseModel)
    return [tid for tid in set(agent_response.training_ids)]


def resolve_training_conflict(
    training_ids: list[int],
    summary_of_interviews: str,
    ai: AIProvider,
    trainings_path: Path,
) -> int:
    ai_manager = get_ai_manager(ai)

    trainings_prompt = ""
    for tid in training_ids:
        trainings_prompt += f"# TRAINING id={tid}\n"
        training_file = trainings_path / f"tr{tid}.md"
        with open(training_file, "r", encoding="utf-8") as f:
            training_content = f.read()
        trainings_prompt += training_content + "\n\n"
    agent = ai_manager.build_agent(
        system_prompt="""
        RULES:
            You are an expert career advisor helping people find the best trainings to improve their skills and advance their careers.
            Some recommendations have already been made for a person, but there is a conflict (trainings are too similar and should be reduced)
            You should select A SINGLE TRAINING among the provided options that is the most relevant for the person, based on their skills, education, experience and interests.
            IMPORTANT: Only skills and background matters, location, cost and certification does NOT matter.
            IMPORTANT: you HAVE to provide a value for "training_id" and cannot skip it
        """
    )
    agent.messages.append(
        Message(
            role="user",
            content=[
                ContentBlock(text="PERSON PROFILE:\n"),
                ContentBlock(text=summary_of_interviews),
                ContentBlock(text="\n\nTRAININGS:\n"),
                ContentBlock(text=trainings_prompt),
            ],
        )
    )

    class TrainingIdResponseModel(BaseModel):
        training_id: int = Field(
            0,
            description="Identifier of the training selected among the provided options",
        )

    agent_response = agent.structured_output(output_model=TrainingIdResponseModel)
    return agent_response.training_id


def _get_chunked_relevant_trainings(
    chunk_size: int,
    training_ids: list[str],
    ai: AIProvider,
    interview_summary: str,
    trainings_path: Path,
) -> list[int]:
    raw_trainings = []
    for i in range(0, len(training_ids), chunk_size):
        chunk = training_ids[i : i + chunk_size]
        chunk_raw_trainings = get_relevant_trainings(
            ai, chunk, interview_summary, trainings_path, chunk_size // 2
        )
        raw_trainings.extend(chunk_raw_trainings)
    return raw_trainings


@app.command()
def suggest_training(
    ai: Annotated[AIProvider, typer.Option("--ai")],
    path: Annotated[Path, typer.Option("--path")],
):
    """Suggest trainings for each person"""

    skills = read_skills()
    trainings_path = path / "trainings"

    training_suggestions_file = Workspace().get_training_suggestions_file()
    if not training_suggestions_file.exists():
        training_suggestions = {}
    else:
        with open(training_suggestions_file, "r", encoding="utf-8") as f:
            training_suggestions = json.load(f)

    manual_intents = read_manual_intents()
    workspace = Workspace()
    for persona_id_string, manual_user_intent in manual_intents.items():
        if manual_user_intent != ManualUserIntent.TRAININGS_ONLY:
            continue
        persona_id = int(persona_id_string.split("_")[1])

        existing_training_suggestion = training_suggestions.get(persona_id_string, {})

        # First, identify relevant skills from interviews
        if not existing_training_suggestion.get("skills"):
            relevant_skill_ids = get_relevant_skills(persona_id, ai, skills)
            relevant_skill_ids = sorted(set(relevant_skill_ids))
            additional_skills = []
            for skill in relevant_skill_ids:
                if (
                    skill + 1 not in relevant_skill_ids
                    and skill + 2 in relevant_skill_ids
                ):
                    additional_skills.append(skill + 1)
                elif (
                    skill + 1 not in relevant_skill_ids
                    and skill + 2 not in relevant_skill_ids
                    and skill + 3 in relevant_skill_ids
                ):
                    additional_skills.append(skill + 1)
                    additional_skills.append(skill + 2)
            relevant_skill_ids.extend(additional_skills)
            relevant_skill_ids = sorted(set(relevant_skill_ids))
            existing_training_suggestion["skills"] = relevant_skill_ids
        else:
            relevant_skill_ids = existing_training_suggestion["skills"]

        # Then, generate a summary of both interview
        summary_file_path = workspace.get_interview_summary_file(persona_id)
        if summary_file_path.exists():
            with open(summary_file_path, "r", encoding="utf-8") as f:
                interview_summary = f.read()
        else:
            interview_summary = summarize_interviews(persona_id, ai)
            if not interview_summary:
                continue
            summary_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(summary_file_path, "w", encoding="utf-8") as f:
                f.write(interview_summary)

        # Then, find the best trainings for the person based on skills and interview summary
        if not existing_training_suggestion.get("raw_trainings"):
            skill_objects = [
                skill for skill in skills if skill.id in relevant_skill_ids
            ]
            training_ids = [
                training_id
                for skill in skill_objects
                if skill.trainings
                for training_id in skill.trainings
            ]

            chunk_size = 12
            raw_trainings = _get_chunked_relevant_trainings(
                chunk_size=chunk_size,
                training_ids=training_ids,
                ai=ai,
                interview_summary=interview_summary,
                trainings_path=trainings_path,
            )
            while len(raw_trainings) > chunk_size // 2:
                raw_trainings = _get_chunked_relevant_trainings(
                    chunk_size=chunk_size,
                    training_ids=[f"tr{tid}" for tid in raw_trainings],
                    ai=ai,
                    interview_summary=interview_summary,
                    trainings_path=trainings_path,
                )
            raw_trainings = sorted(set(raw_trainings))
            existing_training_suggestion["raw_trainings"] = raw_trainings
        else:
            raw_trainings = existing_training_suggestion["raw_trainings"]

        # Finally, resolve conflicts if several trainings belong to the same skill
        if not existing_training_suggestion.get("trainings"):
            # Looking for conflicts
            resolved_trainings = []
            for skill in relevant_skill_ids:
                skill_object = next((s for s in skills if s.id == skill), None)
                if not skill_object or not skill_object.trainings:
                    continue
                trainings_of_skill = [int(tid[2:]) for tid in skill_object.trainings]
                selected_trainings_of_skill = [
                    tid for tid in raw_trainings if tid in trainings_of_skill
                ]
                if len(selected_trainings_of_skill) > 1:
                    # Conflict found between several trainings of the same skill
                    # Only one can be recommended, as per the rules
                    resolved_training_id = resolve_training_conflict(
                        selected_trainings_of_skill,
                        interview_summary,
                        ai,
                        trainings_path,
                    )
                    resolved_trainings.append(resolved_training_id)
                else:
                    resolved_trainings.extend(selected_trainings_of_skill)

            max_trainings_in_output = 10
            if len(resolved_trainings) > max_trainings_in_output:
                resolved_trainings = get_relevant_trainings(
                    ai,
                    [f"tr{tid}" for tid in resolved_trainings],
                    interview_summary,
                    trainings_path,
                    max_trainings_in_output,
                )
            resolved_trainings = sorted(set(resolved_trainings))
            existing_training_suggestion["trainings"] = sorted(resolved_trainings)

        training_suggestions[persona_id_string] = existing_training_suggestion

        # Write the file again (after each persona) to avoid losing progress
        with open(training_suggestions_file, "w", encoding="utf-8") as f:
            json.dump(training_suggestions, f, indent=4)

    # Finally, generate the next suggestion based on that
    results = []
    for persona_id in PersonaRange().range():
        persona_id_string = f"persona_{persona_id:03d}"
        persona_analysis = read_persona_analysis(persona_id_string)
        if not persona_analysis:
            raise ValueError(f"Persona analysis for {persona_id_string} not found.")

        if persona_analysis.age < 16:
            result = AwarenessSuggestionResult(
                persona_analysis.id, PredictedItems.TOO_YOUNG
            )
        elif persona_analysis.intent == UserIntent.AWARENESS:
            result = AwarenessSuggestionResult(persona_analysis.id, PredictedItems.INFO)
        elif persona_analysis.intent == UserIntent.ONLY_TRAININGS:
            result = TrainingsOnlySuggestionResult(
                persona_id_string,
                trainings=[
                    f"tr{id}"
                    for id in training_suggestions[persona_id_string]["trainings"]
                ],
            )
        else:  # persona_analysis.intent == UserIntent.JOBS_AND_TRAININGS:
            result = JobsAndTrainingsSuggestionResult(
                persona_id_string, jobs=[JobSuggestionResult("j0", [])]
            )
        results.append(result)
    save_suggestions(results)
