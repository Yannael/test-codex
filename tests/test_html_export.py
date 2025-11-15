"""Tests for the zen HTML export helpers."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from actus_navigator.client import Article
from actus_navigator import html_export


class RenderHtmlPageTests(unittest.TestCase):
    def test_render_html_contains_search_and_cards(self) -> None:
        articles = [
            Article(
                title="Titre apaisant",
                url="https://actus.ulb.be/article-1",
                summary="Une description très zen.",
                date="1 janvier 2024",
            ),
            Article(
                title="Deuxième nouvelle",
                url="https://actus.ulb.be/article-2",
                summary="Du contenu inspirant.",
                date=None,
            ),
        ]

        html = html_export.render_html_page(articles, title="Actus Zen")

        self.assertIn("Actus Zen", html)
        self.assertIn("input id=\"search\"", html)
        self.assertIn("data-keywords=\"Titre apaisant", html)
        self.assertIn("Aucune actualité ne correspond à votre recherche", html)
        self.assertIn("https://actus.ulb.be/article-1", html)

    def test_render_html_without_articles_shows_placeholder(self) -> None:
        html = html_export.render_html_page([], title="Calme")

        self.assertIn("Calme", html)
        self.assertIn("Aucune actualité n'a pu être chargée", html)
        self.assertIn("class=\"empty-state\"", html)
        # No card should be present when there are no articles.
        self.assertNotIn("article class=\"card\"", html)


class CollectArticlesTests(unittest.TestCase):
    def test_collect_articles_deduplicates_and_stops(self) -> None:
        articles_page_1 = [
            Article(title="Titre 1", url="https://example.com/1", summary="Résumé 1", date="2024-01-01"),
            Article(title="Titre 2", url="https://example.com/2", summary="Résumé 2", date="2024-01-02"),
        ]
        articles_page_2 = [
            Article(title="Titre 2", url="https://example.com/2", summary="Résumé 2", date="2024-01-02"),
            Article(title="Titre 3", url="https://example.com/3", summary="Résumé 3", date="2024-01-03"),
        ]

        with patch.object(html_export, "get_listing_articles", side_effect=[articles_page_1, articles_page_2, []]):
            result = html_export.collect_articles(pages=5, page_size=10)

        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].title, "Titre 1")
        self.assertEqual(result[-1].title, "Titre 3")

    def test_collect_articles_raises_on_empty_first_page(self) -> None:
        with patch.object(html_export, "get_listing_articles", return_value=[]):
            with self.assertRaises(html_export.ArticleListParseError):
                html_export.collect_articles(pages=2, page_size=10)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
