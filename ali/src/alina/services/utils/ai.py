from abc import ABC, abstractmethod
from enum import Enum

import boto3
from botocore.config import Config as BotocoreConfig
from strands import Agent
from strands.models import BedrockModel
from strands.models.mistral import MistralModel
from strands.models.model import Model
from strands.models.openai import OpenAIModel

from alina.shared.config import Configuration


class AIProvider(Enum):
    BEDROCK = "bedrock"
    MISTRAL = "mistral"
    AZURE = "azure"


class AIManager(ABC):
    def build_agent(self, system_prompt: str) -> Agent:
        return Agent(
            model=self._build_model(),
            system_prompt=system_prompt,
            callback_handler=None,
        )

    @abstractmethod
    def _build_model(self) -> Model:
        pass


class _BedrockAIManager(AIManager):
    def _build_model(self) -> Model:
        configuration = Configuration()
        session = boto3.Session(
            region_name=configuration.BEDROCK_REGION,
            aws_access_key_id=configuration.BEDROCK_ACCESS_KEY_ID,
            aws_secret_access_key=configuration.BEDROCK_SECRET_ACCESS_KEY,
        )
        boto_client_config = BotocoreConfig(
            read_timeout=120,
            connect_timeout=120,
            max_pool_connections=10,
            retries={"max_attempts": 2},
        )
        return BedrockModel(
            boto_session=session,
            boto_client_config=boto_client_config,
            model_id=configuration.BEDROCK_MODEL_ID,
            streaming=False,
            max_tokens=1000,
            cache_prompt="default",
            cache_tools="default",
        )


class _MistralAIManager(AIManager):
    def _build_model(self) -> Model:
        configuration = Configuration()

        return MistralModel(
            api_key=configuration.MISTRAL_API_KEY,
            model_id=configuration.MISTRAL_MODEL_ID,
            max_tokens=2000,
            stream=False,
            client_args={"timeout_ms": 120_000},
        )


class _AzureAIManager(AIManager):
    def _build_model(self) -> Model:
        configuration = Configuration()

        base_url = f"{configuration.AZURE_API_BASE.rstrip('/')}/openai/deployments/{configuration.AZURE_DEPLOYMENT_NAME}/"
        return OpenAIModel(
            model_id=configuration.AZURE_DEPLOYMENT_NAME,
            client_args={
                "base_url": base_url,
                "api_key": configuration.AZURE_API_KEY,
                "default_query": {"api-version": configuration.AZURE_API_VERSION},
                "timeout": 120,
            },
            params={
                "max_tokens": 1000,
            },
        )


def get_ai_manager(name: AIProvider) -> AIManager:
    if name == AIProvider.BEDROCK:
        return _BedrockAIManager()
    elif name == AIProvider.MISTRAL:
        return _MistralAIManager()
    elif name == AIProvider.AZURE:
        return _AzureAIManager()
    else:
        raise ValueError(f"Unknown AI Manager: {name}")
