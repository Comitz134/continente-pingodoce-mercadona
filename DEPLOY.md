# Publicar a app (Supabase + GitHub Pages)

A app é 100% estática: vive no GitHub Pages. Os preços reais vêm do Supabase
(Postgres) e são preenchidos por um workflow agendado que corre os scrapers.

```
[GitHub Actions: scrape.yml]  ──►  Supabase (products/prices)
        (de 6 em 6 h)                    ▲
                                          │ lê (chave anon)
                                   [GitHub Pages] receitas/
```

## 1. Supabase (base de dados)

1. Cria um projeto em https://supabase.com (grátis).
2. SQL Editor → cola e corre o conteúdo de `backend/schema.sql`.
3. Anota:
   - **Project URL** (ex.: `https://xyzcompany.supabase.co`) → `SUPABASE_URL`
   - **Chave `service_role`** (Settings → API) → `SUPABASE_SERVICE_KEY` (só backend)
   - **Chave `anon/public`** (Settings → API) → `SUPABASE_ANON_KEY` (vai para a app)

## 2. GitHub

1. Cria um repositório e faz push deste projeto (a pasta `receitas/`, `backend/`
   e `.github/`).
2. Repo → **Settings → Secrets and variables → Actions → New repository secret**:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_KEY`
   - `SUPABASE_ANON_KEY`
3. Repo → **Settings → Pages → Source = GitHub Actions**.

Feito: o workflow `pages.yml` publica a app e injeta o Supabase na app; o
`scrape.yml` corre de 6 em 6 horas e enche a base de dados.

Abre o link (Settings → Pages) no telemóvel → **Adicionar ao ecrã principal**.

## 3. Testar os scrapers localmente

```bash
cd backend
pip install -r requirements.txt
python run_scrape.py                          # usa SQLite local (prices.db)
SUPABASE_URL=... SUPABASE_SERVICE_KEY=... python run_scrape.py   # usa Supabase
```

- **Mercadona**: Algolia (endpoint verificado; índice de ES — para PT copia o
  índice/App ID/API key do mercadona.pt no DevTools para `config.py`).
- **Continente**: `continente.pt/pesquisa/?q=` — produtos em
  `data-product-tile-impression` (verificado).
- **Pingo Doce**: `pingodoce.pt/home/produtos?q=` — tiles com `data-pid`,
  preço e €/Kg (verificado).

## 4. Como a app usa os preços

- No carrinho, cada ingrediente pesquisa o produto mais barato por loja no
  Supabase e mostra o **preço real + link para o produto** (selo "preço real").
- Se o Supabase estiver vazio/offline, a app usa os preços curados
  (`precos.js`) — nunca fica sem preços.

## Limitações (importante)

- São endpoints **internos** (não públicos): mudam e o uso pode contrariar os
  termos dos sites. Uso pessoal, com intervalos razoáveis.
- O "casamento" ingrediente→produto em v1 escolhe o **produto mais barato** que
  contenha o nome do ingrediente, ao preço da **embalagem** (não escala à grama
  exata). Para escalar bem, o passo seguinte é usar o `price_per_unit` (€/Kg)
  que a Mercadona e o Pingo Doce já expõem — o Continente exige ir à página do
  produto.
