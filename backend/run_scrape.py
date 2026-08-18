"""Recolhe as 3 lojas e guarda no Supabase (ou SQLite local).

Para correr localmente:
    pip install -r requirements.txt
    python run_scrape.py

Com Supabase (define as variáveis antes):
    SUPABASE_URL=... SUPABASE_SERVICE_KEY=... python run_scrape.py

No GitHub Actions este script corre pelo workflow .github/workflows/scrape.yml.
"""

import db
import scrapers
from config import STORES, QUERIES


def main():
    db.init()
    for store_id, cfg in STORES.items():
        for q in QUERIES:
            try:
                results = scrapers.search_store(q, cfg)
                changed = 0
                for p in results:
                    db.upsert_product(p)
                    if db.snapshot_price(p):
                        changed += 1
                print(f"[{store_id}] {q}: {len(results)} produtos, {changed} preços novos")
            except Exception as exc:  # noqa: BLE001
                print(f"[erro] [{store_id}] {q}: {exc}")


if __name__ == "__main__":
    main()
