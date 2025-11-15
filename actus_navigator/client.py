"""HTTP client and parsers for the ULB news website."""
from __future__ import annotations

from dataclasses import dataclass
from html import unescape
from typing import Iterable, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://actus.ulb.be"
LIST_PATH = "/fr/toutes-les-actus"


@dataclass
class Article:
    """Representation of a news article entry."""

    title: str
    url: str
    summary: str
    date: Optional[str] = None


class ArticleListParseError(RuntimeError):
    """Raised when the article list cannot be parsed."""


class ArticleDetailParseError(RuntimeError):
    """Raised when an article page cannot be parsed."""


def fetch_listing(page: int = 0, timeout: float = 10.0) -> str:
    """Fetch the HTML for the listing page.

    Args:
        page: Zero-based page index. The first page is 0.
        timeout: Optional timeout for the HTTP request in seconds.
    """

    params = {"page": page} if page else None
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        )
    }
    response = requests.get(urljoin(BASE_URL, LIST_PATH), params=params, timeout=timeout, headers=headers)
    response.raise_for_status()
    return response.text


def parse_articles(html: str) -> List[Article]:
    """Parse all articles from a listing HTML page."""

    soup = BeautifulSoup(html, "html.parser")

    # There can be multiple view containers depending on filters. We only
    # consider the main one that contains article cards.
    container_candidates: Iterable = soup.select("div.view-content") or [soup]
    for container in container_candidates:
        articles = [_parse_article_card(node) for node in container.select("article")]
        articles = [article for article in articles if article]
        if articles:
            return articles

    raise ArticleListParseError("No articles found in the provided HTML page.")


def _parse_article_card(node) -> Optional[Article]:
    """Parse a single article card element."""

    title_tag = node.select_one("h2 a, h3 a, .card__title a, .node__title a")
    if not title_tag or not title_tag.get_text(strip=True):
        return None

    url = urljoin(BASE_URL, title_tag.get("href", "").strip())
    title = unescape(title_tag.get_text(strip=True))

    summary_tag = (
        node.select_one("div.field--name-field-introduction, .card__summary, .node__teaser")
        or node.select_one("p")
    )
    summary = summary_tag.get_text(" ", strip=True) if summary_tag else ""

    time_tag = node.find("time")
    date_text = time_tag.get_text(strip=True) if time_tag else None

    return Article(title=title, url=url, summary=summary, date=date_text)


def fetch_article(url: str, timeout: float = 10.0) -> str:
    """Fetch a specific article page."""

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        )
    }
    response = requests.get(url, timeout=timeout, headers=headers)
    response.raise_for_status()
    return response.text


def parse_article_detail(html: str) -> str:
    """Extract a readable text summary from an article page."""

    soup = BeautifulSoup(html, "html.parser")

    content = soup.select_one(
        "div.node__content, article .node__content, div.article__body, main article"
    )
    if not content:
        raise ArticleDetailParseError("Article content not found.")

    paragraphs = [p.get_text(" ", strip=True) for p in content.find_all("p") if p.get_text(strip=True)]
    if not paragraphs:
        raise ArticleDetailParseError("Article body appears to be empty.")

    return "\n\n".join(paragraphs)
