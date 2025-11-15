"""Utilities to render a zen HTML page listing ULB articles."""
from __future__ import annotations

import argparse
from datetime import datetime
from html import escape
from pathlib import Path
from typing import List, Optional, Sequence
from string import Template

from .client import Article, ArticleListParseError, get_listing_articles


def collect_articles(pages: int = 3, page_size: int = 20) -> List[Article]:
    """Collect articles from the listing across a number of pages."""

    if pages <= 0:
        raise ValueError("pages must be a positive integer")
    if page_size <= 0:
        raise ValueError("page_size must be a positive integer")

    articles: List[Article] = []
    seen_urls: set[str] = set()

    for index in range(pages):
        page_articles = get_listing_articles(index, page_size=page_size)
        if not page_articles and index == 0:
            raise ArticleListParseError("Aucune actualité n'a été récupérée depuis le site.")
        if not page_articles:
            break

        for article in page_articles:
            if article.url in seen_urls:
                continue
            seen_urls.add(article.url)
            articles.append(article)

    return articles


def render_html_page(articles: Sequence[Article], title: str = "Actus ULB") -> str:
    """Render a zen dashboard HTML page for the provided articles."""

    generated_at = datetime.now().strftime("%d %B %Y à %H:%M")
    safe_title = escape(title)
    safe_generated_at = escape(generated_at)

    cards_html = "\n".join(_render_article(article) for article in articles)
    has_articles = bool(cards_html.strip())
    if not has_articles:
        cards_html = ""

    if has_articles:
        empty_state_attrs = " hidden"
        empty_message = "Aucune actualité ne correspond à votre recherche pour le moment."
    else:
        empty_state_attrs = ""
        empty_message = "Aucune actualité n'a pu être chargée. Réessayez plus tard."

    empty_state = (
        f"    <p class=\"empty-state\"{empty_state_attrs}>"
        f"{escape(empty_message, quote=False)}</p>"
    )

    template = Template(
        """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>$title</title>
  <style>
    :root {
      color-scheme: light dark;
      --bg: #f6f6f0;
      --card-bg: rgba(255, 255, 255, 0.75);
      --accent: #2f8f83;
      --accent-soft: rgba(47, 143, 131, 0.12);
      --text: #33433f;
      --muted: #60706c;
      --shadow: 0 20px 40px rgba(15, 31, 28, 0.12);
      font-family: 'Helvetica Neue', 'Segoe UI', sans-serif;
    }

    body {
      margin: 0;
      min-height: 100vh;
      background: linear-gradient(160deg, var(--bg) 0%, #e7efe9 50%, #f4f0ff 100%);
      color: var(--text);
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 4rem 1rem 3rem;
      transition: background 0.4s ease;
      position: relative;
    }

    header {
      max-width: 960px;
      width: 100%;
      text-align: center;
      margin-bottom: 2rem;
      position: relative;
      z-index: 1;
    }

    h1 {
      font-weight: 300;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      margin-bottom: 0.75rem;
    }

    .subtitle {
      color: var(--muted);
      margin-bottom: 2rem;
    }

    .search-wrapper {
      position: relative;
      display: inline-flex;
      align-items: center;
      background: var(--card-bg);
      padding: 0.75rem 1rem;
      border-radius: 999px;
      box-shadow: var(--shadow);
    }

    .search-wrapper input {
      border: none;
      outline: none;
      background: transparent;
      font-size: 1rem;
      min-width: 18rem;
      color: inherit;
    }

    main {
      width: 100%;
      max-width: 960px;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 1.5rem;
      position: relative;
      z-index: 1;
    }

    article.card {
      background: var(--card-bg);
      backdrop-filter: blur(8px);
      border-radius: 24px;
      padding: 1.75rem;
      box-shadow: var(--shadow);
      display: flex;
      flex-direction: column;
      gap: 1rem;
      transition: transform 0.3s ease, box-shadow 0.3s ease;
    }

    article.card:hover {
      transform: translateY(-6px);
      box-shadow: 0 30px 45px rgba(15, 31, 28, 0.18);
    }

    article.card h2 {
      margin: 0;
      font-size: 1.35rem;
      font-weight: 400;
    }

    article.card a {
      color: var(--accent);
      text-decoration: none;
    }

    article.card a:hover {
      text-decoration: underline;
    }

    .meta {
      font-size: 0.9rem;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    .empty-state {
      grid-column: 1 / -1;
      text-align: center;
      background: var(--card-bg);
      padding: 2rem;
      border-radius: 24px;
      box-shadow: var(--shadow);
    }

    footer {
      margin-top: 3rem;
      text-align: center;
      font-size: 0.85rem;
      color: var(--muted);
      position: relative;
      z-index: 1;
    }

    .pill {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      background: var(--accent-soft);
      color: var(--accent);
      padding: 0.35rem 0.85rem;
      border-radius: 999px;
      font-size: 0.8rem;
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }

    .butterfly-layer {
      position: fixed;
      inset: 0;
      overflow: hidden;
      pointer-events: none;
      z-index: 0;
    }

    .butterfly {
      position: absolute;
      bottom: -12vh;
      width: var(--size, 42px);
      height: var(--size, 42px);
      opacity: 0;
      transform-origin: center;
      animation: flutter var(--duration, 22s) linear infinite;
      animation-delay: var(--delay, 0s);
    }

    .butterfly::before,
    .butterfly::after {
      content: "";
      position: absolute;
      width: 70%;
      height: 70%;
      top: 15%;
      border-radius: 100% 0 100% 0;
      background: radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.9), rgba(47, 143, 131, 0.15));
      box-shadow: 0 0 12px rgba(47, 143, 131, 0.25);
    }

    .butterfly::before {
      left: -10%;
      transform: rotate(35deg);
    }

    .butterfly::after {
      right: -10%;
      transform: scaleX(-1) rotate(35deg);
    }

    @keyframes flutter {
      0% {
        transform: translate3d(0, 0, 0) scale(0.9) rotate(-8deg);
        opacity: 0;
      }
      12% {
        opacity: 0.7;
      }
      50% {
        transform: translate3d(var(--sway, 60px), -55vh, 0) scale(1) rotate(10deg);
        opacity: 0.85;
      }
      86% {
        opacity: 0.65;
      }
      100% {
        transform: translate3d(calc(var(--sway, 60px) * -0.4), -110vh, 0) scale(0.95) rotate(-8deg);
        opacity: 0;
      }
    }

    .soundscape {
      position: fixed;
      bottom: 1.25rem;
      right: 1.5rem;
      z-index: 2;
      background: var(--card-bg);
      border-radius: 999px;
      box-shadow: var(--shadow);
      padding: 0.35rem 0.75rem;
    }

    @media (max-width: 600px) {
      body {
        padding-top: 3rem;
      }

      .search-wrapper input {
        min-width: 12rem;
      }
    }
  </style>
</head>
<body>
  <div class="butterfly-layer" aria-hidden="true">
    <span class="butterfly" style="--delay: -2s; --duration: 24s; --size: 40px;"></span>
    <span class="butterfly" style="--delay: -8s; --duration: 28s; --size: 48px;"></span>
    <span class="butterfly" style="--delay: -12s; --duration: 26s; --size: 36px;"></span>
    <span class="butterfly" style="--delay: -4s; --duration: 30s; --size: 44px;"></span>
    <span class="butterfly" style="--delay: -16s; --duration: 32s; --size: 38px;"></span>
    <span class="butterfly" style="--delay: -20s; --duration: 27s; --size: 46px;"></span>
  </div>
  <header>
    <h1>$title</h1>
    <p class="subtitle">Un espace apaisant pour parcourir les dernières nouvelles de l'ULB.</p>
    <div class="search-wrapper">
      <span class="pill">Filtrer</span>
      <input id="search" type="search" placeholder="Entrez des mots clés..." aria-label="Filtrer les actualités">
    </div>
  </header>
  <main id="articles">
$cards_html
$empty_state
  </main>
  <footer>
    Généré le $generated_at – Les contenus appartiennent à l'Université libre de Bruxelles.
  </footer>
  <audio id="soundscape" class="soundscape" controls loop preload="auto">
    <source src="https://cdn.pixabay.com/download/audio/2022/01/19/audio_e8d3ba1adb.mp3?filename=morning-garden-18307.mp3" type="audio/mpeg">
    Votre navigateur ne supporte pas la lecture audio HTML5.
  </audio>
  <script>
    const searchInput = document.getElementById('search');
    const cards = Array.from(document.querySelectorAll('article.card'));
    const emptyState = document.querySelector('.empty-state');
    const butterflies = Array.from(document.querySelectorAll('.butterfly'));
    const audio = document.getElementById('soundscape');

    function normalise(text) {
      if (!text) return '';
      let base = text.toLowerCase();
      if (base.normalize) {
        base = base.normalize('NFD');
      }
      return base
        .replace(/[\u0300-\u036f]/g, '')
        .replace(/[^a-z0-9\s]/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();
    }

    const cardMetadata = cards.map(card => ({
      element: card,
      keywords: normalise((card.dataset.keywords || '') + ' ' + (card.textContent || ''))
    }));

    function filterCards() {
      if (!searchInput) {
        return;
      }
      const query = normalise(searchInput.value || '');
      if (!query) {
        cardMetadata.forEach(item => item.element.hidden = false);
        if (emptyState) emptyState.hidden = cardMetadata.length > 0 ? true : false;
        return;
      }

      const tokens = query.split(' ').filter(Boolean);
      let visibleCount = 0;
      cardMetadata.forEach(item => {
        const matches = tokens.every(token => item.keywords.includes(token));
        item.element.hidden = !matches;
        if (matches) visibleCount += 1;
      });

      if (emptyState) emptyState.hidden = visibleCount !== 0;
    }

    if (searchInput) {
      searchInput.addEventListener('input', filterCards);
      searchInput.addEventListener('search', filterCards);
      filterCards();
    }

    butterflies.forEach(butterfly => {
      const randomise = () => {
        const left = Math.random() * 100;
        const sway = 40 + Math.random() * 80;
        const duration = 22 + Math.random() * 10;
        const delay = -Math.random() * 20;
        butterfly.style.left = left + '%';
        butterfly.style.setProperty('--sway', sway + 'px');
        butterfly.style.setProperty('--duration', duration + 's');
        butterfly.style.setProperty('--delay', delay + 's');
      };
      randomise();
      butterfly.addEventListener('animationiteration', randomise);
    });

    if (audio) {
      audio.volume = 0.6;
      const startPlayback = () => {
        audio.play().catch(() => {});
      };
      if (searchInput) {
        searchInput.addEventListener('focus', startPlayback, { once: true });
      }
      document.addEventListener('pointerdown', startPlayback, { once: true });
    }
  </script>
</body>
</html>
"""
    )

    return template.substitute(
        title=safe_title,
        cards_html=cards_html,
        empty_state=empty_state,
        generated_at=safe_generated_at,
    )


