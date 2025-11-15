# Navigateur d'actualités ULB

Cette application en ligne de commande facilite la consultation des actualités publiées sur [https://actus.ulb.be/fr/toutes-les-actus](https://actus.ulb.be/fr/toutes-les-actus).

## Installation

1. Créez un environnement virtuel Python (facultatif mais recommandé) :
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

## Utilisation

Lancez le navigateur depuis la racine du projet :

```bash
python -m actus_navigator.cli
```

L'application récupère la liste des actualités et affiche pour chacune :
- le titre,
- la date (si disponible),
- un court résumé,
- le lien direct vers l'article.

Lorsque la page HTML des actus ne renvoie aucun contenu (cas fréquent depuis la
mise à jour du site), l'outil se rabat automatiquement sur le flux RSS officiel
exposé par l'ULB. Cela garantit qu'au moins les dernières actualités restent
accessibles depuis la ligne de commande.

Entrez le numéro d'une actualité pour consulter son contenu détaillé directement dans le terminal, ou utilisez `N` / `P` pour naviguer entre les pages et `Q` pour quitter.

> **Remarque :** l'application a besoin d'un accès réseau sortant pour interroger le site de l'ULB.
