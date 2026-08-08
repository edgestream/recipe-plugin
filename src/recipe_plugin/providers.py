"""Provider adapters for Recipe MCP."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from .repository import RecipeRepository


class RecipeProvider(Protocol):
    """A recipe source that can resolve one provider URL."""

    def get_recipe(self, url: str) -> dict[str, Any]:
        """Return the Schema.org Recipe document stored for *url*."""

    def search_recipes(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Return recipes matching a free-text query."""


class MockRecipeProvider:
    """Initial adapter backed by static JSON recipe documents."""

    def __init__(self, data_path: Path) -> None:
        self._repository = RecipeRepository(data_path)

    def get_recipe(self, url: str) -> dict[str, Any]:
        return self._repository.get_by_url(url)

    def search_recipes(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        return self._repository.search(query, limit)
