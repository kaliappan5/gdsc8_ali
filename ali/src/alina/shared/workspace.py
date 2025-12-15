from pathlib import Path


def get_workspace_folder() -> Path:
    # Iterate until a .git folder is found
    current_path = Path.cwd()
    for parent in [current_path] + list(current_path.parents):
        if (parent / ".git").is_dir():
            return parent / "workspace"

    # If no .git folder is found, return the current working directory
    return current_path


class Workspace:
    def __init__(self):
        self.folder: Path = get_workspace_folder()

        if not self.folder.exists():
            self.folder.mkdir(parents=True, exist_ok=True)

    def get_data_folder(self) -> Path:
        return self.folder / ".." / ".." / "data"

    def get_data_trainings_folder(self) -> Path:
        return self.get_data_folder() / "trainings"

    def get_data_jobs_folder(self) -> Path:
        return self.get_data_folder() / "jobs"

    def get_submissions_file(self) -> Path:
        return self.folder / "submissions.json"

    def get_trainings_db_file(self) -> Path:
        return self.folder / "trainings.json"

    def get_jobs_db_file(self) -> Path:
        return self.folder / "jobs.json"

    def get_personas_db_file(self) -> Path:
        return self.folder / "personas.json"

    def get_skills_db_file(self) -> Path:
        return self.folder / "skills.json"

    def get_manual_intents_db_file(self) -> Path:
        return self.folder / "manual-intents.json"

    def get_interview_file(self, persona_id: int) -> Path:
        return self.folder / "interviews" / f"persona_{persona_id:03d}.md"

    def get_interview_training_file(self, persona_id: int) -> Path:
        return self.folder / "interviews_training" / f"persona_{persona_id:03d}.md"

    def get_interview_job_file(self, persona_id: int) -> Path:
        return self.folder / "interviews_job" / f"persona_{persona_id:03d}.md"

    def get_interview_full_file(self, persona_id: int) -> Path:
        return self.folder / "interviews_full" / f"persona_{persona_id:03d}.md"

    def get_interview_summary_file(self, persona_id: int) -> Path:
        return (
            self.folder / "interview_summaries" / f"persona_{persona_id:03d}_summary.md"
        )

    def get_training_suggestions_file(self):
        return self.folder / "training_suggestions.json"

    def get_suggestions_folder(self):
        return self.folder / "suggestions"

    def get_next_suggestion_file(self) -> Path:
        folder = self.get_suggestions_folder()
        if not folder.exists():
            folder.mkdir(parents=True, exist_ok=True)
        existing_files = list(folder.glob("suggestions_*.json"))
        max_index = max([int(f.stem.split("_")[1]) for f in existing_files] or [0])
        return folder / f"suggestions_{max_index + 1:03d}.json"

    def get_in_progress_suggestion_folder(self) -> Path:
        return self.get_suggestions_folder() / "in_progress"

    def get_in_progress_suggestion_file(self, persona_id: int) -> Path:
        folder = self.get_in_progress_suggestion_folder()
        return folder / f"persona_{persona_id:03d}_suggestions.json"

    def get_last_suggestion_file(self) -> Path:
        folder = self.get_suggestions_folder()
        existing_files = list(folder.glob("suggestions_*.json"))
        if not existing_files:
            raise FileNotFoundError("No suggestion files found.")
        max_index = max([int(f.stem.split("_")[1]) for f in existing_files])
        return folder / f"suggestions_{max_index:03d}.json"

    def get_submissions_folder(self) -> Path:
        return self.folder / "submissions"

    def get_submission_file(self, index: int) -> Path:
        return self.get_submissions_folder() / f"submission_{index:03d}.json"

    def get_next_submission_file(self) -> Path:
        folder = self.get_submissions_folder()
        if not folder.exists():
            folder.mkdir(parents=True, exist_ok=True)
        existing_files = list(folder.glob("submission_*.json"))
        max_index = max([int(f.stem.split("_")[1]) for f in existing_files] or [0])
        return folder / f"submission_{max_index + 1:03d}.json"
