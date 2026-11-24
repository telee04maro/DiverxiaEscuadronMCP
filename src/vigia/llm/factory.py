"""Pick the language model from the settings and the available credentials."""

import os

from vigia.config import Settings
from vigia.llm.base import LanguageModel, OfflineModel
from vigia.llm.claude import ClaudeModel


def build_model(settings: Settings) -> LanguageModel:
    has_credentials = any(
        os.environ.get(name) for name in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")
    )
    if settings.use_ai and has_credentials:
        return ClaudeModel(settings)
    return OfflineModel()
