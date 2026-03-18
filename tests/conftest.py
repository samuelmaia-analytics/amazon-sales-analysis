"""Shared pytest configuration lives in pyproject.toml."""

from collections.abc import Iterator

import pytest

from amazon_sales_analysis.config import get_settings


@pytest.fixture(autouse=True)
def reset_settings_cache() -> Iterator[None]:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
