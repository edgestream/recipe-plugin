"""Normalize Chefkoch JSON-LD and Nuxt recipe data."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Iterable

from .models import Ingredient, Recipe

_QUANTITY = re.compile(r"^(?P<quantity>\d+(?:[.,]\d+)?(?:\s*/\s*\d+)?|[½¼¾⅓⅔])\s*(?P<rest>.*)$")
_UNITS = {"g", "kg", "ml", "l", "el", "tl", "prise", "prisen", "stk", "stück", "scheibe", "scheiben", "dose", "dosen", "bund", "zehe", "zehen", "becher", "packung", "päckchen"}


def normalize_recipe(raw: dict[str, Any], source_url: str) -> Recipe:
    is_jsonld = "@type" in raw or "recipeIngredient" in raw
    title = _text(raw.get("name") if is_jsonld else raw.get("title")) or "Untitled recipe"
    recipe_id = _text(raw.get("identifier") if is_jsonld else raw.get("id")) or source_url.rstrip("/").split("/")[-1].split(".")[0]
    return Recipe(
        source="chefkoch", source_url=source_url, recipe_id=recipe_id, title=title,
        description=_text(raw.get("description") or raw.get("subtitle")),
        is_plus=bool(raw.get("isPlus")) if not is_jsonld else bool(raw.get("isPlus") or raw.get("isAccessibleForFree") is False),
        editorial={key: raw[key] for key in ("author", "publisher", "source", "isPlus") if raw.get(key) is not None},
        servings=_integer(raw.get("recipeYield") if is_jsonld else raw.get("servings") or raw.get("portions")),
        prep_time=_duration_minutes(raw.get("prepTime") or raw.get("preparationTime")),
        cook_time=_duration_minutes(raw.get("cookTime") or raw.get("cookingTime")),
        total_time=_duration_minutes(raw.get("totalTime") or raw.get("duration")),
        ingredients=tuple(_ingredients(raw, is_jsonld)), instructions=tuple(_instructions(raw, is_jsonld)),
        tags=tuple(_strings(raw.get("keywords") if is_jsonld else raw.get("tags") or raw.get("categories"))),
        nutrition=dict(raw["nutrition"]) if isinstance(raw.get("nutrition"), dict) else {}, image_url=_image(raw.get("image") if is_jsonld else raw.get("image") or raw.get("imageUrl")),
        retrieved_at=datetime.now(timezone.utc).isoformat(), date_modified=_text(raw.get("dateModified") or raw.get("modifiedAt")),
    )


def parse_ingredient(value: str) -> Ingredient:
    raw = " ".join(value.split())
    optional = bool(re.search(r"\boptional\b|\bnach belieben\b", raw, re.I))
    match = _QUANTITY.match(raw)
    if not match:
        return Ingredient(ingredient=raw or None, optional=optional, raw_text=raw)
    quantity, rest = match.group("quantity"), match.group("rest").strip()
    words = rest.split(maxsplit=1)
    unit = words[0].lower().rstrip(".") if words and words[0].lower().rstrip(".") in _UNITS else None
    ingredient = words[1] if unit and len(words) > 1 else rest
    parts = re.split(r"\s*,\s*", ingredient, maxsplit=1)
    return Ingredient(quantity, unit, parts[0] or None, parts[1] if len(parts) == 2 else None, optional, raw)


def _ingredients(raw: dict[str, Any], jsonld: bool) -> Iterable[Ingredient]:
    if jsonld:
        yield from (parse_ingredient(item) for item in _strings(raw.get("recipeIngredient")))
        return
    for group in raw.get("ingredientGroups", []) or []:
        for item in group.get("ingredients", []) if isinstance(group, dict) else []:
            if isinstance(item, str):
                yield parse_ingredient(item)
            elif isinstance(item, dict):
                raw_text = _text(item.get("text") or item.get("displayText") or item.get("name")) or ""
                name, quantity, unit, qualifier = _text(item.get("ingredient") or item.get("name")), _text(item.get("amount") or item.get("quantity")), _text(item.get("unit")), _text(item.get("note") or item.get("qualifier"))
                yield Ingredient(quantity, unit, name, qualifier, bool(item.get("optional")), raw_text or " ".join(x for x in (quantity, unit, name, qualifier) if x))


def _instructions(raw: dict[str, Any], jsonld: bool) -> Iterable[str]:
    value = raw.get("recipeInstructions") if jsonld else raw.get("instructions") or raw.get("preparationSteps") or raw.get("steps")
    values = value if isinstance(value, list) else [value]
    for item in values:
        if isinstance(item, dict): item = item.get("text") or item.get("description")
        if text := _text(item): yield text


def _duration_minutes(value: Any) -> int | None:
    if isinstance(value, (int, float)): return int(value)
    if not isinstance(value, str): return None
    match = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?", value.upper())
    return int(match.group(1) or 0) * 60 + int(match.group(2) or 0) if match else _integer(value)
def _integer(value: Any) -> int | None:
    match = re.search(r"\d+", str(value)) if value is not None else None
    return int(match.group()) if match else None
def _strings(value: Any) -> list[str]:
    if isinstance(value, str): return [part.strip() for part in value.split(",") if part.strip()]
    return [item for item in value if isinstance(item, str) and item.strip()] if isinstance(value, list) else []
def _text(value: Any) -> str | None: return value.strip() if isinstance(value, str) and value.strip() else None
def _image(value: Any) -> str | None:
    if isinstance(value, str): return value
    if isinstance(value, list) and value: return _image(value[0])
    return _text(value.get("url")) if isinstance(value, dict) else None
