"""High level orchestration of the EMG article answering workflow."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable
from urllib import error, request

from .config import AzureOpenAISettings
from .weaviate_retriever import ArticleDocument

DEFAULT_SYSTEM_PROMPT = (
    "Je bent een behulpzame redacteur voor de Erdee Media Groep. Beantwoord "
    "vragen uitsluitend op basis van de aangeleverde bronnen."
)


@dataclass(slots=True)
class AgentPrompt:
    """Representation of the prompt that will be sent to Azure OpenAI."""

    question: str
    system: str = DEFAULT_SYSTEM_PROMPT

    def to_payload(self, document: ArticleDocument) -> dict[str, object]:
        """Return the chat completion payload for the ``document``."""

        content = self._format_context(document)
        return {
            "messages": [
                {"role": "system", "content": self.system},
                {"role": "user", "content": f"Vraag: {self.question}\n\n{content}"},
            ]
        }

    @staticmethod
    def _format_context(document: ArticleDocument) -> str:
        return (
            "Context:\n"
            f"Titel: {document.title}\n"
            f"Inhoud: {document.body}\n"
        )


class ArticleAnsweringAgent:
    """Wrapper around Azure OpenAI chat completions for EMG articles."""

    def __init__(self, settings: AzureOpenAISettings) -> None:
        self._settings = settings

    def answer(self, prompt: AgentPrompt, document: ArticleDocument) -> str:
        """Return the answer for ``prompt`` given ``document``."""

        payload = prompt.to_payload(document)
        response = self._post(payload)
        return self._extract_answer(response)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _post(self, payload: dict[str, object]) -> dict[str, object]:
        url = f"{self._settings.endpoint}/openai/deployments/{self._settings.deployment}/chat/completions?api-version={self._settings.api_version}"
        data = json.dumps(payload).encode("utf-8")
        headers = self._settings.headers()
        req = request.Request(url, data=data, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8")
        except error.HTTPError as exc:  # pragma: no cover - requires live HTTP
            raise RuntimeError(f"Azure OpenAI request failed: {exc}") from exc
        return json.loads(body)

    @staticmethod
    def _extract_answer(response: dict[str, object]) -> str:
        choices = response.get("choices", [])
        if not isinstance(choices, Iterable):  # type: ignore[arg-type]
            return ""
        for choice in choices:
            if not isinstance(choice, dict):
                continue
            message = choice.get("message")
            if isinstance(message, dict) and isinstance(message.get("content"), str):
                return message["content"].strip()
        return ""


__all__ = ["ArticleAnsweringAgent", "AgentPrompt", "DEFAULT_SYSTEM_PROMPT"]
