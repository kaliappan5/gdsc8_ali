from strands import Agent
from strands.agent.conversation_manager import NullConversationManager
from strands.types.content import ContentBlock, Message

from alina.services.chat.base.interview import BaseInterviewer, InterviewDetails
from alina.services.utils.ai import AIProvider, get_ai_manager
from alina.shared.database import read_jobs_analysis, read_skills


class BaseAIInterviewer(BaseInterviewer):
    max_messages_per_person: int
    ai_provider: AIProvider
    max_messages_per_person: int
    system_prompt: str

    def __init__(
        self,
        ai_provider: AIProvider,
        max_messages_per_person: int = 10,
    ):
        super().__init__()
        self.ai_provider = ai_provider
        self.max_messages_per_person = max_messages_per_person

    def _initialize_agent(self, system_prompt: str) -> Agent:
        ai_manager = get_ai_manager(self.ai_provider)
        agent = ai_manager.build_agent(system_prompt=system_prompt)
        agent.conversation_manager = NullConversationManager()
        return agent

    def _start_conversation(self, agent: Agent) -> InterviewDetails:
        interview_details = agent.structured_output(
            output_model=InterviewDetails,
            prompt="Your first message is the prompt, to give your name, greet the person and ask for their information.",
        )
        self._append_assistant_message(agent, interview_details)
        return interview_details

    def _append_assistant_message(
        self, agent: Agent, interview_details: InterviewDetails
    ):
        if interview_details.next_message:
            agent.messages.append(
                Message(
                    role="user",
                    content=[
                        ContentBlock(text="Alina assistant said:"),
                        ContentBlock(text=interview_details.next_message),
                    ],
                )
            )

    def _send_message(self, agent: Agent, message: str) -> InterviewDetails:
        self._append_user_message(agent, message)
        remaining_messages = max(
            0, self.max_messages_per_person - len(agent.messages) // 2
        )
        if remaining_messages == 0:
            prompt = "You have reached the maximum number of messages allowed. Politely inform the person that the interview is complete and that you will send them the list of results (jobs and/or trainings)."
        else:
            prompt = f"You have {remaining_messages} messages left to collect the required information, what is your next message?"

        interview_details = agent.structured_output(
            output_model=InterviewDetails,
            prompt=prompt,
        )
        print(interview_details.model_dump())
        if (
            interview_details.confidence_in_age is not None
            and interview_details.confidence_in_age <= 5
        ) or (
            interview_details.age is not None
            and interview_details.age > 16
            and interview_details.education_level is not None
            and interview_details.education_level <= 2
        ):
            # If confidence in age is low, ask for clarification
            clarification_prompt = "We have low confidence in the reported age. Please ask a follow-up question to clarify and verify the interviewee's age."
            clarification_details = agent.structured_output(
                output_model=InterviewDetails,
                prompt=clarification_prompt,
            )
            if clarification_details.next_message:
                interview_details.next_message = clarification_details.next_message
        self._append_assistant_message(agent, interview_details)
        return interview_details

    def _append_user_message(self, agent: Agent, message: str):
        agent.messages.append(
            Message(
                role="user",
                content=[ContentBlock(text="User said:"), ContentBlock(text=message)],
            )
        )


class InitialAIInterviewer(BaseAIInterviewer):
    welcome_agent: Agent

    def __init__(self, ai_provider: AIProvider, max_messages_per_person: int = 10):
        super().__init__(ai_provider, max_messages_per_person)
        self.welcome_agent = self._initialize_agent(
            system_prompt="""
            DESCRIPTION:
                You are a front desk agent responsible for directing people to the appropriate service.
                Your role is to identify basic information about the person in order to pass it on to specialized agents.
                These individuals reside in Brazil and are seeking employment, training, or information.
                Your name is Alina.
                If the person gives you information that is not relevant to your role, politely steer the conversation back to collecting the required information.
                The people you assist may be of any educational level and any age, but if the person is under 16 years old, you must politely inform them that you cannot assist them further due to age restrictions.
            
            ROLE:
                You have to collect the following information:
                - Age
                - City of residence and ability to relocate
                - Educational level
                - Intent: seeking employment, training, or information
                - Domain of interest
                - Years of experience in the domain of interest
                - Skills and proficiency levels (if applicable)
            
            RULES:
                You must be polite and considerate.
                All your message should be short and consise: no Markdown, no bullet points, no lists. Just a short paragraph of maximum 3 sentences.
                Do not mention the list of information you need to collect; just ask targeted questions to get specific information quickly.
                Do not provide job recommendations yet.
                You must always respond in English.
            """
        )

    def start_conversation(self) -> InterviewDetails:
        return super()._start_conversation(self.welcome_agent)

    def send_message(self, message: str) -> InterviewDetails:
        return super()._send_message(self.welcome_agent, message)


