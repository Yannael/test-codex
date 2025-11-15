import importlib.util
import unittest

MISSING_DEPENDENCIES = [
    name for name in ("requests", "bs4") if importlib.util.find_spec(name) is None
]

if not MISSING_DEPENDENCIES:
    from requests import RequestException
    from actus_navigator.client import fetch_listing, parse_articles
else:  # pragma: no cover - executed only when optional dependencies are missing
    fetch_listing = None  # type: ignore[assignment]
    parse_articles = None  # type: ignore[assignment]
    RequestException = Exception  # type: ignore[misc,assignment]


def _skip_message() -> str:
    return "Modules manquants: " + ", ".join(MISSING_DEPENDENCIES)


@unittest.skipIf(parse_articles is None or fetch_listing is None, _skip_message())
class LiveListingIntegrationTests(unittest.TestCase):
    def test_fetch_listing_returns_articles(self) -> None:
        try:
            html = fetch_listing(timeout=20)
        except RequestException as exc:  # pragma: no cover - network failures
            self.skipTest(f"Echec du telechargement du listing en ligne: {exc}")

        articles = parse_articles(html)

        self.assertGreater(len(articles), 0, "Le listing en ligne ne contient aucune actu")
        first_article = articles[0]
        self.assertTrue(first_article.title)
        self.assertTrue(first_article.url.startswith("https://"))


if __name__ == "__main__":  # pragma: no cover - manual execution helper
    unittest.main()