def _render_article(article: Article) -> str:
    summary_text = article.summary or ""
    keywords = " ".join(
        filter(
            None,
            [
                article.title,
                summary_text,
                article.date or "",
                article.url,
            ],
        )
    )
    safe_keywords = escape(keywords)
    safe_title = escape(article.title)
    safe_summary = escape(summary_text)
    safe_url = escape(article.url)

    date_block = f"      <p class=\"meta\">{escape(article.date)}</p>\n" if article.date else ""
    summary_block = (
        f"      <p>{safe_summary}</p>\n" if summary_text else "      <p class=\"meta\">Pas de résumé disponible.</p>\n"
    )

    return (
        f"    <article class=\"card\" data-keywords=\"{safe_keywords}\">\n"
        f"      <h2><a href=\"{safe_url}\" target=\"_blank\" rel=\"noopener noreferrer\">{safe_title}</a></h2>\n"
        f"{date_block}"
        f"{summary_block}"
        "    </article>"
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Console script entry point to generate the HTML page."""

    parser = argparse.ArgumentParser(
        description=(
            "Génère une page HTML zen permettant de filtrer dynamiquement les actualités de l'ULB."
        )
    )
    parser.add_argument(
        "output",
        nargs="?",
        default="actus_ulb.html",
        help="Chemin du fichier HTML à créer (défaut: actus_ulb.html)",
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=3,
        help="Nombre maximum de pages d'actualités à récupérer (défaut: 3)",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=20,
        help="Nombre d'actualités à demander par page (défaut: 20)",
    )

    args = parser.parse_args(argv)

    articles = collect_articles(pages=args.pages, page_size=args.page_size)
    html = render_html_page(articles)
    output_path = Path(args.output)
    output_path.write_text(html, encoding="utf-8")
    print(f"Page HTML générée dans {output_path.resolve()}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI hook
    raise SystemExit(main())
