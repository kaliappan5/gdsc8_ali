import logging
from typing import Dict, List, Optional

from .aws import aws_signed_request


def validate_submission_format(results: List[Dict]) -> None:
    """
    Validate submission format before sending.

    Good practice: Always validate before external API calls!

    Args:
        results: List of prediction dictionaries

    Raises:
        ValueError: If format is invalid
    """
    if not results:
        raise ValueError("Results list is empty")

    if len(results) != 100:
        raise ValueError(f"Error: Expected 100 personas, got {len(results)}")

    required_fields = {"persona_id", "predicted_type"}
    valid_types = {"jobs+trainings", "trainings_only", "awareness"}

    for i, result in enumerate(results):
        # Check required fields
        if not required_fields.issubset(result.keys()):
            missing = required_fields - result.keys()
            raise ValueError(f"Result {i} missing required fields: {missing}")

        # Check predicted_type
        pred_type = result["predicted_type"]
        if pred_type not in valid_types:
            raise ValueError(
                f"Result {i} has invalid predicted_type: '{pred_type}'. "
                f"Must be one of: {valid_types}"
            )

        # Type-specific validation
        if pred_type == "jobs+trainings":
            if "jobs" not in result:
                raise ValueError(f"Result {i} missing 'jobs' field")
            if not isinstance(result["jobs"], list):
                raise ValueError(f"Result {i} 'jobs' must be a list")
            # Validate job structure
            for job in result["jobs"]:
                if not isinstance(job, dict):
                    raise ValueError(
                        f"Result {i} job items must be dictionaries, got {type(job)}"
                    )
                if "job_id" not in job:
                    raise ValueError(f"Result {i} job missing 'job_id'")
                if "suggested_trainings" not in job:
                    raise ValueError(f"Result {i} job missing 'suggested_trainings'")

        elif pred_type == "trainings_only":
            if "trainings" not in result:
                raise ValueError(f"Result {i} missing 'trainings' field")
            if not isinstance(result["trainings"], list):
                raise ValueError(f"Result {i} 'trainings' must be a list")

        elif pred_type == "awareness":
            # awareness type can have optional predicted_items
            pass


class SubmissionResponse:
    def __init__(
        self,
        success: bool,
        message: Optional[str] = None,
        id: Optional[str] = None,
        submission_count: Optional[int] = None,
    ):
        self.success = success
        self.message = message
        self.id = id
        self.submission_count = submission_count


def make_submission(results: List[Dict]) -> SubmissionResponse:
    """
    Submit results to GDSC challenge endpoint.

    Args:
        results: List of predictions in challenge format

    Returns:
        API response
    """

    response = aws_signed_request(
        path="submit",
        method="POST",
        payload={"submission": results},
    )
    if response is None:
        return SubmissionResponse(success=False, message="No response from server")
    if not response.ok:
        return SubmissionResponse(
            success=False,
            message=f"Submission failed with status {response.status_code}: {response.text}",
        )
    try:
        response_json = response.json()
        if response_json:
            msg = response_json.get("message")
            sid = response_json.get("submission_id")
            scount = response_json.get("submission_count")
            return SubmissionResponse(
                success=True,
                message=msg,
                id=sid,
                submission_count=scount,
            )
        else:
            return SubmissionResponse(success=True)
    except ValueError:
        logging.warning("Submission succeeded but response body was not JSON")
        return SubmissionResponse(success=True)


class SubmissionHistoryEntry:
    def __init__(self, date: str, score: float):
        self.date = date
        self.score = score


def get_submissions() -> list[SubmissionHistoryEntry]:
    try:
        response = aws_signed_request(path="submit", method="GET")
        if not response:
            logging.error("No response from server when fetching submissions")
            return []
        try:
            submissions = response.json()
            history = []
            for entry in submissions:
                history.append(
                    SubmissionHistoryEntry(
                        date=entry["CreatedAt"], score=float(entry["Score"])
                    )
                )
            return history
        except ValueError as e:
            raise RuntimeError("Failed to parse JSON for submissions list") from e
    except Exception as e:
        logging.error(f"Error fetching submissions: {e}")
        return []
