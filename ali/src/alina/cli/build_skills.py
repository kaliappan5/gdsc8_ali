import typer
from pydantic import BaseModel, Field
from strands import Agent
from typing_extensions import Annotated, Optional

from alina.models.referential import SkillReferential, TrainingReferential
from alina.services.utils.ai import AIProvider, get_ai_manager
from alina.shared.database import read_trainings_analysis, save_skills
from alina.shared.workspace import Workspace

app = typer.Typer()
workspace = Workspace()


class SkillTaxonomy(BaseModel):
    name: str = Field(
        "",
        description="""
                The name of the aggregated skill, in title-case, in English.
                The skill is not tight to a specific experience level, so do not include "Advanced", "Expert", etc. in the name.
            """,
    )
    jobs: Optional[str] = Field(
        None,
        description=f"""
                A comma-separated list of jobs the skill is related to, if applicable.
                Jobs should be in English and in title-case (e.g. Data Scientist, Software Engineer).
            """,
    )


def build_taxonomy(trainings: list[TrainingReferential], agent: Agent) -> SkillTaxonomy:
    prompt = f"""
        Given the following trainings, extract and aggregate the skills they teach into a single skill
        {''.join([f'- Training ID: {tr.id}, Skills Description: {tr.skills_description}, Target Job: {tr.target_job}\\n' for tr in trainings])}
    """
    return agent.structured_output(output_model=SkillTaxonomy, prompt=prompt)


@app.command()
def build_skills(
    ai: Annotated[AIProvider, typer.Option("--ai")],
):
    """Build skills taxonomy"""
    training_analysis = read_trainings_analysis()

    ai_manager = get_ai_manager(ai)
    taxonomy_agent = ai_manager.build_agent(
        """
        You are an expert career coach and skills taxonomy builder.
        Given a list of trainings (in ascending requirement level), you will aggregate skills they teach into a skills taxonomy (i.e. a single skill)
        """
    )

    skills = []
    trainings_per_skill = 3
    for i in range(0, len(training_analysis), trainings_per_skill):
        ids = [f"tr{j}" for j in range(i, i + trainings_per_skill)]
        trainings = [tr for tr in training_analysis if tr.id in ids]
        taxonomy = build_taxonomy(trainings, taxonomy_agent)
        skills.append(
            SkillReferential(
                id=i // trainings_per_skill + 1,
                name=taxonomy.name,
                jobs=taxonomy.jobs,
                trainings=ids,
            )
        )
    save_skills(skills)
