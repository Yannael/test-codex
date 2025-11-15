"""Command-line interface for the ULB news navigator."""
from __future__ import annotations

import sys
from dataclasses import dataclass
from textwrap import fill
from typing import Callable, Iterable, List, Optional

from .client import (
    Article,
    ArticleDetailParseError,
    ArticleListParseError,
    fetch_article,
    get_listing_articles,
    parse_article_detail,
)


DEFAULT_WIDTH = 80


@dataclass
class MenuAction:
    key: str
    description: str
    handler: Callable[[], Optional[bool]]


class NewsNavigator:
    """Interactive terminal navigator for the ULB news website."""

    def __init__(self, page_size: int = 10, wrap_width: int = DEFAULT_WIDTH) -> None:
        self.page_index = 0
        self.page_size = page_size
        self.wrap_width = wrap_width
        self._articles: List[Article] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self) -> None:
        """Start the navigation loop."""

        print("Bienvenue dans l'outil de navigation des actus de l'ULB !")
        while True:
            try:
                self._load_page(self.page_index)
            except Exception as exc:  # pragma: no cover - defensive branch
                print(f"\nErreur lors du chargement de la page: {exc}")
                return

            self._display_page()
            action = self._prompt_action()
            if action is None:
                print("\nÀ bientôt !")
                return

            should_exit = action.handler()
            if should_exit:
                print("\nÀ bientôt !")
                return

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _load_page(self, page_index: int) -> None:
        try:
            articles = get_listing_articles(page_index, page_size=self.page_size)
        except ArticleListParseError as exc:
            raise RuntimeError(f"Impossible d'interpréter la liste d'actualités: {exc}") from exc
        self._articles = articles

    def _display_page(self) -> None:
        print("\n" + "=" * self.wrap_width)
        print(fill(f"Page {self.page_index + 1}", width=self.wrap_width))
        print("=" * self.wrap_width)

        if not self._articles:
            print("Aucune actualité trouvée.")
            return

        for idx, article in enumerate(self._articles, start=1):
            header = f"[{idx}] {article.title}"
            print(fill(header, width=self.wrap_width))
            if article.date:
                print(fill(f"Date : {article.date}", width=self.wrap_width))
            if article.summary:
                print(fill(article.summary, width=self.wrap_width))
            print(fill(f"Lien : {article.url}", width=self.wrap_width))
            print("-" * self.wrap_width)

        print("Commandes :")
        for action in self._actions():
            print(f"  {action.key} - {action.description}")

    def _actions(self) -> Iterable[MenuAction]:
        yield MenuAction("Entrée", "Choisir un numéro pour lire une actu", self._read_article)
        yield MenuAction("N", "Page suivante", self._next_page)
        if self.page_index > 0:
            yield MenuAction("P", "Page précédente", self._previous_page)
        yield MenuAction("Q", "Quitter", lambda: True)

    def _prompt_action(self) -> Optional[MenuAction]:
        raw = input("\nVotre choix (numéro, N, P, Q) : ").strip()
        if not raw:
            return None

        if raw.isdigit():
            index = int(raw) - 1
            return MenuAction(raw, "Ouvrir l'article", lambda: self._show_article(index))

        upper = raw.upper()
        mapping = {action.key.upper(): action for action in self._actions() if action.key.isalpha()}
        return mapping.get(upper)

    # ------------------------------------------------------------------
    # Action handlers
    # ------------------------------------------------------------------
    def _read_article(self) -> Optional[bool]:  # pragma: no cover - placeholder action
        return None

    def _show_article(self, index: int) -> Optional[bool]:
        if not 0 <= index < len(self._articles):
            print("Indice invalide.")
            return None

        article = self._articles[index]
        print("\n" + article.title)
        print(article.url)
        try:
            html = fetch_article(article.url)
            content = parse_article_detail(html)
        except (ArticleDetailParseError, Exception) as exc:
            print(f"Impossible de récupérer l'article complet: {exc}")
            return None

        for paragraph in content.split("\n\n"):
            print("\n" + fill(paragraph, width=self.wrap_width))

        input("\nAppuyez sur Entrée pour revenir à la liste...")
        return None

    def _next_page(self) -> Optional[bool]:
        self.page_index += 1
        return None

    def _previous_page(self) -> Optional[bool]:
        if self.page_index > 0:
            self.page_index -= 1
        return None


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point used by the console script."""

    navigator = NewsNavigator()
    navigator.run()
    return 0


if __name__ == "__main__":  # pragma: no cover - manual invocation
    raise SystemExit(main(sys.argv[1:]))
