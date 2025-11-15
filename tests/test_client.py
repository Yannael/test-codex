import importlib.util
import unittest

MISSING_DEPENDENCIES = [
    name for name in ("requests", "bs4") if importlib.util.find_spec(name) is None
]

if not MISSING_DEPENDENCIES:
    from actus_navigator.client import parse_articles  # type: ignore
else:  # pragma: no cover - exercised only when optional deps are missing
    parse_articles = None


def _skip_message() -> str:
    return "Modules manquants: " + ", ".join(MISSING_DEPENDENCIES)


@unittest.skipIf(parse_articles is None, _skip_message())
class ParseArticlesTests(unittest.TestCase):
    def test_parse_articles_from_common_containers(self) -> None:
        html = """
        <html>
          <body>
            <div class="view-content">
              <div class="views-row">
                <div class="card__date">1 janvier 2024</div>
                <h3 class="card__title"><a href="/fr/toutes-les-actus/article-1">Titre 1</a></h3>
                <div class="card__summary">Résumé de l'article 1</div>
              </div>
              <div class="views-row">
                <h2><a href="/fr/actualites/article-2">Titre 2</a></h2>
                <div class="field--name-field-introduction">Résumé 2</div>
                <time>15 février 2024</time>
              </div>
            </div>
          </body>
        </html>
        """

        articles = parse_articles(html)

        self.assertEqual(len(articles), 2)
        self.assertEqual(articles[0].title, "Titre 1")
        self.assertEqual(articles[0].summary, "Résumé de l'article 1")
        self.assertEqual(articles[0].date, "1 janvier 2024")
        self.assertEqual(articles[1].title, "Titre 2")
        self.assertEqual(articles[1].summary, "Résumé 2")
        self.assertEqual(articles[1].date, "15 février 2024")

    def test_parse_articles_fallback_from_links(self) -> None:
        html = """
        <html>
          <body>
            <ul>
              <li>
                <a href="/fr/toutes-les-actus/article-3">Titre 3</a>
                <span class="date">3 mars 2024</span>
                <p>Résumé 3</p>
              </li>
            </ul>
          </body>
        </html>
        """

        articles = parse_articles(html)

        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0].title, "Titre 3")
        self.assertEqual(articles[0].summary, "Résumé 3")
        self.assertEqual(articles[0].date, "3 mars 2024")


if __name__ == "__main__":
    unittest.main()
