import os


class Configuration:
    # Preferences for AWS signed requests (to challenge API)
    AWS_BASE_URL: str
    AWS_REGION: str

    # Preferences for AWS public endpoints
    AWS_PUBLIC_BASE_URL: str

    # Preferences for Mistral API
    MISTRAL_API_KEY: str
    MISTRAL_MODEL_ID: str

    # Preferences for Amazon Bedrock
    BEDROCK_ACCESS_KEY_ID: str
    BEDROCK_SECRET_ACCESS_KEY: str
    BEDROCK_REGION: str
    BEDROCK_MODEL_ID: str

    # Preferences for Azure OpenAI
    AZURE_API_BASE: str
    AZURE_API_KEY: str
    AZURE_API_VERSION: str
    AZURE_DEPLOYMENT_NAME: str

    def __init__(self):
        self.AWS_BASE_URL = os.getenv("AWS_BASE_URL", "")
        if not self.AWS_BASE_URL:
            raise ValueError("AWS_BASE_URL environment variable is not set")
        self.AWS_REGION = os.getenv("AWS_REGION", "")
        if not self.AWS_REGION:
            raise ValueError("AWS_REGION environment variable is not set")

        self.AWS_PUBLIC_BASE_URL = os.getenv("AWS_PUBLIC_BASE_URL", "")
        if not self.AWS_PUBLIC_BASE_URL:
            raise ValueError("AWS_PUBLIC_BASE_URL environment variable is not set")

        self.MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
        if not self.MISTRAL_API_KEY:
            raise ValueError("MISTRAL_API_KEY environment variable is not set")
        self.MISTRAL_MODEL_ID = os.getenv("MISTRAL_MODEL_ID", "")
        if not self.MISTRAL_MODEL_ID:
            raise ValueError("MISTRAL_MODEL_ID environment variable is not set")

        self.BEDROCK_ACCESS_KEY_ID = os.getenv("BEDROCK_ACCESS_KEY_ID", "")
        self.BEDROCK_SECRET_ACCESS_KEY = os.getenv("BEDROCK_SECRET_ACCESS_KEY", "")
        self.BEDROCK_REGION = os.getenv("BEDROCK_REGION", "")
        self.BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "")

        self.AZURE_API_BASE = os.getenv("AZURE_API_BASE", "")
        self.AZURE_API_KEY = os.getenv("AZURE_API_KEY", "")
        self.AZURE_API_VERSION = os.getenv("AZURE_API_VERSION", "")
        self.AZURE_DEPLOYMENT_NAME = os.getenv("AZURE_DEPLOYMENT_NAME", "")

    @property
    def bedrock_configured(self) -> bool:
        return all(
            [
                self.BEDROCK_ACCESS_KEY_ID,
                self.BEDROCK_SECRET_ACCESS_KEY,
                self.BEDROCK_REGION,
                self.BEDROCK_MODEL_ID,
            ]
        )

    @property
    def azure_configured(self) -> bool:
        return all(
            [
                self.AZURE_API_BASE,
                self.AZURE_API_KEY,
                self.AZURE_DEPLOYMENT_NAME,
            ]
        )
