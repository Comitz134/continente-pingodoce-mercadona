"""Recolhe produtos das 3 lojas e normaliza para um schema comum.

Schema de saída:
    {
      "product_id": "4949515",
      "name": "Arroz Basmati Continente",
      "brand": "Continente",
      "store": "Continente",
      "price": 1.89,          # preço do pacote
      "old_price": None,
      "unit": "1 Kg",          # quantidade do pacote
      "price_per_unit": 1.89,  # €/unidade de referência, quando disponível
      "url": "https://…",
      "image": None,
    }
"""

import html as _html
import json
import re
from urllib.parse import quote

import httpx

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"


def _get(url):
    r = httpx.get(url, headers={"User-Agent": UA}, follow_redirects=True, timeout=20.0)
    r.raise_for_status()
    return r.text


# ------------------------- Mercadona (Algolia) -------------------------

def search_mercadona(query, cfg):
    payload = {"params": f"query={quote(query)}&clickAnalytics=true&hitsPerPage=24"}
    r = httpx.post(
        cfg["endpoint"],
        params={
            "x-algolia-agent": "Algolia for JavaScript (3.35.1); Browser",
            "x-algolia-application-id": cfg["app_id"],
            "x-algolia-api-key": cfg["api_key"],
        },
        headers={"User-Agent": UA},
        json=payload,
        timeout=15.0,
    )
    r.raise_for_status()
    return [_normalize_mercadona(hit, cfg["store_id"]) for hit in r.json().get("hits", [])]


def _normalize_mercadona(hit, store):
    pi = hit.get("price_instructions") or {}
    size, fmt = pi.get("unit_size"), pi.get("size_format")
    unit = f"{size} {fmt}".strip() if size is not None else None
    bulk, unit_price = pi.get("bulk_price"), pi.get("unit_price")
    return {
        "product_id": str(hit.get("objectID") or hit.get("id")),
        "name": hit.get("display_name"),
        "brand": hit.get("brand"),
        "store": store,
        "price": float(bulk) if bulk not in (None, "") else None,
        "old_price": None,
        "unit": unit,
        "price_per_unit": float(unit_price) if unit_price not in (None, "") else None,
        "url": hit.get("share_url"),
        "image": hit.get("thumbnail"),
    }


# ------------------------- Continente (HTML) -------------------------

def search_continente(query, cfg):
    doc = _get(cfg["search_url"].format(query=quote(query)))
    results = []
    # cada tile começa com <div class="product" data-pid="…"> e traz o JSON
    for chunk in doc.split('<div class="product" data-pid="')[1:]:
        m = re.search(r"data-product-tile-impression='([^']*)'", chunk)
        if not m:
            continue
        try:
            imp = json.loads(_html.unescape(m.group(1)))
        except json.JSONDecodeError:
            continue
        href = re.search(r'href="(/produto/[^"?]+\.html)', chunk)
        price = imp.get("price")
        results.append({
            "product_id": str(imp.get("id")),
            "name": imp.get("name"),
            "brand": imp.get("brand"),
            "store": cfg["store_id"],
            "price": float(price) if price not in (None, "") else None,
            "old_price": None,
            "unit": None,
            "price_per_unit": None,
            "url": ("https://www.continente.pt" + href.group(1)) if href else None,
            "image": None,
        })
    return results


# ------------------------- Pingo Doce (HTML) -------------------------

def search_pingodoce(query, cfg):
    doc = _get(cfg["search_url"].format(query=quote(query)))
    results = []
    # cada produto tem um bloco product-name-link → … → product-cta data-pid
    for chunk in doc.split('<div class="product-name-link">')[1:]:
        mname = re.search(r'<a href="([^"]+)">([^<]+)</a>', chunk)
        mprice = re.search(r'class="value" content="([0-9,.]+)"', chunk)
        if not (mname and mprice):
            continue
        mbrand = re.search(r'class="product-brand-name">\s*([^<]+)', chunk)
        munit = re.search(r'class="product-unit">\s*([^<]+)', chunk)
        mpid = re.search(r'data-pid="(\d+)"', chunk)
        unit, ppu = _parse_unit(munit.group(1)) if munit else (None, None)
        results.append({
            "product_id": mpid.group(1) if mpid else None,
            "name": _html.unescape(mname.group(2)).strip(),
            "brand": mbrand.group(1).strip() if mbrand else None,
            "store": cfg["store_id"],
            "price": float(mprice.group(1).replace(",", ".")),
            "old_price": None,
            "unit": unit,
            "price_per_unit": ppu,
            "url": "https://www.pingodoce.pt" + mname.group(1),
            "image": None,
        })
    return results


def _parse_unit(text):
    # ex.: "1 Kg | 1,89 €/Kg"
    t = _html.unescape(text).strip()
    unit = t.split("|")[0].strip() if "|" in t else t
    m = re.search(r"([0-9,.]+)\s*€\s*/\s*([A-Za-z]+)", t)
    ppu = float(m.group(1).replace(",", ".")) if m else None
    return unit, ppu


# ------------------------- Dispatcher -------------------------

def search_store(query, cfg):
    kind = cfg.get("kind")
    if kind == "algolia":
        return search_mercadona(query, cfg)
    if kind == "html_continente":
        return search_continente(query, cfg)
    if kind == "html_pingodoce":
        return search_pingodoce(query, cfg)
    raise NotImplementedError(f"Conector '{kind}' não implementado.")
