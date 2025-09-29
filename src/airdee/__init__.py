"""Core package for the Airdee EMG AI tooling."""

from .config import WeaviateSettings, AzureOpenAISettings
from .weaviate_retriever import WeaviateRetriever, ArticleDocument
from .ai_agent import ArticleAnsweringAgent

__all__ = [
    "WeaviateSettings",
    "AzureOpenAISettings",
    "WeaviateRetriever",
    "ArticleDocument",
    "ArticleAnsweringAgent",
]
