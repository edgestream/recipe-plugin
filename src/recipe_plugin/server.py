"""Recipe MCP server using the Streamable HTTP transport."""

from __future__ import annotations

from importlib.resources import files
import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from .providers import MockRecipeProvider
from .repository import RecipeNotFoundError

provider = MockRecipeProvider(files("recipe_plugin").joinpath("data"))

mcp = FastMCP(
    "recipe-mcp",
    instructions=(
        "Use search_recipes to find recipes by name, description, category, cuisine, "
        "keywords, or ingredients. Use get_recipe when the user supplies a recipe URL. "
        "The server currently contains mock recipes and returns Schema.org Recipe data."
    ),
    host=os.environ.get("RECIPE_MCP_HOST", "127.0.0.1"),
    port=int(os.environ.get("RECIPE_MCP_PORT", "8001")),
    stateless_http=True,
    json_response=True,
)


@mcp.tool(
    name="get_recipe",
    description="Get the structured Schema.org Recipe stored for a recipe URL.",
)
def get_recipe(url: str) -> dict[str, Any]:
    """Return one complete Schema.org Recipe document for *url*."""
    try:
        return provider.get_recipe(url)
    except RecipeNotFoundError as error:
        raise ValueError(str(error)) from error


@mcp.tool(
    name="search_recipes",
    description="Search stored recipes by name, description, category, cuisine, keywords, or ingredients.",
)
def search_recipes(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Return compact recipe search results for a free-text query."""
    recipes = provider.search_recipes(query, limit)
    return [
        {
            "name": recipe.get("name"),
            "description": recipe.get("description"),
            "url": recipe.get("url"),
            "image": recipe.get("image"),
            "recipeCategory": recipe.get("recipeCategory"),
            "recipeCuisine": recipe.get("recipeCuisine"),
        }
        for recipe in recipes
    ]


def main() -> None:
    """Start the MCP server with the Streamable HTTP transport."""
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
