"""Recipe MCP server using the Streamable HTTP transport."""

from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from .chefkoch import ChallengeRequiredError, ChefkochClient
from .recipe_jsonld import RecipeNotFoundError

mcp = FastMCP(
    "recipe-mcp",
    instructions=(
        "Use search_recipes to find recipes and get_recipe when the user supplies a "
        "recipe URL. Both tools only access publicly available data "
        "and never require or use credentials."
    ),
    host=os.environ.get("RECIPE_MCP_HOST", "127.0.0.1"),
    port=int(os.environ.get("RECIPE_MCP_PORT", "8001")),
    stateless_http=True,
    json_response=True,
)

READ_ONLY_TOOL = ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=True)


def _error(exc: Exception) -> dict[str, str]:
    if isinstance(exc, RecipeNotFoundError):
        return {"outcome": "recipe_not_found", "message": "Recipe details were not found."}
    if isinstance(exc, ChallengeRequiredError):
        return {"outcome": "challenge_required", "message": "Chefkoch requires an interactive client challenge."}
    if isinstance(exc, ValueError):
        return {"outcome": "invalid_request", "message": str(exc)}
    return {"outcome": "upstream_error", "message": "Chefkoch could not complete the request."}


@mcp.tool(name="get_recipe", description="Fetch and normalize one public recipe URL.", annotations=READ_ONLY_TOOL)
async def get_recipe(url: str) -> dict[str, Any]:
    """Fetch one public recipe without authentication."""
    try:
        return {"outcome": "success", "recipe": (await ChefkochClient().get_recipe(url)).to_dict()}
    except Exception as exc:
        return _error(exc)


@mcp.tool(name="search_recipes", description="Search publicly available recipes.", annotations=READ_ONLY_TOOL)
async def search_recipes(query: str, limit: int = 10) -> dict[str, object]:
    """Search public recipes matching a free-text query."""
    try:
        recipes = await ChefkochClient().search_recipes(query, limit)
        return {"outcome": "success", "recipes": [recipe.to_dict() for recipe in recipes]}
    except Exception as exc:
        return _error(exc)


def main() -> None:
    """Start the MCP server with the Streamable HTTP transport."""
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
