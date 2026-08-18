-- Corre isto no Supabase → SQL Editor (uma vez).
-- As tabelas têm leitura pública (chave anon) para a app; as escritas
-- vêm do scraper com a chave service_role.

create table if not exists public.products (
  product_id      text not null,
  store           text not null,
  name            text,
  brand           text,
  unit            text,
  url             text,
  image           text,
  price           numeric,
  price_per_unit  numeric,
  updated_at      timestamptz default now(),
  primary key (product_id, store)
);

create table if not exists public.prices (
  product_id      text not null,
  store           text not null,
  ts              timestamptz not null default now(),
  price           numeric,
  price_per_unit  numeric,
  primary key (product_id, store, ts)
);

alter table public.products enable row level security;
create policy "leitura publica products" on public.products for select using (true);

alter table public.prices enable row level security;
create policy "leitura publica prices" on public.prices for select using (true);

create index if not exists products_name_idx on public.products (name);
create index if not exists products_store_idx on public.products (store);
