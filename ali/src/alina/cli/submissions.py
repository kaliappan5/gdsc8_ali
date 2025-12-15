import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Sequence

import typer
import xlsxwriter
from rich import print

from alina.models.suggestion import PredictionType
from alina.services.utils.submission import SubmissionHistoryEntry, get_submissions
from alina.shared.workspace import Workspace

app = typer.Typer()


def read_submission_file(submission_file: Path):
    with open(submission_file) as f:
        submission_data = json.load(f)
    return submission_data


def build_matrix(files: list[Path]):
    matrix = []
    for submission_file in files:
        submission_data = read_submission_file(submission_file)
        submission_data_entries: Dict[int, Dict] = {}
        for entry in submission_data:
            submission_data_entries[
                int(str(entry["persona_id"]).replace("persona_", ""))
            ] = entry
        cell_content: Dict[int, str] = {}
        for persona_id in range(1, 101):
            submission_entry = submission_data_entries.get(persona_id)
            if not submission_entry:
                continue
            intent_cell_content = None

            if submission_entry.get("predicted_type", "") == "trainings_only":
                intent_cell_content = "Tr"
            elif submission_entry.get("predicted_type", "") == "jobs+trainings":
                intent_cell_content = "Jo"
            elif submission_entry.get("predicted_type", "") == "awareness":
                if submission_entry.get("predicted_items") == "too_young":
                    intent_cell_content = "Ay"
                elif submission_entry.get("predicted_items") == "info":
                    intent_cell_content = "Ai"
                else:
                    intent_cell_content = "?"
            else:
                intent_cell_content = "?"

            cell_content[persona_id] = intent_cell_content
        matrix.append(cell_content)
    return matrix


def read_or_get_submissions(folder: Path) -> Sequence[SubmissionHistoryEntry]:
    expected_submissions = len(list(folder.glob("submission_*.json")))
    submissions_file = Workspace().get_submissions_file()
    if submissions_file.exists():
        with open(submissions_file) as f:
            submissions_json = json.load(f)
            current_submissions_in_cache = len(submissions_json)
            submissions = [
                SubmissionHistoryEntry(**entry) for entry in submissions_json
            ]
    else:
        current_submissions_in_cache = 0
        submissions = []

    if current_submissions_in_cache != expected_submissions:
        logging.info(f"Difference in submissions count, reloading...")
        submissions = get_submissions()
        # Write the cache
        with open(submissions_file, "w") as f:
            json.dump(
                [entry for entry in submissions],
                f,
                indent=4,
                default=lambda x: getattr(x, "__dict__", str(x)),
            )
    else:
        logging.info(f"Loading submissions from cache...")

    return submissions


def generate_intent_worksheet(
    workbook: xlsxwriter.Workbook,
    first_id: int,
    submissions_files: list[Path],
    scored_submissions_by_date: Sequence[SubmissionHistoryEntry],
):
    center_bold_format = workbook.add_format({"align": "center", "bold": True})
    center_format = workbook.add_format({"align": "center"})
    red_format = workbook.add_format({"font_color": "red", "align": "center"})
    light_gray_bg_format = workbook.add_format(
        {"bg_color": "#D3D3D3", "align": "center"}
    )
    light_green_format = workbook.add_format({"bg_color": "#90EE90"})
    light_red_format = workbook.add_format({"bg_color": "#FFCCCB"})
    worksheet = workbook.add_worksheet("Intent")
    worksheet.freeze_panes(2, 1)

    for persona_id in range(1, 101):
        worksheet.write(persona_id + 1, 0, f"P{persona_id:03d}", center_bold_format)
    matrix = build_matrix(submissions_files)
    for sub_index, submission_dict in enumerate(matrix):
        worksheet.write(
            0,
            sub_index + 1,
            f"#{sub_index + 1 + first_id}",
            center_bold_format,
        )
        # Score format based on value and previous score
        previous_score = (
            scored_submissions_by_date[sub_index - 1].score if sub_index > 0 else None
        )
        current_score = scored_submissions_by_date[sub_index].score
        if previous_score is not None:
            if current_score > previous_score:
                score_format = light_green_format
            elif current_score < previous_score:
                score_format = light_red_format
            else:
                score_format = None
        else:
            score_format = None

        worksheet.write(
            1, sub_index + 1, scored_submissions_by_date[sub_index].score, score_format
        )

        for persona_id in range(1, 101):
            content = submission_dict.get(persona_id, "")
            previous_content = (
                matrix[sub_index - 1].get(persona_id) if sub_index > 0 else ""
            )

            if previous_content and content != previous_content:
                style = light_gray_bg_format
            else:
                if content == "?" or content is None:
                    style = red_format
                else:
                    style = center_format
            worksheet.write(
                persona_id + 1,
                sub_index + 1,
                submission_dict.get(persona_id, ""),
                style,
            )

    for persona_id in range(1, 101):
        # Reduce row height if all submissions have the same content for this persona
        all_same = all(
            matrix[0].get(persona_id) == matrix[i].get(persona_id)
            for i in range(1, len(matrix))
        )
        if all_same:
            worksheet.set_row(persona_id + 1, 0)


