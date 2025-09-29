from __future__ import annotations

from airdee.config import WeaviateSettings


def test_weaviate_settings_as_kwargs_includes_api_key():
    settings = WeaviateSettings(
        url="https://example.com",
        api_key="secret",
        collection="Articles",
    )

    kwargs = settings.as_kwargs()

    assert kwargs["http_host"] == "https://example.com"
    assert kwargs["auth_credentials"] == {"api_key": "secret"}


def test_weaviate_settings_headers_returns_expected_header():
    settings = WeaviateSettings(
        url="https://example.com",
        api_key="secret",
        collection="Articles",
    )

    assert settings.headers() == {"X-API-Key": "secret"}


def test_weaviate_settings_headers_empty_when_no_key():
    settings = WeaviateSettings(url="https://example.com", collection="Articles")

    assert settings.headers() == {}
