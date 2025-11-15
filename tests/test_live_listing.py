import importlib.util
import unittest

MISSING_DEPENDENCIES = [
    name for name in ("requests", "bs4") if importlib.util.find_spec(name) is None
]

if not MISSING_DEPENDENCIES:
    from requests import RequestException
    from actus_navigator.client import get_listing_articles
else:  # pragma: no cover - executed only when optional dependencies are missing
    get_listing_articles = None  # type: ignore[assignment]
    RequestException = Exception  # type: ignore[misc,assignment]


def _skip_message() -> str:
    return "Modules manquants: " + ", ".join(MISSING_DEPENDENCIES)


@unittest.skipIf(get_listing_articles is None, _skip_message())
class LiveListingIntegrationTests(unittest.TestCase):
    def test_fetch_listing_returns_articles(self) -> None:
        try:
            articles = get_listing_articles(timeout=20)
        except RequestException as exc:  # pragma: no cover - network failures
            self.skipTest(f"Echec du telechargement du listing en ligne: {exc}")

        self.assertGreater(len(articles), 0, "Le listing en ligne ne contient aucune actu")
        first_article = articles[0]
        self.assertTrue(first_article.title)
        self.assertTrue(first_article.url.startswith("https://"))


if __name__ == "__main__":  # pragma: no cover - manual execution helper
    unittest.main()
