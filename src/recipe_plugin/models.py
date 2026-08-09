"""Stable public representation of a Chefkoch recipe."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Ingredient:
    quantity: str | None = None
    unit: str | None = None
    ingredient: str | None = None
    qualifier: str | None = None
    optional: bool = False
    raw_text: str = ""


@dataclass(frozen=True)
class Recipe:
    source: str
    source_url: str
    recipe_id: str
    title: str
    description: str | None
    is_plus: bool
    editorial: dict[str, Any] = field(default_factory=dict)
    servings: int | None = None
    prep_time: int | None = None
    cook_time: int | None = None
    total_time: int | None = None
    ingredients: tuple[Ingredient, ...] = ()
    instructions: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    nutrition: dict[str, Any] = field(default_factory=dict)
    image_url: str | None = None
    retrieved_at: str = ""
    date_modified: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RecipeCandidate:
    recipe_id: str | None
    title: str
    source_url: str
    description: str | None = None
    image_url: str | None = None
    is_plus: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
