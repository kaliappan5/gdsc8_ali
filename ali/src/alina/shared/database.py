import json
import logging
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from alina.models.referential import (
    JobReferential,
    JobSkillRequirementLevel,
    ManualUserIntent,
    PersonaReferential,
    SkillReferential,
    TrainingReferential,
    UserIntent,
)
from alina.models.suggestion import (
    AwarenessSuggestionResult,
    BaseSuggestionResult,
    JobsAndTrainingsSuggestionResult,
    JobSuggestionResult,
    PredictedItems,
    PredictionType,
    TrainingsOnlySuggestionResult,
)
from alina.shared.workspace import Workspace


def _save_result_to_json_file(result: Any, file_path: Path):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(
            result,
            file,
            ensure_ascii=False,
            indent=4,
            default=lambda x: getattr(x, "__dict__", str(x)),
        )
        logging.info(f"Saved to {file_path}")


def save_training_analysis(results: Sequence[TrainingReferential]):
    _save_result_to_json_file(results, Workspace().get_trainings_db_file())


def save_job_analysis(results: Sequence[JobReferential]):
    _save_result_to_json_file(results, Workspace().get_jobs_db_file())


def save_personas_analysis(results: Sequence[PersonaReferential]):
    _save_result_to_json_file(results, Workspace().get_personas_db_file())


def _convert_persona_analysis_item(item: dict) -> PersonaReferential:
    intent = None
    if "intent" in item and item["intent"] is not None:
        intent = UserIntent(item["intent"])
    return PersonaReferential(
        id=item["id"],
        age=item["age"],
        city=item.get("city"),
        intent=intent,
        willing_to_relocate=item.get("willing_to_relocate"),
        education_level=item.get("education_level"),
        domain=item.get("domain"),
        job_experience=item.get("job_experience"),
        job_description=item.get("job_description"),
        training_description=item.get("training_description"),
        current_skills=item.get("current_skills"),
        growth_skills=item.get("growth_skills"),
        new_skills=item.get("new_skills"),
    )


def read_personas_analysis() -> list[PersonaReferential]:
    personas_db_file = Workspace().get_personas_db_file()
    if not personas_db_file.exists():
        return []
    with open(personas_db_file, "r", encoding="utf-8") as file:
        data = json.load(file)
        personas = []
        for item in data:
            persona = _convert_persona_analysis_item(item)
            personas.append(persona)
        return personas


def read_persona_analysis(persona_id: str) -> Optional[PersonaReferential]:
    personas_db_file = Workspace().get_personas_db_file()
    with open(personas_db_file, "r", encoding="utf-8") as file:
        data = json.load(file)
        for item in data:
            if item["id"] == persona_id:
                return _convert_persona_analysis_item(item)
    return None


def read_trainings_analysis() -> Sequence[TrainingReferential]:
    trainings_db_file = Workspace().get_trainings_db_file()
    with open(trainings_db_file, "r", encoding="utf-8") as file:
        data = json.load(file)
        trainings = []
        for item in data:
            training = TrainingReferential(
                id=item["id"],
                online=item["online"],
                locale=item["locale"],
                duration_weeks=item["duration_weeks"],
                certification=item["certification"],
                domain=item["domain"],
                skills_description=item.get("skills_description"),
                level_change=item.get("level_change"),
                city=item.get("city"),
                target_job=item.get("target_job"),
            )
            trainings.append(training)
        return trainings


def read_jobs_analysis() -> Sequence[JobReferential]:
    jobs_db_file = Workspace().get_jobs_db_file()
    with open(jobs_db_file, "r", encoding="utf-8") as file:
        data = json.load(file)
        jobs = []
        for item in data:
            skills = [
                JobSkillRequirementLevel(
                    skill=skill_item["skill"],
                    level=skill_item["level"],
                    required=skill_item["required"],
                )
                for skill_item in item["skills"]
            ]
            job = JobReferential(
                id=item["id"],
                remote=item["remote"],
                domain=item["domain"],
                education_level=item.get("education_level"),
                languages=item["languages"],
                experience=item["experience"],
                skills=skills,
                city=item.get("city"),
                description=item.get("description"),
            )
            jobs.append(job)
        return jobs


