from pathlib import Path

import pytest

from recipe_plugin.repository import RecipeNotFoundError, RecipeRepository


DATA_PATH = Path(__file__).parents[1] / "src" / "recipe_plugin" / "data"


def test_returns_recipe_matching_url() -> None:
    recipe = RecipeRepository(DATA_PATH).get_by_url(
        "https://recipes.example.test/mock/classic-pancakes"
    )

    assert recipe["@context"] == "https://schema.org"
    assert recipe["@type"] == "Recipe"
    assert recipe["name"] == "Classic Pancakes"


def test_rejects_unknown_recipe_url() -> None:
    with pytest.raises(RecipeNotFoundError):
        RecipeRepository(DATA_PATH).get_by_url("https://example.test/no-recipe")


def test_rejects_non_http_url() -> None:
    with pytest.raises(ValueError, match="absolute HTTP"):
        RecipeRepository(DATA_PATH).get_by_url("file:///recipe.json")


def test_searches_recipe_metadata_case_insensitively() -> None:
    recipes = RecipeRepository(DATA_PATH).search("BREAKFAST fluffy")

    assert [recipe["name"] for recipe in recipes] == ["Classic Pancakes"]


def test_searches_recipe_ingredients_and_respects_limit() -> None:
    recipes = RecipeRepository(DATA_PATH).search("melted butter", limit=1)

    assert len(recipes) == 1
    assert recipes[0]["url"] == "https://recipes.example.test/mock/classic-pancakes"


@pytest.mark.parametrize("query", ["", "   ", None])
def test_rejects_empty_search_query(query: object) -> None:
    with pytest.raises(ValueError, match="non-empty"):
        RecipeRepository(DATA_PATH).search(query)  # type: ignore[arg-type]


@pytest.mark.parametrize("limit", [0, -1, True, "1"])
def test_rejects_invalid_search_limit(limit: object) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        RecipeRepository(DATA_PATH).search("pancakes", limit)  # type: ignore[arg-type]
