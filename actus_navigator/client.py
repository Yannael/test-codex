"""HTTP client and parsers for the ULB news website."""
from __future__ import annotations

from dataclasses import dataclass
from html import unescape
import json
from typing import Any, Iterable, List, Optional, Sequence
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

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

    articles = _parse_from_containers(soup)
    if not articles:
        articles = _parse_from_structured_data(soup)
    if not articles:
        articles = _parse_from_links(soup)

    if articles:
        return articles

    raise ArticleListParseError("No articles found in the provided HTML page.")


def _parse_from_containers(soup: BeautifulSoup) -> List[Article]:
    """Try parsing article cards using common container structures."""

    container_selectors: Sequence[str] = (
        "div.view-content",
        "div.layout__region",
        "div.region-content",
        "main",
    )

    seen_urls: set[str] = set()
    articles: List[Article] = []

    containers = []
    for selector in container_selectors:
        containers.extend(soup.select(selector))
    if not containers:
        containers = [soup]

    for container in containers:
        for node in _iter_article_nodes(container):
            article = _parse_article_card(node)
            if article and article.url not in seen_urls:
                articles.append(article)
                seen_urls.add(article.url)
        if articles:
            break

    return articles


def _iter_article_nodes(container) -> Iterable:
    selectors: Sequence[str] = (
        "article",
        "div.views-row",
        "div.node--type-actualite",
        "div.card",
        "div.news-card",
        "div.article-card",
        "div.c-card",
        "div.media",
        "ul.objets.actualites li",
        "li.avec_vignette",
        "li.views-row",
        "li.card",
        "li.search-result__item",
    )

    yielded: set[int] = set()
    for selector in selectors:
        for node in container.select(selector):
            node_id = id(node)
            if node_id in yielded:
                continue
            yielded.add(node_id)
            yield node


def _parse_from_links(soup: BeautifulSoup) -> List[Article]:
    """Fallback parser extracting article information from anchor tags."""

    candidates = soup.select(
        ", ".join(
            {
                "a[href*='/toutes-les-actus']",
                "a[href*='/actualites']",
                "a[href*='/actualite']",
                "a[href*='/actus']",
                "a[href*='/news']",
                "a[href*='/agenda']",
            }
        )
    )

    articles: List[Article] = []
    seen_urls: set[str] = set()
    for link in candidates:
        article = _parse_article_from_link(link)
        if article and article.url not in seen_urls:
            articles.append(article)
            seen_urls.add(article.url)

    return articles


def _parse_article_card(node) -> Optional[Article]:
    """Parse a single article card element."""

    title_tag = node.select_one("h2 a, h3 a, .card__title a, .node__title a")
    if not title_tag:
        title_tag = _select_title_link(node)
    if not title_tag or not title_tag.get_text(strip=True):
        return None

    url = urljoin(BASE_URL, title_tag.get("href", "").strip())
    title = unescape(title_tag.get_text(strip=True))

    summary = _extract_summary(node, exclude_text=title)
    date_text = _extract_date(node)

    return Article(title=title, url=url, summary=summary, date=date_text)


def _select_title_link(node):
    """Return the anchor most likely to represent the article title."""

    candidate_links = [
        link
        for link in node.select("a[href]")
        if link.get("href") and any(part in link.get("href", "") for part in ("/actus/", "/actualites/"))
    ]

    if not candidate_links:
        return None

    candidate_links.sort(key=lambda link: len(link.get_text(strip=True) or ""), reverse=True)
    return candidate_links[0]


def _extract_summary(node, *, exclude_text: Optional[str] = None) -> str:
    summary_selectors: Sequence[str] = (
        "div.field--name-field-introduction",
        ".card__summary",
        ".node__teaser",
        ".views-field-field-introduction",
        ".field--name-field-introduction",
        ".c-card__summary",
        ".article-card__excerpt",
        "div.resume",
        ".media__content",
        "p",
    )

    current: Optional[Tag] = node if isinstance(node, Tag) else None
    depth = 0
    while current is not None and depth <= 5:
        for selector in summary_selectors:
            summary_tag = current.select_one(selector)
            if summary_tag:
                summary = summary_tag.get_text(" ", strip=True)
                if summary and (not exclude_text or summary != exclude_text):
                    return summary
        current = current.parent if isinstance(current.parent, Tag) else None
        depth += 1

    return ""


def _extract_date(node) -> Optional[str]:
    date_selectors: Sequence[str] = (
        "time",
        "span.date",
        ".card__date",
        ".news-card__date",
        ".c-card__date",
        ".article-card__date",
        ".date-display-single",
        ".date",
        "span.date--debut",
    )

    current: Optional[Tag] = node if isinstance(node, Tag) else None
    depth = 0
    while current is not None and depth <= 5:
        for selector in date_selectors:
            tag = current.select_one(selector)
            if tag and tag.get_text(strip=True):
                return tag.get_text(strip=True)
        current = current.parent if isinstance(current.parent, Tag) else None
        depth += 1

    return None


def _parse_article_from_link(link) -> Optional[Article]:
    text = link.get_text(strip=True)
    href = link.get("href")
    if not text or not href:
        return None

    url = urljoin(BASE_URL, href.strip())

    summary = _extract_summary(link.parent or link, exclude_text=text)
    date = _extract_date(link.parent or link)

    return Article(title=unescape(text), url=url, summary=summary, date=date)


def _parse_from_structured_data(soup: BeautifulSoup) -> List[Article]:
    """Parse articles embedded in structured JSON data."""

    scripts = soup.find_all(
        "script",
        attrs={"type": ["application/ld+json", "application/json"]},
    )

    seen_urls: set[str] = set()
    articles: List[Article] = []

    for script in scripts:
        text = script.string or script.get_text()
        if not text:
            continue

        try:
            data = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            continue

        for payload in _iter_json_nodes(data):
            article = _article_from_json(payload)
            if article and article.url not in seen_urls:
                articles.append(article)
                seen_urls.add(article.url)

    return articles


def _iter_json_nodes(data: Any) -> Iterable[Any]:
    if isinstance(data, dict):
        yield data
        for value in data.values():
            yield from _iter_json_nodes(value)
    elif isinstance(data, list):
        for item in data:
            yield from _iter_json_nodes(item)


def _article_from_json(data: Any) -> Optional[Article]:
    if not isinstance(data, dict):
        return None

    type_hint = data.get("@type") or data.get("type")
    if isinstance(type_hint, list):
        types = {t.lower() for t in type_hint if isinstance(t, str)}
    elif isinstance(type_hint, str):
        types = {type_hint.lower()}
    else:
        types = set()

    if types and not any(
        t in {
            "newsarticle",
            "article",
            "creativework",
            "listitem",
        }
        for t in types
    ):
        return None

    url = data.get("url") or data.get("@id")
    if not isinstance(url, str) or not url.strip():
        return None

    title = (
        data.get("headline")
        or data.get("name")
        or data.get("title")
        or data.get("text")
    )
    if not isinstance(title, str) or not title.strip():
        return None

    summary = data.get("description") or data.get("abstract") or ""
    if not isinstance(summary, str):
        summary = ""

    date = data.get("datePublished") or data.get("dateCreated") or data.get("dateModified")
    if not isinstance(date, str):
        date = None

    return Article(
        title=unescape(title.strip()),
        url=urljoin(BASE_URL, url.strip()),
        summary=unescape(summary.strip()),
        date=date.strip() if date else None,
    )


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