def generate_trainings_worksheet(
    workbook: xlsxwriter.Workbook,
    submissions_file: Path,
):
    center_bold_format = workbook.add_format({"align": "center", "bold": True})
    center_format = workbook.add_format(
        {
            "align": "center",
        }
    )
    worksheet = workbook.add_worksheet("Trainings Only")

    submission_data = read_submission_file(submissions_file)
    row = 0
    for submission_entry in submission_data:
        if submission_entry.get("predicted_type", "") != PredictionType.TRAININGS_ONLY:
            continue
        worksheet.write(
            row,
            0,
            f"P{str(submission_entry['persona_id']).replace('persona_', '')}",
            center_bold_format,
        )
        trainings_ids = sorted(submission_entry.get("trainings", []))
        for column, training_id in enumerate(trainings_ids, start=1):
            worksheet.write(row, column, training_id, center_format)
        row += 1


def generate_job_trainings_worksheet(
    workbook: xlsxwriter.Workbook,
    submissions_file: Path,
):
    center_bold_format = workbook.add_format({"align": "center", "bold": True})
    center_format = workbook.add_format(
        {
            "align": "center",
        }
    )
    worksheet = workbook.add_worksheet("Jobs + Trainings")

    submission_data = read_submission_file(submissions_file)
    row = 0
    for submission_entry in submission_data:
        if (
            submission_entry.get("predicted_type", "")
            != PredictionType.JOBS_AND_TRAININGS
        ):
            continue
        worksheet.write(
            row,
            0,
            f"P{str(submission_entry['persona_id']).replace('persona_', '')}",
            center_bold_format,
        )
        jobs = sorted(
            submission_entry.get("jobs", []), key=lambda j: j.get("job_id", "")
        )
        column = 1
        max_trainings = 0
        for job_dict in jobs:
            job_id = job_dict.get("job_id", "")
            worksheet.write(row, column, job_id, center_bold_format)
            trainings_ids = sorted(job_dict.get("suggested_trainings", []))
            for idx, training_id in enumerate(trainings_ids):
                worksheet.write(row + idx + 1, column, training_id, center_format)
            if len(trainings_ids) > max_trainings:
                max_trainings = len(trainings_ids)
            column += 1
        row += 1 + max_trainings


@app.command()
def submissions(
    tail: Optional[int] = typer.Option(None, help="Show only the last N submissions"),
    inspect: Optional[int] = typer.Option(
        None,
        help="Inspect a specific submission by its ID (otherwise the latest submission is used)",
    ),
):
    """Generate an Excel file of all submissions"""

    workspace = Workspace()
    submissions_folder = workspace.get_submissions_folder()

    scored_submissions = read_or_get_submissions(submissions_folder)
    scored_submissions_by_date = sorted(
        scored_submissions, key=lambda entry: entry.date
    )

    # Save the XLSX file in user's download folder, named with current date/time
    output_xls_file = (
        Path.home()
        / "Downloads"
        / f"submissions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    )

    workbook = xlsxwriter.Workbook(output_xls_file)

    all_submissions_files = sorted(
        list(submissions_folder.glob("submission_*.json")), key=lambda p: p.name
    )
    if tail is not None:
        submissions_files = all_submissions_files[-tail:]
        scored_submissions_by_date = scored_submissions_by_date[-tail:]
    else:
        submissions_files = all_submissions_files

    generate_intent_worksheet(
        workbook,
        first_id=(len(all_submissions_files) - tail if tail is not None else 0),
        submissions_files=submissions_files,
        scored_submissions_by_date=scored_submissions_by_date,
    )

    if inspect:
        inspected_submission_file = (
            workspace.get_submissions_folder() / f"submission_{inspect:03d}.json"
        )
    else:
        inspected_submission_file = submissions_files[-1]
    generate_trainings_worksheet(workbook, submissions_file=inspected_submission_file)

    generate_job_trainings_worksheet(
        workbook, submissions_file=inspected_submission_file
    )

    workbook.close()
    print(f"Saved submissions XLSX file to: {output_xls_file}")
