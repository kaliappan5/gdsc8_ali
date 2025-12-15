from enum import Enum
from typing import Optional

EDUCATION_LEVELS = {
    1: "Ensino Fundamental",
    2: "Ensino Médio",
    3: "Técnico",
    4: "Tecnólogo",
    5: "Graduação",
    6: "Bacharelado",
    7: "Licenciatura",
    8: "Pós-graduação",
    9: "Especialização",
    10: "Mestrado",
    11: "MBA",
    12: "Doutorado",
}

DOMAINS = {
    1: "Finance & Accounting",
    2: "Legal & Regulatory",
    3: "Engineering & Technology",
    4: "Manufacturing & Industrial Operations",
    5: "Food Science & Production",
    6: "Paper & Fiber Industries",
    7: "Maritime & Port Operations",
    8: "Safety, Health & Environment",
    9: "Arts, Culture & Design",
    10: "Events & Entertainment",
    11: "Tourism & Hospitality",
    12: "Procurement & Supply Chain",
    13: "Community & Social Services",
    14: "Education & Information Management",
    15: "Research & Innovation",
}

HIGH_LEVEL_DOMAINS = [
    [3, 4, 5, 6, 7],
    [1, 2, 12],
    [9, 10, 11],
    [8, 13],
    [14, 15],
]

HIGH_LEVEL_DOMAIN_NAMES = {
    100: "Technical & Industrial",
    200: "Business & Administrative",
    300: "Arts, Culture & Tourism",
    400: "Social & Environmental",
    500: "Education & Research",
}

SKILL_LEVELS = {
    0: "No Knowledge",
    1: "Básico",
    2: "Intermediário",
    3: "Avançado",
}


class TrainingReferential:
    id: str
    city: Optional[str]
    online: bool
    locale: str
    duration_weeks: int
    certification: bool
    domain: int
    skills_description: str
    level_change: str
    target_job: str

    def __init__(
        self,
        id: str,
        online: bool,
        locale: str,
        duration_weeks: int,
        certification: bool,
        domain: int,
        skills_description: str,
        level_change: str,
        target_job: str,
        city: Optional[str] = None,
    ):
        self.id = id
        self.online = online
        self.locale = locale
        self.duration_weeks = duration_weeks
        self.certification = certification
        self.domain = domain
        self.skills_description = skills_description
        self.level_change = level_change
        self.target_job = target_job
        self.city = city


class JobSkillRequirementLevel:
    skill: str
    level: int
    required: bool

    def __init__(self, skill: str, level: int, required: bool):
        self.skill = skill
        self.level = level
        self.required = required


class JobReferential:
    id: str
    city: Optional[str]
    remote: bool
    domain: int
    education_level: Optional[int]
    languages: list[str]
    experience: int
    description: str
    skills: list[JobSkillRequirementLevel]

    def __init__(
        self,
        id: str,
        skills: list[JobSkillRequirementLevel],
        remote: bool,
        domain: int,
        languages: list[str],
        experience: int,
        education_level: Optional[int],
        description: str,
        city: Optional[str] = None,
    ):
        self.id = id
        self.remote = remote
        self.domain = domain
        self.education_level = education_level
        self.languages = languages
        self.experience = experience
        self.skills = skills
        self.description = description
        self.city = city


class UserIntent(str, Enum):
    AWARENESS = "awareness"
    JOBS_AND_TRAININGS = "jobs_and_trainings"
    ONLY_TRAININGS = "only_trainings"


class ManualUserIntent(str, Enum):
    AWARENESS_INFO = "awareness:info"
    AWARENESS_TOO_YOUNG = "awareness:too_young"
    JOBS_AND_TRAININGS = "jobs+trainings"
    TRAININGS_ONLY = "trainings_only"


class PersonaReferential:
    id: str
    age: int
    city: Optional[str]
    intent: Optional[UserIntent]
    willing_to_relocate: Optional[bool]
    education_level: Optional[int]
    domain: Optional[int]
    job_experience: Optional[int]
    job_description: Optional[str]
    training_description: Optional[str]
    current_skills: Optional[str]
    growth_skills: Optional[str]
    new_skills: Optional[str]

    def __init__(
        self,
        id: str,
        age: int,
        city: Optional[str] = None,
        intent: Optional[UserIntent] = None,
        willing_to_relocate: Optional[bool] = None,
        education_level: Optional[int] = None,
        domain: Optional[int] = None,
        job_experience: Optional[int] = None,
        job_description: Optional[str] = None,
        training_description: Optional[str] = None,
        current_skills: Optional[str] = None,
        growth_skills: Optional[str] = None,
        new_skills: Optional[str] = None,
    ):
        self.id = id
        self.age = age
        self.city = city
        self.intent = intent
        self.willing_to_relocate = willing_to_relocate
        self.education_level = education_level
        self.domain = domain
        self.job_experience = job_experience
        self.job_description = job_description
        self.training_description = training_description
        self.current_skills = current_skills
        self.growth_skills = growth_skills
        self.new_skills = new_skills


class SkillReferential:
    id: int
    name: str
    jobs: Optional[str]
    trainings: list[str]

    def __init__(
        self,
        id: int,
        name: str,
        trainings: list[str],
        jobs: Optional[str] = None,
    ):
        self.id = id
        self.name = name
        self.trainings = trainings
        self.jobs = jobs
