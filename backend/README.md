# Backend de preços (Continente · Pingo Doce · Mercadona)

Implementa a tua **opção 2** (APIs internas) + histórico de preços, com
**SQLite** em vez de Postgres (chega para uso pessoal e não precisa de servidor
de base de dados).

Fluxo:

```
mercadoria.pt / continente.pt / pingodoce.pt
        │  (endpoint interno: JSON)
        ▼
   scrapers.py  ──►  db.py (SQLite: products + prices)
        ▲                    │
        └──── run_scrape.py  │  (cron)
                             ▼
                     main.py (FastAPI)
                             │
                     a tua app (ainda não ligada)
```

## Correr

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

- `GET /api/health`
- `GET /api/search?q=arroz&store=mercadona_es` — pesquisa ao vivo e regista o preço
- `GET /api/history?product_id=34210&store=mercadona_es` — histórico de preços
- `GET /api/products?q=arroz` — catálogo local
- `python run_scrape.py` — recolhe um lote e guarda histórico (agendar via cron/Task Scheduler)

## O que já funciona

- **Mercadona** via Algolia (endpoint/App ID/API key em `config.py`, verificados).
  O índice atual é o de Valência (ES). Para Portugal: abre `mercadona.pt` com o
  DevTools aberto (F12 → Network → Fetch/XHR), pesquisa um produto e copia o
  índice `products_prod_*_pt`, o `x-algolia-application-id` e a
  `x-algolia-api-key` para uma nova entrada `mercadona_pt` em `config.py`.

## O que falta (por ordem de esforço)

1. **Mercadona PT**: copiar os 3 valores do DevTools (1 minuto).
2. **Continente**: descobrir o endpoint (Salesforce Commerce Cloud) no
   DevTools e escrever o normalizador em `scrapers.py`.
3. **Pingo Doce**: idem.
4. **Ligar a app**: trocar a tabela estática `precos.js` por chamadas a esta
   API (com fallback para os preços curados quando a API estiver offline).

## Avisos importantes

- Estes são **endpoints internos, não APIs públicas**: mudam sem aviso, podem
  exigir headers/CSRF, e o uso pode contrariar os termos de cada site. Usa
  **apenas para uso pessoal**, com um intervalo razoável entre pedidos.
- `snapshot_price` só guarda um ponto no histórico **quando o preço muda**, por
  isso o histórico fica pequeno e útil (não polui com duplicados).
- Os campos `price`/`unit`/`price_per_unit` vêm do `price_instructions` da
  Mercadona; para Continente/Pingo Doce vais ter de mapear o equivalente no
  JSON de cada um.