class TrainingAIInterviewer(BaseAIInterviewer):
    welcome_agent: Agent

    def __init__(
        self, ai_provider: AIProvider, summary: str, max_messages_per_person: int = 10
    ):
        super().__init__(ai_provider, max_messages_per_person)
        skills = read_skills()
        skills_prompt = "\n".join(
            f" - {skill.name} (e.g. for jobs: {skill.jobs})" for skill in skills
        )

        self.welcome_agent = self._initialize_agent(
            system_prompt=f"""
            DESCRIPTION:
                You are a training-focused front desk agent responsible for directing people to the appropriate service.
                Your role is to identify which skills the person wants to develop in order to recommend suitable training programs.
                Your name is Alina.
                If the person gives you information that is not relevant to your role, politely steer the conversation back to collecting the required information.
                At the end of the interview, after {max_messages_per_person} messages, you have to know all the skills the person has, and the skills they want to develop.
            SKILLS LIST:
                {skills_prompt}
            PREVIOUS INTERVIEW SUMMARY:
                {summary}
            RULES:
                You must be polite and considerate.
                All your message should be short and consise: no Markdown, no bullet points, no lists. Just a short paragraph of maximum 3 sentences.
                Do not mention the list of information you need to collect; just ask targeted questions to get specific information quickly.
                Do not provide job recommendations yet.
                You must always respond in English.
            """
        )

    def start_conversation(self) -> InterviewDetails:
        return super()._start_conversation(self.welcome_agent)

    def send_message(self, message: str) -> InterviewDetails:
        return super()._send_message(self.welcome_agent, message)


class JobAIInterviewer(BaseAIInterviewer):
    welcome_agent: Agent

    def __init__(
        self, ai_provider: AIProvider, summary: str, max_messages_per_person: int = 10
    ):
        super().__init__(ai_provider, max_messages_per_person)
        skills = read_skills()
        skills_prompt = "\n".join(
            f" - {skill.name} (e.g. for jobs: {skill.jobs})" for skill in skills
        )

        jobs = read_jobs_analysis()
        jobs_prompt = "\n".join(f" - {job.description}" for job in jobs)

        self.welcome_agent = self._initialize_agent(
            system_prompt=f"""
            DESCRIPTION:
                You are a training-focused front desk agent responsible for directing people to the appropriate service.
                Your role is to identify which jobs the person is interested in and their skills in order to recommend suitable job opportunities.
                Your name is Alina.
                If the person gives you information that is not relevant to your role, politely steer the conversation back to collecting the required information.
                At the end of the interview, after {max_messages_per_person} messages, you have to know:
                    - all jobs the person is interested in
                    - all the skills the person has
                    - the skills they want to develop
            SKILLS LIST:
                {skills_prompt}
            JOBS LIST:
                {jobs_prompt}
            PREVIOUS INTERVIEW SUMMARY:
                {summary}
            RULES:
                You must be polite and considerate.
                All your message should be short and consise: no Markdown, no bullet points, no lists. Just a short paragraph of maximum 3 sentences.
                Do not mention the list of information you need to collect; just ask targeted questions to get specific information quickly.
                Do not provide job recommendations yet.
                You must always respond in English.
            """
        )

    def start_conversation(self) -> InterviewDetails:
        return super()._start_conversation(self.welcome_agent)

    def send_message(self, message: str) -> InterviewDetails:
        return super()._send_message(self.welcome_agent, message)


class FullAIInterviewer(BaseAIInterviewer):
    welcome_agent: Agent

    def __init__(self, ai_provider: AIProvider, max_messages_per_person: int = 10):
        super().__init__(ai_provider, max_messages_per_person)
        skills = read_skills()
        skills_prompt = "\n".join(
            f" - {skill.name} (e.g. for jobs: {skill.jobs})" for skill in skills
        )

        jobs = read_jobs_analysis()
        jobs_prompt = "\n".join(f" - {job.description}" for job in jobs)
        self.welcome_agent = self._initialize_agent(
            system_prompt=f"""
            DESCRIPTION:
                You are a front desk agent responsible for directing people to the appropriate service.
                Your role is to identify basic information about the person in order to pass it on to specialized agents.
                These individuals reside in Brazil and are seeking employment, training, or information.
                Your name is Alina.
                If the person gives you information that is not relevant to your role, politely steer the conversation back to collecting the required information.
                The people you assist may be of any educational level and any age, but if the person is under 16 years old, you must politely inform them that you cannot assist them further due to age restrictions.
                At the end of the interview, after {max_messages_per_person} messages, you have to know:
                    - all jobs the person is interested in
                    - all the skills the person has
                    - the skills they want to develop
            ROLE:
                You have to collect the following information (ideally in this order or as close as possible):
                - Age
                - City of residence and ability to relocate
                - Educational level
                - Intent: seeking employment, training, or information
                - Domain of interest
                - Years of experience in the domain of interest
                - Skills and proficiency levels (if applicable)
            SKILLS LIST:
                {skills_prompt}
            JOBS LIST:
                {jobs_prompt}
            RULES:
                You must be polite and considerate.
                All your message should be short and consise: no Markdown, no bullet points, no lists. Just a short paragraph of maximum 3 sentences.
                Do not mention the list of information you need to collect; just ask targeted questions to get specific information quickly.
                Do not provide job recommendations yet.
                You must always respond in English.
            ADDITIONAL CHECKS:
                If the person claims to be older than 16 years old, it's hard to believe they are still in school, especially in ensino fundametal.
                If in doubt about the authenticity of the information provided (e.g., age, experience, skills), ask follow-up questions to clarify and verify the details.
            """
        )

    def start_conversation(self) -> InterviewDetails:
        return super()._start_conversation(self.welcome_agent)

    def send_message(self, message: str) -> InterviewDetails:
        return super()._send_message(self.welcome_agent, message)
