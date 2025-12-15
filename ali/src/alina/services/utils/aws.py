import json
from typing import Any, Optional

import boto3
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

from ...shared.config import Configuration

configuration = Configuration()


def aws_signed_request(
    path: str,
    method: str,
    payload: Optional[Any] = None,
) -> Optional[requests.Response]:
    """Make a SigV4 signed request to the challenge API.

    Lean error handling: raises RuntimeError on failure.

    Args:
        path: API path segment (e.g. "chat", "submit", "health")
        method: HTTP verb (GET/POST)
        payload: dict / list / JSON-string / None

    Returns:
        Response object
    """
    # Normalize payload into raw JSON string (boto3 signing sends raw body)
    body = None
    if payload is not None:
        try:
            if isinstance(payload, (dict, list)):
                body = json.dumps(payload)
            elif isinstance(payload, (str, bytes)):
                body = payload if isinstance(payload, str) else payload.decode("utf-8")
            else:  # Fallback attempt json serialization
                body = json.dumps(payload)
        except Exception as e:  # pragma: no cover
            raise RuntimeError(f"Failed to serialize payload for path '{path}'") from e

    try:
        session = boto3.Session(region_name=configuration.AWS_REGION)
        credentials = session.get_credentials()
        if not credentials:
            raise RuntimeError(
                "AWS credentials not found (configure with aws configure)"
            )

        headers = {"Content-Type": "application/json"}
        request = AWSRequest(
            url=f"{configuration.AWS_BASE_URL.rstrip('/')}/{path}",
            method=method.upper(),
            data=body,
            headers=headers,
        )
        SigV4Auth(credentials, "execute-api", configuration.AWS_REGION).add_auth(
            request
        )

        try:
            response = requests.request(
                method=str(request.method),
                url=str(request.url),
                headers=dict(request.headers),
                data=request.body,
            )
        except requests.RequestException as e:
            raise RuntimeError(f"Network error during request to '{path}'") from e

        if response.status_code == 200:
            return response
        raise RuntimeError(
            f"API call '{path}' failed: status={response.status_code} body={response.text[:300]}"
        )

    except Exception as e:
        raise RuntimeError(f"Unexpected error during signed request to '{path}'") from e
