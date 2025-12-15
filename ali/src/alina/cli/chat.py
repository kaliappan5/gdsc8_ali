import typer
from rich import print
from typing_extensions import Annotated, Optional

from alina.services.chat.ai.interview import InitialAIInterviewer, InterviewDetails
from alina.services.chat.mock.interview import MockInterviewer
from alina.services.utils.ai import AIProvider

app = typer.Typer()


@app.command()
def chat(ai: Optional[Annotated[AIProvider, typer.Option("--ai")]] = None):
    """Chat with ALINA"""

    if ai:
        interviewer = InitialAIInterviewer(ai)
    else:
        interviewer = MockInterviewer()

    def print_details(interview_details: InterviewDetails):
        if interview_details.next_message:
            print("[bold magenta][i]Alina:[/i][/bold magenta] ", end="")
            print(interview_details.next_message)

    def print_current_state(interview_details: InterviewDetails):
        print("\n[bold yellow]Current Interview Details:[/bold yellow]")
        print(f"- Age: {interview_details.age}")
        print(
            f"- City: {interview_details.city} (Able to relocate: {interview_details.ability_to_relocate})"
        )
        print(f"- Education Level: {interview_details.education_level}")
        print(f"- Intent: {interview_details.intent}")
        print(f"- Domain of Interest: {interview_details.domain_of_interest}\n")
        print()

    interview_details = interviewer.start_conversation()
    print_details(interview_details)
    for _ in range(9):
        print_current_state(interview_details)
        print("[bold cyan][i]You:[/i][/bold cyan] ", end="")
        user_message = input()
        if not user_message.strip():
            break
        interview_details = interviewer.send_message(user_message)
        print_details(interview_details)

    print_current_state(interview_details)
    print("[bold green]Interview completed[/bold green]")
