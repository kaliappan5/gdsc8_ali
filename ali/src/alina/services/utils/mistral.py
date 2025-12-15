from datetime import datetime, timedelta, timezone
from typing import Sequence

from mistralai import Mistral

from alina.shared.config import Configuration

api_key = Configuration().MISTRAL_API_KEY


def _is_deprecated_soon(model) -> bool:
    if not model.deprecation:
        return False
    # model.deprecation is a datetime object
    # Check if the deprecation date is within the next 30 days

    return model.deprecation <= datetime.now(tz=timezone.utc) + timedelta(days=30)


def list_models() -> Sequence[str]:
    models = Mistral(api_key=api_key).models.list()
    return (
        [m.id for m in models.data if m.name and not _is_deprecated_soon(m)]
        if models.data
        else []
    )
