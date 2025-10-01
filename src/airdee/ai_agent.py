"""High level orchestration of the EMG article answering workflow."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable, Mapping
from urllib import error, request

from .config import AzureOpenAISettings

DEFAULT_SYSTEM_PROMPT = (
    "Je bent een behulpzame redacteur voor de Erdee Media Groep. "
    "Beantwoord vragen uitsluitend op basis van de aangeleverde bronnen."
)


@dataclass(slots=True)
class AgentPrompt:
    """Representation of the prompt that will be sent to Azure OpenAI."""

    question: str
    system: str = DEFAULT_SYSTEM_PROMPT

    def to_payload(self, document: Mapping[str, object]) -> dict[str, object]:
        """Return the chat completion payload for a retrieved article dict."""
        content = self._format_context(document)
        return {
            "messages": [
                {"role": "system", "content": self.system},
                {"role": "user", "content": f"Vraag: {self.question}\n\n{content}"},
            ]
        }

    @staticmethod
    def _format_context(document: Mapping[str, object]) -> str:
        title = str(document.get("title", "") or "")
        body = str(document.get("body", "") or "")
        published_at = str(document.get("publishedAt", "") or "")
        rd_id = str(document.get("rdId", "") or "")
        parts = [
            "Context:",
            f"Titel: {title}",
            f"Publicatiedatum: {published_at}",
            f"rdId: {rd_id}",
            f"Inhoud: {body}",
        ]
        return "\n".join(parts)


class ArticleAnsweringAgent:
    """Wrapper around Azure OpenAI chat completions for EMG articles."""

    def __init__(self, settings: AzureOpenAISettings) -> None:
        self._settings = settings

    def answer(self, prompt: AgentPrompt, document: Mapping[str, object]) -> str:
        """Return the answer for `prompt` given a document dict."""
        payload = prompt.to_payload(document)
        response = self._post(payload)
        return self._extract_answer(response)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _post(self, payload: dict[str, object]) -> dict[str, object]:
        url = (
            f"{self._settings.endpoint}/openai/deployments/"
            f"{self._settings.deployment}/chat/completions"
            f"?api-version={self._settings.api_version}"
        )
        data = json.dumps(payload).encode("utf-8")
        headers = self._settings.headers()
        req = request.Request(url, data=data, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8")
        except error.HTTPError as exc:  # pragma: no cover
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
