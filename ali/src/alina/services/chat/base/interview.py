from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Intent(str, Enum):
    EMPLOYMENT = "EMPLOYMENT"
    TRAINING = "TRAINING"
    INFORMATION = "INFORMATION"


class InterviewDetails(BaseModel):
    next_message: str = Field(
        "",
        description="""
            The next message to ask the user for more information. You HAVE to provide a message here.
        """,
    )
    age: Optional[int] = Field(
        None,
        description="The age of the interviewee.",
    )
    confidence_in_age: Optional[int] = Field(
        None,
        description="The confidence level (1-10) in the reported age of the interviewee.",
    )
    city: Optional[str] = Field(
        None,
        description="The city of residence of the interviewee.",
    )
    ability_to_relocate: Optional[bool] = Field(
        None,
        description="Indicates whether the interviewee is willing to relocate.",
    )
    intent: Optional[Intent] = Field(
        None,
        description="The intent of the interviewee: seeking employment, training, or information.",
    )
    education_level: Optional[int] = Field(
        None,
        description="""
            The educational level of the interviewee.
            Brazilian educational levels are:
            1. Ensino Fundamental
            2. Ensino Médio
            3. Técnico
            4. Tecnólogo
            5. Graduação
            6. Bacharelado
            7. Licenciatura
            8. Pós-graduação
            9. Especialização
            10. Mestrado
            11. MBA
            12. Doutorado
        """,
    )
    domain_of_interest: Optional[str] = Field(
        None,
        description="The domain of interest of the interviewee.",
    )
    years_of_experience: Optional[int] = Field(
        None,
        description="The number of years of experience the interviewee has in their domain of interest.",
    )
    skills: Optional[str] = Field(
        None,
        description="The skills and proficiency levels (1 Básico, 2 Intermediário or 3 Avançado) of the interviewee, if applicable.",
    )


class BaseInterviewer(ABC):
    @abstractmethod
    def start_conversation(self) -> InterviewDetails:
        pass

    @abstractmethod
    def send_message(self, message: str) -> InterviewDetails:
        pass
