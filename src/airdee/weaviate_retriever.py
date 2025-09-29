"""Utilities for interacting with the Weaviate vector database."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from .config import WeaviateSettings

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class ArticleDocument:
    """Container for an article retrieved from Weaviate."""

    uuid: str
    title: str
    body: str
    vector: Sequence[float]


class WeaviateRetriever:
    """High level helper to fetch article content and vectors from Weaviate."""

    def __init__(
        self,
        client: Any,
        settings: WeaviateSettings,
        vector_property: str = "te_3_large",
    ) -> None:
        self._client = client
        self._settings = settings
        self._vector_property = vector_property

    def get_article(self, article_uuid: str) -> ArticleDocument:
        """Return an :class:`ArticleDocument` for ``article_uuid``.

        The method normalises the stored vector by trimming metadata the
        importer appended to the tail of the vector.  The amount of metadata to
        remove can be configured with ``settings.trailing_metadata``.  If the
        ``settings.expected_vector_size`` is defined and the fetched vector does
        not match the expectation an informative :class:`ValueError` is raised.
        """

        collection = self._get_collection(self._settings.collection)
        response = collection.query.fetch_object_by_id(
            article_uuid,
            include_vector=True,
        )
        if response is None:
            msg = f"Article with UUID {article_uuid!r} was not found."
            LOGGER.error(msg)
            raise LookupError(msg)

        properties = self._extract_properties(response)
        vector = self._extract_vector(response)
        normalised = self._normalise_vector(vector)

        return ArticleDocument(
            uuid=article_uuid,
            title=str(properties.get("title", "")),
            body=str(properties.get("body", "")),
            vector=normalised,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _get_collection(self, name: str) -> Any:
        """Return the collection handle from the client, raising on failure."""

        if not hasattr(self._client, "collections"):
            msg = "Weaviate client does not expose a 'collections' attribute."
            raise AttributeError(msg)
        return self._client.collections.get(name)

    @staticmethod
    def _extract_properties(response: Mapping[str, Any]) -> Mapping[str, Any]:
        """Return the ``properties`` section of the fetch response."""

        properties = response.get("properties")
        if not isinstance(properties, Mapping):
            msg = "Response does not contain a property map."
            raise TypeError(msg)
        return properties

    def _extract_vector(self, response: Mapping[str, Any]) -> Sequence[float]:
        """Return the vector associated with ``self._vector_property``."""

        vector_maps: list[Mapping[str, Any]] = []

        direct = response.get("vector")
        if isinstance(direct, Mapping):
            vector_maps.append(direct)

        vectors = response.get("vectors")
        if isinstance(vectors, Mapping):
            vector_maps.append(vectors)

        additional = response.get("additional")
        if isinstance(additional, Mapping):
            additional_vector = additional.get("vector")
            if isinstance(additional_vector, Mapping):
                vector_maps.append(additional_vector)

        for mapping in vector_maps:
            data = mapping.get(self._vector_property)
            if isinstance(data, Iterable):
                return list(float(v) for v in data)  # type: ignore[arg-type]

        msg = f"Vector property {self._vector_property!r} is missing."
        raise KeyError(msg)

    def _normalise_vector(self, vector: Sequence[float]) -> Sequence[float]:
        """Trim trailing metadata and validate the vector length."""

        expected = self._settings.expected_vector_size
        trailing = self._settings.trailing_metadata
        trimmed = list(vector)
        if trailing:
            if len(trimmed) <= trailing:
                msg = (
                    "Vector bevat minder waarden (%s) dan het aantal "
                    "te verwijderen metadata (%s)."
                    % (len(trimmed), trailing)
                )
                LOGGER.error(msg)
                raise ValueError(msg)
            trimmed = trimmed[:-trailing]

        if expected is None:
            return trimmed

        if len(trimmed) == expected:
            return trimmed

        if len(vector) == expected:
            return list(vector)

        msg = (
            "Vector length mismatch: expected %s values but received %s."
            % (expected, len(vector))
        )
        LOGGER.error(msg)
        raise ValueError(msg)


__all__ = ["WeaviateRetriever", "ArticleDocument"]
