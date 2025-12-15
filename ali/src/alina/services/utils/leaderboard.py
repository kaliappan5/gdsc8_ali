import requests

from ...shared.config import Configuration


class LeaderboardEntry:
    date: str
    score: float
    team_name: str

    def __init__(self, date: str, score: float, team_name: str):
        self.date = date
        self.score = score
        self.team_name = team_name


def get_leaderboard() -> list[LeaderboardEntry]:
    configuration = Configuration()
    try:
        response = requests.request(
            method="GET",
            url=f"{configuration.AWS_PUBLIC_BASE_URL.rstrip('/')}/human_eval/leaderboard",
            headers={"Content-Type": "application/json"},
        )
    except requests.RequestException as e:
        raise RuntimeError(f"Network error during request") from e

    if response.ok:
        data = response.json()
        return [
            LeaderboardEntry(
                date=item["CreatedAt"],
                score=float(item["Score"]),
                team_name=item["TeamName"],
            )
            for item in data
        ]
    else:
        raise RuntimeError(
            f"Leaderboard request failed with status {response.status_code}: {response.text}"
        )
