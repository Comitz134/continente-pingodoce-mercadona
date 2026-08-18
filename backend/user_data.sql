-- Dados por utilizador (contas na app): preferências, lista de compras,
-- receitas guardadas e ementas guardadas.
-- Cada utilizador só lê/escreve as próprias linhas (RLS).

create table if not exists public.user_data (
  user_id uuid not null references auth.users(id) on delete cascade,
  key text not null,
  value jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now(),
  primary key (user_id, key)
);

alter table public.user_data enable row level security;

drop policy if exists "own data select" on public.user_data;
create policy "own data select" on public.user_data
  for select using (auth.uid() = user_id);

drop policy if exists "own data insert" on public.user_data;
create policy "own data insert" on public.user_data
  for insert with check (auth.uid() = user_id);

drop policy if exists "own data update" on public.user_data;
create policy "own data update" on public.user_data
  for update using (auth.uid() = user_id);

drop policy if exists "own data delete" on public.user_data;
create policy "own data delete" on public.user_data
  for delete using (auth.uid() = user_id);

grant select, insert, update, delete on public.user_data to authenticated;