def read_manual_intents() -> Dict[str, ManualUserIntent]:
    manual_intents_db_file = Workspace().get_manual_intents_db_file()
    if not manual_intents_db_file.exists():
        return {}
    with open(manual_intents_db_file, "r", encoding="utf-8") as file:
        data = json.load(file)
        intents = {}
        for persona_id, intent_str in data.items():
            intents[persona_id] = ManualUserIntent(intent_str)
        return intents


def save_suggestions(results: Sequence[BaseSuggestionResult]):
    _save_result_to_json_file(results, Workspace().get_next_suggestion_file())


def read_last_suggestions() -> Sequence[BaseSuggestionResult]:
    last_suggestion_file = Workspace().get_last_suggestion_file()
    with open(last_suggestion_file, "r", encoding="utf-8") as file:
        data = json.load(file)
        suggestions = []
        for item in data:
            suggestions.append(_to_base_suggestion_result(item))
        return suggestions


def _to_base_suggestion_result(data: dict) -> BaseSuggestionResult:
    persona_id_string = str(data["persona_id"])
    if data["predicted_type"] == PredictionType.JOBS_AND_TRAININGS:
        return JobsAndTrainingsSuggestionResult(
            persona_id_string,
            jobs=[
                JobSuggestionResult(
                    job_id=job_data["job_id"],
                    suggested_trainings=job_data.get("suggested_trainings", []),
                )
                for job_data in data["jobs"]
            ],
        )
    if data["predicted_type"] == PredictionType.AWARENESS:
        return AwarenessSuggestionResult(
            persona_id_string, data.get("predicted_items", "")
        )
    if data["predicted_type"] == PredictionType.TRAININGS_ONLY:
        return TrainingsOnlySuggestionResult(persona_id_string, data["trainings"])
    raise ValueError(f"Unknown prediction type: {data['predicted_type']}")


def read_in_progress_suggestions(persona_id: int) -> Optional[BaseSuggestionResult]:
    persona_suggestion_file = Workspace().get_in_progress_suggestion_file(persona_id)
    if not persona_suggestion_file.exists():
        return None
    with open(persona_suggestion_file, "r", encoding="utf-8") as file:
        data = json.load(file)
        return _to_base_suggestion_result(data)
    return None


def save_in_progress_suggestions(
    persona_id: int, suggestion_result: BaseSuggestionResult
):
    persona_suggestion_file = Workspace().get_in_progress_suggestion_file(persona_id)
    persona_suggestion_file.parent.mkdir(parents=True, exist_ok=True)
    _save_result_to_json_file(suggestion_result, persona_suggestion_file)


def clear_in_progress_suggestions():
    in_progress_folder = Workspace().get_in_progress_suggestion_folder()
    if in_progress_folder.exists():
        for file in in_progress_folder.glob("*.json"):
            file.unlink()
        in_progress_folder.rmdir()


def save_submission(results: List[Dict]):
    next_submission_file = Workspace().get_next_submission_file()
    if not next_submission_file.parent.exists():
        next_submission_file.parent.mkdir(parents=True, exist_ok=True)
    _save_result_to_json_file(results, next_submission_file)


def save_skills(skills: list[SkillReferential]):
    skills_db_file = Workspace().get_skills_db_file()
    _save_result_to_json_file(skills, skills_db_file)


def read_skills() -> list[SkillReferential]:
    skills_db_file = Workspace().get_skills_db_file()
    with open(skills_db_file, "r", encoding="utf-8") as file:
        data = json.load(file)
        skills = []
        for item in data:
            skill = SkillReferential(
                id=item["id"],
                name=item["name"],
                jobs=item.get("jobs"),
                trainings=item.get("trainings", []),
            )
            skills.append(skill)
        return skills
