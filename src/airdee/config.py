"""Configuration models for the Airdee AI toolchain."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class WeaviateSettings:
    """Configuration required to talk to the Weaviate vector database."""

    url: str
    api_key: Optional[str] = None
    collection: str = "Articles"
    expected_vector_size: Optional[int] = None
    trailing_metadata: int = 0

    def as_kwargs(self) -> dict[str, object]:
        """Return keyword arguments for :func:`weaviate.connect_to_weaviate`."""

        data: dict[str, object] = {"http_host": self.url}
        if self.api_key:
            data["auth_credentials"] = {"api_key": self.api_key}
        return data

    def headers(self) -> dict[str, str]:
        """Return HTTP headers for direct REST calls to Weaviate."""

        if not self.api_key:
            return {}
        return {"X-API-Key": self.api_key}


@dataclass
class AzureOpenAISettings:
    """Azure OpenAI configuration used by the article answering agent."""

    endpoint: str
    deployment: str
    api_key: str
    api_version: str = "2024-02-01"

    def headers(self) -> dict[str, str]:
        """Return the HTTP headers required for Azure OpenAI requests."""

        return {
            "api-key": self.api_key,
            "Content-Type": "application/json",
        }
