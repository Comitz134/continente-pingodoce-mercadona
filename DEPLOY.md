# Publicar a app (Supabase + GitHub Pages)

A app é 100% estática: vive no GitHub Pages. Os preços reais vêm do Supabase
(Postgres) e são preenchidos por um workflow agendado que corre os scrapers.

```
[GitHub Actions: scrape.yml]  ──►  Supabase (products/prices)
        (de 6 em 6 h)                    ▲
                                          │ lê (chave anon)
                                   [GitHub Pages] receitas/
```

## Já está configurado (automático)

- `receitas/supabase-config.js` já tem a **URL** e a **chave `anon`** do
  Supabase. Ambas são públicas por design (a chave `anon` só lê, protegida por
  RLS) — a chave `service_role` **nunca** vai para a app.
- `scrape.yml` já aponta para o teu projeto Supabase e corre de 6 em 6 horas.

## Faltam 2 passos únicos (manuais)

### 1. Criar as tabelas no Supabase

1. Abre https://supabase.com → o teu projeto.
2. **SQL Editor** → cola o conteúdo de `backend/schema.sql` → **Run**.

### 2. Adicionar o único segredo (`service_role`)

1. No repositório GitHub → **Settings → Secrets and variables → Actions →
   New repository secret**.
2. **Name**: `SUPABASE_SERVICE_KEY`
3. **Value**: a chave `service_role` do Supabase (começa por `eyJ…` e tem
   `"role":"service_role"`). Guarda-a só aqui — nunca no chat nem no código.

(É o único segredo. A URL do Supabase é pública e já está gravada no workflow.)

## Recolher os preços

- GitHub → **Actions → Recolher preços → Run workflow** (ou espera o
  agendamento de 6 em 6 h).
- Assim que o workflow terminar, abre a app no telemóvel: o carrinho passa a
  mostrar o **preço real + link do produto** por loja, com o selo "preço real".

## Testar os scrapers localmente

```bash
cd backend
pip install -r requirements.txt
python run_scrape.py                          # usa SQLite local (prices.db)
SUPABASE_URL=https://pieijihvcpcqzercvjhb.supabase.co \
SUPABASE_SERVICE_KEY=<service_role> \
python run_scrape.py                          # usa o Supabase
```

## Como a app usa os preços

- No carrinho, cada ingrediente pesquisa o produto mais barato por loja no
  Supabase (`/rest/v1/products`) e mostra o **preço real + link**.
- Se a tabela estiver vazia/offline, a app usa os preços curados
  (`precos.js`) — nunca fica sem preços.

## Limitações (importante)

- São endpoints **internos** (não públicos): mudam e o uso pode contrariar os
  termos dos sites. Uso pessoal, com intervalos razoáveis.
- O "casamento" ingrediente→produto em v1 escolhe o **produto mais barato** que
  contenha o nome do ingrediente, ao preço da **embalagem** (não escala à grama
  exata). O passo seguinte é usar o `price_per_unit` (€/Kg) que a Mercadona e o
  Pingo Doce já expõem — o Continente exige ir à página do produto.
- A Mercadona em `config.py` usa o índice de Valência (ES); para produtos PT
  copia o índice/App ID/API key de `mercadona.pt` (F12 → Network) para uma
  entrada `mercadona_pt`.
