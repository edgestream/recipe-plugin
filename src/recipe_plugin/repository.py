"""Repository access for static Schema.org Recipe documents."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


class RecipeNotFoundError(LookupError):
    """Raised when the mock provider has no recipe for a requested URL."""


class RecipeRepository:
    """Read individual JSON recipe documents and index them by canonical URL."""

    def __init__(self, data_path: Path) -> None:
        self._data_path = data_path

    def get_by_url(self, url: str) -> dict[str, Any]:
        self._validate_url(url)
        for recipe_path in sorted(self._data_path.glob("*.json")):
            recipe = self._read_recipe(recipe_path)
            if recipe.get("url") == url:
                return recipe
        raise RecipeNotFoundError(f"No mock recipe is available for URL: {url}")

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Return recipes whose searchable metadata contains every query term."""
        normalized_query = self._validate_query(query)
        self._validate_limit(limit)
        terms = normalized_query.casefold().split()

        matches = []
        for recipe_path in sorted(self._data_path.glob("*.json")):
            recipe = self._read_recipe(recipe_path)
            searchable_text = " ".join(
                self._text_values(
                    recipe,
                    "name",
                    "description",
                    "recipeCategory",
                    "recipeCuisine",
                    "keywords",
                    "recipeIngredient",
                )
            ).casefold()
            if all(term in searchable_text for term in terms):
                matches.append(recipe)
                if len(matches) == limit:
                    break
        return matches

    @staticmethod
    def _validate_url(url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("url must be an absolute HTTP or HTTPS URL")

    @staticmethod
    def _validate_query(query: str) -> str:
        if not isinstance(query, str) or not (normalized_query := query.strip()):
            raise ValueError("query must be a non-empty string")
        return normalized_query

    @staticmethod
    def _validate_limit(limit: int) -> None:
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be a positive integer")

    @staticmethod
    def _text_values(recipe: dict[str, Any], *fields: str) -> list[str]:
        values: list[str] = []
        for field in fields:
            value = recipe.get(field)
            if isinstance(value, str):
                values.append(value)
            elif isinstance(value, list):
                values.extend(item for item in value if isinstance(item, str))
        return values

    @staticmethod
    def _read_recipe(recipe_path: Path) -> dict[str, Any]:
        with recipe_path.open(encoding="utf-8") as recipe_file:
            recipe = json.load(recipe_file)
        if not isinstance(recipe, dict) or recipe.get("@type") != "Recipe":
            raise ValueError(f"{recipe_path.name} is not a Schema.org Recipe document")
        return recipe
