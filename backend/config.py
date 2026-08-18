"""Conectores por supermercado (endpoints internos, uso pessoal).

Verificado em 2026-08-18:
- Mercadona: Algolia (JSON). O índice abaixo é o de Valência (ES); para
  Portugal abre mercadona.pt com o DevTools e copia índice/App ID/API key
  para uma entrada `mercadona_pt`.
- Continente: `continente.pt/pesquisa/?q=` devolve HTML com os produtos em
  `data-product-tile-impression` (JSON com nome/preço/marca/categoria).
- Pingo Doce: `pingodoce.pt/home/produtos?q=` (Salesforce Commerce Cloud),
  tiles com `data-pid`, nome, marca, preço e preço por unidade (€/Kg).

Estes endpoints são internos e podem mudar. Usa com moderação.
"""

STORES = {
    "mercadona_es": {
        "display": "Mercadona",
        "kind": "algolia",
        "endpoint": "https://7uzjkl1dj0-dsn.algolia.net/1/indexes/products_prod_vlc1_es/query",
        "app_id": "7UZJKL1DJ0",
        "api_key": "9d8f2e39e90df472b4f2e559a116fe17",
        "index": "products_prod_vlc1_es",
    },
    "continente": {
        "display": "Continente",
        "kind": "html_continente",
        "search_url": "https://www.continente.pt/pesquisa/?q={query}",
    },
    "pingo_doce": {
        "display": "Pingo Doce",
        "kind": "html_pingodoce",
        "search_url": "https://www.pingodoce.pt/home/produtos?q={query}",
    },
    # "mercadona_pt": {
    #     "display": "Mercadona",
    #     "kind": "algolia",
    #     "endpoint": "https://<id>-dsn.algolia.net/1/indexes/<indice>/query",
    #     "app_id": "<app-id>",
    #     "api_key": "<search-only-key>",
    #     "index": "<indice>",
    # },
}

# Queries usadas pelo job agendado (ingredientes mais comuns das receitas).
QUERIES = [
    "arroz", "massa esparguete", "azeite", "peito de frango", "leite",
    "ovos", "batata", "cebola", "tomate", "banana",
    "sardinha", "salmao", "camarao", "carne picada", "feijao",
    "lentilhas", "grao de bico", "farinha", "acucar", "queijo ralado",
]
