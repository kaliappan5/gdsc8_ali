import boto3

from alina.shared.config import Configuration

configuration = Configuration()


def _get_client():
    """Create and return a boto3 Bedrock client."""
    if not configuration.bedrock_configured:
        raise ValueError("Amazon Bedrock is not properly configured.")
    return boto3.client(
        "bedrock",
        region_name=configuration.BEDROCK_REGION,
        aws_access_key_id=configuration.BEDROCK_ACCESS_KEY_ID,
        aws_secret_access_key=configuration.BEDROCK_SECRET_ACCESS_KEY,
    )


def get_models():
    """Retrieve available models from Amazon Bedrock."""
    bedrock_client = _get_client()
    inference_profiles = bedrock_client.list_inference_profiles()
    summaries = inference_profiles.get("inferenceProfileSummaries", [])
    return [model["inferenceProfileId"] for model in summaries] if summaries else []
