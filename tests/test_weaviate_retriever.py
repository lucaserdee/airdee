from __future__ import annotations

import pytest

from airdee.config import WeaviateSettings
from airdee.weaviate_retriever import ArticleDocument, WeaviateRetriever


class DummyCollection:
    def __init__(self, response):
        self._response = response

    class Query:
        def __init__(self, response):
            self._response = response

        def fetch_object_by_id(self, _uuid, include_vector):
            return self._response

    @property
    def query(self):
        return DummyCollection.Query(self._response)


class DummyClient:
    def __init__(self, response):
        self._response = response

    class Collections:
        def __init__(self, response):
            self._response = response

        def get(self, name):
            return DummyCollection(self._response)

    @property
    def collections(self):
        return DummyClient.Collections(self._response)


def test_normalise_vector_trims_trailing_metadata():
    response = {
        "properties": {"title": "Test", "body": "Inhoud"},
        "vector": {"te_3_large": [1.0, 2.0, 3.0, 99.0, 98.0]},
    }
    settings = WeaviateSettings(
        url="https://example.com",
        collection="Articles",
        expected_vector_size=3,
        trailing_metadata=2,
    )
    retriever = WeaviateRetriever(DummyClient(response), settings)

    document = retriever.get_article("uuid")

    assert isinstance(document, ArticleDocument)
    assert document.vector == [1.0, 2.0, 3.0]


def test_normalise_vector_raises_on_wrong_length():
    response = {
        "properties": {"title": "Test", "body": "Inhoud"},
        "vector": {"te_3_large": [1.0, 2.0]},
    }
    settings = WeaviateSettings(
        url="https://example.com",
        collection="Articles",
        expected_vector_size=3,
        trailing_metadata=0,
    )
    retriever = WeaviateRetriever(DummyClient(response), settings)

    with pytest.raises(ValueError):
        retriever.get_article("uuid")


def test_normalise_vector_raises_when_trailing_exceeds_length():
    response = {
        "properties": {"title": "Test", "body": "Inhoud"},
        "vector": {"te_3_large": [1.0, 2.0]},
    }
    settings = WeaviateSettings(
        url="https://example.com",
        collection="Articles",
        trailing_metadata=3,
    )
    retriever = WeaviateRetriever(DummyClient(response), settings)

    with pytest.raises(ValueError):
        retriever.get_article("uuid")


def test_extract_vector_from_additional_block():
    response = {
        "properties": {"title": "Test", "body": "Inhoud"},
        "additional": {"vector": {"te_3_large": [1.0, 2.0, 3.0]}},
    }
    settings = WeaviateSettings(
        url="https://example.com",
        collection="Articles",
        trailing_metadata=0,
    )
    retriever = WeaviateRetriever(DummyClient(response), settings)

    document = retriever.get_article("uuid")

    assert document.vector == [1.0, 2.0, 3.0]


def test_extract_vector_from_vectors_block():
    response = {
        "properties": {"title": "Test", "body": "Inhoud"},
        "vectors": {"te_3_large": [5.0, 6.0, 7.0]},
    }
    settings = WeaviateSettings(
        url="https://example.com",
        collection="Articles",
        trailing_metadata=0,
    )
    retriever = WeaviateRetriever(DummyClient(response), settings)

    document = retriever.get_article("uuid")

    assert document.vector == [5.0, 6.0, 7.0]
