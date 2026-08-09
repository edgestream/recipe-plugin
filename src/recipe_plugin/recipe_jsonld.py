"""Extract Chefkoch recipe data from JSON-LD or Nuxt page payloads."""

from __future__ import annotations

import json
from html.parser import HTMLParser
from typing import Any


class RecipeNotFoundError(ValueError):
    """Raised when a document has no recipe object."""


def extract_recipe_jsonld(html: str) -> dict[str, Any]:
    parser = _JsonLdScriptParser()
    parser.feed(html)
    for payload in parser.payloads:
        try:
            document = json.loads(payload)
        except json.JSONDecodeError:
            continue
        for node in _nodes(document):
            node_type = node.get("@type")
            if "Recipe" in (node_type if isinstance(node_type, list) else [node_type]):
                return node
    recipe = _find_recipe(decode_nuxt_payload(parser.nuxt_payload))
    if recipe is not None:
        return recipe
    raise RecipeNotFoundError("No recipe object found.")


class _JsonLdScriptParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.payloads: list[str] = []
        self.nuxt_payload: str | None = None
        self._parts: list[str] | None = None
        self._is_nuxt = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag.lower() != "script":
            return
        self._is_nuxt = attributes.get("id") == "__NUXT_DATA__" and attributes.get("data-nuxt-data") == "nuxt-app"
        if attributes.get("type", "").lower().startswith("application/ld+json") or self._is_nuxt:
            self._parts = []

    def handle_data(self, data: str) -> None:
        if self._parts is not None:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._parts is not None:
            payload = "".join(self._parts)
            if self._is_nuxt:
                self.nuxt_payload = payload
            else:
                self.payloads.append(payload)
            self._parts = None
            self._is_nuxt = False


def decode_nuxt_payload(payload: str | None) -> Any:
    if not payload:
        return None
    try:
        return _NuxtUnflattener(json.loads(payload)).value(0)
    except (json.JSONDecodeError, IndexError, TypeError, ValueError):
        return None


class _NuxtUnflattener:
    def __init__(self, flat: Any) -> None:
        if not isinstance(flat, list):
            raise ValueError("Nuxt payload must be a list.")
        self._flat = flat
        self._cache: dict[int, Any] = {}

    def value(self, index: int) -> Any:
        if index < 0:
            return None
        if index >= len(self._flat):
            raise IndexError(index)
        if index in self._cache:
            return self._cache[index]
        raw = self._flat[index]
        if not isinstance(raw, (dict, list)):
            return raw
        if isinstance(raw, list) and raw and raw[0] in {"ShallowReactive", "Reactive", "Ref"}:
            result = self.value(raw[1])
            self._cache[index] = result
            return result
        result: Any = [] if isinstance(raw, list) else {}
        self._cache[index] = result
        if isinstance(raw, list):
            result.extend(self.value(item) if isinstance(item, int) else item for item in raw)
        else:
            result.update({key: self.value(item) if isinstance(item, int) else item for key, item in raw.items()})
        return result


def _nodes(document: Any) -> list[dict[str, Any]]:
    if isinstance(document, dict):
        graph = document.get("@graph")
        return [node for node in graph if isinstance(node, dict)] if isinstance(graph, list) else [document]
    return [node for node in document if isinstance(node, dict)] if isinstance(document, list) else []


def _find_recipe(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        if isinstance(value.get("id"), str) and isinstance(value.get("title"), str) and "ingredientGroups" in value:
            return value
        for child in value.values():
            if recipe := _find_recipe(child):
                return recipe
    elif isinstance(value, list):
        for child in value:
            if recipe := _find_recipe(child):
                return recipe
    return None
