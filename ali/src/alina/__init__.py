from dotenv import load_dotenv

load_dotenv()

import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logging.getLogger("botocore").setLevel(logging.WARN)
logging.getLogger("httpx").setLevel(logging.WARN)

import typer

from .cli.analyze import app as analyze_app
from .cli.build_skills import app as build_skills_app
from .cli.chat import app as chat_app
from .cli.chat_persona import app as chat_persona_app
from .cli.experiment import app as experiment_app
from .cli.fuzzy import app as fuzzy_app
from .cli.interview import app as interview_app
from .cli.interview_full import app as interview_full_app
from .cli.interview_job import app as interview_job_app
from .cli.interview_training import app as interview_training_app
from .cli.merge import app as merge_app
from .cli.presuggest import app as presuggest_app
from .cli.rank import app as rank_app
from .cli.status import app as status_app
from .cli.submissions import app as submissions_app
from .cli.submit import app as submit_app
from .cli.suggest import app as suggest_app
from .cli.suggest_training import app as suggest_training_app
from .cli.version import app as version_app

app = typer.Typer()

app.add_typer(analyze_app)
app.add_typer(build_skills_app)
app.add_typer(chat_app)
app.add_typer(chat_persona_app)
app.add_typer(experiment_app)
app.add_typer(fuzzy_app)
app.add_typer(interview_app)
app.add_typer(interview_full_app)
app.add_typer(interview_job_app)
app.add_typer(interview_training_app)
app.add_typer(merge_app)
app.add_typer(presuggest_app)
app.add_typer(rank_app)
app.add_typer(status_app)
app.add_typer(submissions_app)
app.add_typer(submit_app)
app.add_typer(suggest_app)
app.add_typer(suggest_training_app)
app.add_typer(version_app)


def main():
    app()
