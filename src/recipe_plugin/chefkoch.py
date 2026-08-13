"""Anonymous, read-only access to public Chefkoch recipe pages."""

from __future__ import annotations

from urllib.parse import quote, urlparse

import aiohttp

from .models import Recipe, RecipeCandidate
from .normalize import normalize_recipe
from .recipe_jsonld import RecipeNotFoundError, _JsonLdScriptParser, decode_nuxt_payload, extract_recipe_jsonld

SEARCH_URL = "https://www.chefkoch.de/rs/s0/{query}/Rezepte.html"
SEARCH_IMAGE_FORMAT = "crop-960x540"


class ChallengeRequiredError(RuntimeError):
    """Raised when Chefkoch requires an interactive browser challenge."""


class RateLimitedError(RuntimeError):
    """Raised when Chefkoch rejects the shared upstream IP temporarily."""

    def __init__(self, retry_after: str | None = None) -> None:
        self.retry_after = retry_after
        super().__init__("Chefkoch rate-limited this service's upstream IP.")


class ChefkochClient:
    """Fetches public recipe data without credentials or persisted state."""

    async def get_recipe(self, recipe_url: str) -> Recipe:
        _validate_chefkoch_url(recipe_url)
        async with self._new_session() as session:
            html, final_url = await self._get_html(session, recipe_url)
        try:
            return normalize_recipe(extract_recipe_jsonld(html), final_url)
        except RecipeNotFoundError as exc:
            raise RecipeNotFoundError("Recipe details were not found in the response.") from exc

    async def search_recipes(self, query: str, limit: int = 10) -> list[RecipeCandidate]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must not be empty.")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 20:
            raise ValueError("limit must be between 1 and 20.")
        async with self._new_session() as session:
            html, _ = await self._get_html(session, SEARCH_URL.format(query=quote(query.strip(), safe="")))
        return _extract_candidates(html)[:limit]

    def _new_session(self) -> aiohttp.ClientSession:
        return aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30), headers={"Accept-Language": "de-DE,de;q=0.9"})

    async def _get_html(self, session: aiohttp.ClientSession, url: str) -> tuple[str, str]:
        for attempt in range(2):
            try:
                async with session.get(url, allow_redirects=True) as response:
                    html = await response.text()
                    _raise_if_challenged(html)
                    if response.status == 429:
                        raise RateLimitedError(response.headers.get("Retry-After"))
                    if response.status >= 500 and attempt == 0:
                        continue
                    if response.status != 200:
                        raise RuntimeError(f"Chefkoch returned HTTP {response.status}.")
                    return html, str(response.url)
            except aiohttp.ClientError:
                if attempt:
                    raise RuntimeError("Chefkoch could not be reached.") from None
        raise RuntimeError("Chefkoch could not be reached.")


def _validate_chefkoch_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in {"www.chefkoch.de", "chefkoch.de"}:
        raise ValueError("Only HTTPS URLs on chefkoch.de are allowed.")


def _raise_if_challenged(html: str) -> None:
    if "client challenge" in html.lower() or "javascript is disabled" in html.lower():
        raise ChallengeRequiredError("Chefkoch requires an interactive client challenge.")


def _extract_candidates(html: str) -> list[RecipeCandidate]:
    parser = _JsonLdScriptParser()
    parser.feed(html)
    candidates, seen = [], set()
    for record in _walk_dicts(decode_nuxt_payload(parser.nuxt_payload)):
        title = record.get("title") or record.get("name")
        url = record.get("siteUrl") or record.get("url") or record.get("canonicalUrl") or record.get("seoUrl")
        if not isinstance(title, str) or not isinstance(url, str):
            continue
        url = "https://www.chefkoch.de" + url if url.startswith("/") else url
        try:
            _validate_chefkoch_url(url)
        except ValueError:
            continue
        if url not in seen:
            seen.add(url)
            candidates.append(
                RecipeCandidate(
                    str(record["id"]) if record.get("id") is not None else None,
                    title,
                    url,
                    _candidate_description(record),
                    _candidate_image(record),
                    record.get("isPlus") is True,
                )
            )
    return candidates


def _walk_dicts(value: object):
    if isinstance(value, dict):
        yield value
        for child in value.values(): yield from _walk_dicts(child)
    elif isinstance(value, list):
        for child in value: yield from _walk_dicts(child)


def _candidate_description(record: dict[str, object]) -> str | None:
    for key in ("description", "subtitle"):
        value = record.get(key)
        if isinstance(value, str) and (text := value.strip()):
            return text
    return None


def _candidate_image(record: dict[str, object]) -> str | None:
    image = record.get("image") or record.get("imageUrl")
    if isinstance(image, str):
        return image
    if isinstance(image, dict) and isinstance(image.get("url"), str):
        return image["url"]
    template = record.get("previewImageUrlTemplate")
    if isinstance(template, str) and template.strip():
        return template.replace("<format>", SEARCH_IMAGE_FORMAT)
    return None
