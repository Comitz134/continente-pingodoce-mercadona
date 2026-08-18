"""Persistência: Supabase (Postgres) se as credenciais existirem, senão SQLite local.

Variáveis de ambiente:
    SUPABASE_URL          ex.: https://xyzcompany.supabase.co
    SUPABASE_SERVICE_KEY  chave `service_role` (nunca a ponhas na app)
    SQLITE_PATH           (opcional) caminho do SQLite local

A app (GitHub Pages) lê do Supabase com a chave `anon` — a `service_role`
fica só aqui no backend/scraper.
"""

import os
import sqlite3
from datetime import datetime, timezone

import httpx

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
USE_SUPABASE = bool(SUPABASE_URL and SUPABASE_SERVICE_KEY)
DB_PATH = os.environ.get("SQLITE_PATH", "prices.db")


def _now():
    return datetime.now(timezone.utc).isoformat()


def _product_row(p):
    return {
        "product_id": p["product_id"],
        "store": p["store"],
        "name": p.get("name"),
        "brand": p.get("brand"),
        "unit": p.get("unit"),
        "url": p.get("url"),
        "image": p.get("image"),
        "price": p.get("price"),
        "price_per_unit": p.get("price_per_unit"),
        "updated_at": _now(),
    }


# ---------------- Supabase (PostgREST) ----------------

def _sb(method, path, params=None, json=None):
    if not USE_SUPABASE:
        raise RuntimeError("Supabase não configurado (SUPABASE_URL/SUPABASE_SERVICE_KEY).")
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }
    r = httpx.request(
        method, f"{SUPABASE_URL}/rest/v1{path}",
        params=params, json=json, headers=headers, timeout=20.0,
    )
    r.raise_for_status()
    return r.json() if r.content else []


# ---------------- SQLite ----------------

def _sql():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def _sql_last_price(product_id, store):
    with _sql() as con:
        row = con.execute(
            "SELECT price FROM prices WHERE product_id=? AND store=? ORDER BY ts DESC LIMIT 1",
            (product_id, store),
        ).fetchone()
        return row


# ---------------- Interface pública ----------------

def init():
    if USE_SUPABASE:
        return  # tabelas criadas via schema.sql no SQL Editor do Supabase
    with _sql() as con:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS products (
                product_id TEXT NOT NULL, store TEXT NOT NULL,
                name TEXT, brand TEXT, unit TEXT, url TEXT, image TEXT,
                price REAL, price_per_unit REAL, updated_at TEXT,
                PRIMARY KEY (product_id, store)
            );
            CREATE TABLE IF NOT EXISTS prices (
                product_id TEXT NOT NULL, store TEXT NOT NULL, ts TEXT NOT NULL,
                price REAL, price_per_unit REAL,
                PRIMARY KEY (product_id, store, ts)
            );
            """
        )


def upsert_product(p):
    row = _product_row(p)
    if USE_SUPABASE:
        _sb("POST", "/products", json=row)
        return
    with _sql() as con:
        con.execute(
            """INSERT INTO products(product_id, store, name, brand, unit, url, image, price, price_per_unit, updated_at)
               VALUES(:product_id,:store,:name,:brand,:unit,:url,:image,:price,:price_per_unit,:updated_at)
               ON CONFLICT(product_id, store) DO UPDATE SET
                 name=excluded.name, brand=excluded.brand, unit=excluded.unit, url=excluded.url,
                 image=excluded.image, price=excluded.price, price_per_unit=excluded.price_per_unit,
                 updated_at=excluded.updated_at""",
            row,
        )


def snapshot_price(p):
    """Guarda um ponto no histórico apenas se o preço mudou. Devolve True se mudou."""
    if p.get("price") is None:
        return False
    price = float(p["price"])
    if USE_SUPABASE:
        last = _sb(
            "GET", "/prices",
            params={
                "product_id": f"eq.{p['product_id']}",
                "store": f"eq.{p['store']}",
                "order": "ts.desc",
                "limit": "1",
                "select": "price",
            },
        )
        if last and float(last[0]["price"]) == price:
            return False
        _sb("POST", "/prices", json={
            "product_id": p["product_id"], "store": p["store"],
            "ts": _now(), "price": price, "price_per_unit": p.get("price_per_unit"),
        })
        return True
    last = _sql_last_price(p["product_id"], p["store"])
    if last is not None and last["price"] == price:
        return False
    with _sql() as con:
        con.execute(
            "INSERT OR REPLACE INTO prices(product_id, store, ts, price, price_per_unit) VALUES (?,?,?,?,?)",
            (p["product_id"], p["store"], _now(), price, p.get("price_per_unit")),
        )
    return True


def history(product_id, store, limit=30):
    if USE_SUPABASE:
        return _sb("GET", "/prices", params={
            "product_id": f"eq.{product_id}", "store": f"eq.{store}",
            "order": "ts.desc", "limit": str(limit),
        })
    with _sql() as con:
        rows = con.execute(
            "SELECT ts, price, price_per_unit FROM prices WHERE product_id=? AND store=? ORDER BY ts DESC LIMIT ?",
            (product_id, store, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def products(store=None, q=None, limit=50):
    if USE_SUPABASE:
        params = {"select": "*", "order": "name.asc", "limit": str(limit)}
        if store:
            params["store"] = f"eq.{store}"
        if q:
            params["name"] = f"ilike.*{q}*"
        return _sb("GET", "/products", params=params)
    sql = "SELECT * FROM products"
    where, args = [], []
    if store:
        where.append("store = ?"); args.append(store)
    if q:
        where.append("name LIKE ?"); args.append(f"%{q}%")
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY name LIMIT ?"
    args.append(limit)
    with _sql() as con:
        return [dict(r) for r in con.execute(sql, args).fetchall()]
