from datetime import datetime, timedelta, timezone
from typing import Annotated, Dict

import typer
from rich import print

from alina.services.utils.leaderboard import LeaderboardEntry, get_leaderboard
from alina.services.utils.submission import get_submissions

app = typer.Typer()


def format_date(date: str):
    dt = datetime.fromisoformat(date)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    utc_plus_2 = dt.astimezone(timezone(timedelta(hours=2)))
    return utc_plus_2.strftime("%d/%m %H:%M:%S")


@app.command()
def rank(
    head: Annotated[int, typer.Option("--head")] = 5,
):
    """Show submissions and leaderboard."""
    submissions = get_submissions()

    if submissions:
        submissions_sorted_by_date = sorted(
            submissions, key=lambda entry: entry.date, reverse=True
        )
        submissions_sorted_by_score = sorted(
            submissions, key=lambda entry: entry.score, reverse=True
        )

        print(f"🗓️ Last {head} submissions:")
        for i, entry in enumerate(submissions_sorted_by_date[:head], 1):
            print(
                f" - #{len(submissions_sorted_by_date) - i + 1}: [bold]{format_date(entry.date)}[/bold], score = {entry.score}"
            )

        print(f"\n🎖️ Top {head} submissions by score:")
        for entry in submissions_sorted_by_score[:head]:
            print(
                f" - #{len(submissions) - submissions_sorted_by_date.index(entry)}: [bold]{format_date(entry.date)}[/bold], score = {entry.score}"
            )
    else:
        print("No submissions found.")

    leaderboard = get_leaderboard()
    top_scores: Dict[str, LeaderboardEntry] = {}
    submission_count: Dict[str, int] = {}
    for entry in leaderboard:
        if (
            entry.team_name not in top_scores
            or entry.score > top_scores[entry.team_name].score
        ):
            top_scores[entry.team_name] = entry
        submission_count[entry.team_name] = submission_count.get(entry.team_name, 0) + 1

    if top_scores:
        top_scores_entries = sorted(
            top_scores.values(), key=lambda entry: entry.score, reverse=True
        )[0:20]
        print("\n🏆 Leaderboard Top Scores:")
        for i, entry in enumerate(top_scores_entries):
            team_name = entry.team_name if entry.team_name else "(none)"
            print(
                f" {i + 1:>2}. [bold]{team_name:<30}[/bold] | {str(entry.score):<8} | {submission_count[entry.team_name]:3d}/120"
            )
