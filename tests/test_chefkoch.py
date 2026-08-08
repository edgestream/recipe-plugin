from contextlib import asynccontextmanager

import pytest

from recipe_plugin.chefkoch import ChefkochClient, SEARCH_URL, _extract_candidates


def test_search_candidates_include_marked_plus_recipes_without_filtering() -> None:
    html = '''<script type="application/json" data-nuxt-data="nuxt-app" id="__NUXT_DATA__">
    [["ShallowReactive",1],{"data":2},{"results":3},[4,9],
    {"id":5,"title":6,"siteUrl":7,"isPlus":8},"1","PLUS Pasta","/rezepte/1/plus-pasta.html",true,
    {"id":10,"title":11,"siteUrl":12,"isPlus":13},"2","Community Pasta","/rezepte/2/community.html",false]
    </script>'''

    results = _extract_candidates(html)

    assert [result.title for result in results] == ["PLUS Pasta", "Community Pasta"]
    assert results[0].is_plus is True
    assert results[1].source_url == "https://www.chefkoch.de/rezepte/2/community.html"


async def test_public_search_never_logs_in_and_uses_public_url() -> None:
    class CapturingClient(ChefkochClient):
        def __init__(self) -> None:
            self.requested_url: str | None = None

        @asynccontextmanager
        async def _new_session(self):
            yield object()

        async def _get_html(self, session: object, url: str) -> tuple[str, str]:
            self.requested_url = url
            return "", url

    client = CapturingClient()
    assert await client.search_recipes("Zucchini & Pasta") == []
    assert client.requested_url == SEARCH_URL.format(query="Zucchini%20%26%20Pasta")


@pytest.mark.parametrize("url", ["http://www.chefkoch.de/rezepte/1", "https://example.com/recipe"])
async def test_public_get_rejects_non_chefkoch_https_urls(url: str) -> None:
    with pytest.raises(ValueError, match="Only HTTPS URLs"):
        await ChefkochClient().get_recipe(url)


@pytest.mark.parametrize("limit", [0, 21, True, "1"])
async def test_search_rejects_invalid_limits(limit: object) -> None:
    with pytest.raises(ValueError, match="between 1 and 20"):
        await ChefkochClient().search_recipes("Pasta", limit)  # type: ignore[arg-type]
