# src/airdee/config.py
"""Configuration models for the Airdee AI toolchain."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict
from urllib.parse import urlparse

@dataclass
class WeaviateSettings:
    url: str                                # e.g. "https://<cluster>.weaviate.cloud"
    api_key: Optional[str] = None
    bearer: Optional[str] = None
    collection: str = "Article"
    expected_vector_size: Optional[int] = None
    trailing_metadata: int = 0

    def _parsed(self):
        p = urlparse(self.url)
        return (p.hostname or self.url, p.port, p.scheme == "https")

    def client_kwargs(self) -> Dict[str, object]:
        host, port, secure = self._parsed()
        kw: Dict[str, object] = {
            "http_host": host, "http_port": port, "http_secure": secure,
            "grpc_host": host, "grpc_port": None, "grpc_secure": secure,
        }
        if self.api_key:
            from weaviate.classes.init import Auth
            kw["auth_credentials"] = Auth.api_key(self.api_key)
        return kw

    def headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.bearer:
            h["Authorization"] = f"Bearer {self.bearer}"
        elif self.api_key:
            h["X-API-KEY"] = self.api_key
        return h

@dataclass
class AzureOpenAISettings:
    endpoint: str
    deployment: str
    api_key: str
    api_version: str = "2024-02-01"

    def headers(self) -> Dict[str, str]:
        return {"api-key": self.api_key, "Content-Type": "application/json"}
