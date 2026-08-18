"""API local (dev) — pesquisa ao vivo e histórico.

A app publicada no GitHub Pages lê do Supabase diretamente (PostgREST); esta
API é útil para desenvolvimento local e para disparar pesquisas sem a app.

Correr:
    pip install -r requirements.txt
    uvicorn main:app --reload
"""

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

import db
import scrapers
from config import STORES


@asynccontextmanager
async def lifespan(_app):
    db.init()
    yield


app = FastAPI(title="Prato da Semana — preços", version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"ok": True, "supabase": db.USE_SUPABASE, "stores": sorted(STORES)}


@app.get("/api/search")
def search(q: str, store: str = Query(default="continente")):
    cfg = STORES.get(store)
    if not cfg:
        raise HTTPException(status_code=404, detail=f"Loja '{store}' não configurada.")
    try:
        results = scrapers.search_store(q, cfg)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Falha ao consultar a loja: {exc}") from exc
    for p in results:
        db.upsert_product(p)
        db.snapshot_price(p)
    return {"query": q, "store": store, "count": len(results), "results": results}


@app.get("/api/history")
def history(product_id: str, store: str):
    return {"product_id": product_id, "store": store, "history": db.history(product_id, store)}


@app.get("/api/products")
def products(
    q: Optional[str] = None,
    store: Optional[str] = None,
    limit: int = Query(default=50, le=200),
):
    return {"products": db.products(store=store, q=q, limit=limit)}
