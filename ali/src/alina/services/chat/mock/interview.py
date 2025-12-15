from ..base.interview import BaseInterviewer, Intent, InterviewDetails


class MockInterviewer(BaseInterviewer):
    def start_conversation(self) -> InterviewDetails:
        return InterviewDetails(
            ability_to_relocate=None,
            age=None,
            city=None,
            education_level=None,
            next_message="Hello! I'm Alina, your virtual assistant. To get started, could you please tell me your age?",
            intent=None,
            domain_of_interest=None,
            years_of_experience=None,
            skills=None,
        )

    def send_message(self, message: str) -> InterviewDetails:
        return InterviewDetails(
            intent=Intent.EMPLOYMENT,
            domain_of_interest="Technology",
            ability_to_relocate=True,
            age=25,
            city="São Paulo",
            education_level=5,
            next_message="Thanks for that",
            years_of_experience=3,
            skills="Python (advanced), Java (intermediate)",
        )
