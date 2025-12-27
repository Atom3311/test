-- Supabase schema (placeholders)

create table if not exists public.users (
  id text primary key,
  username text,
  display_name text,
  photo_url text,
  badges text[] default '{}',
  season text default 'Зима 2025',
  achievements text default '0/30',
  created_at timestamp with time zone default now()
);

create table if not exists public.progress (
  user_id text primary key references public.users(id) on delete cascade,
  data jsonb default '{}'::jsonb,
  updated_at timestamp with time zone default now()
);

create table if not exists public.boosts (
  id text primary key,
  title text not null,
  description text not null,
  price_rub integer not null,
  is_paid boolean default true
);

create table if not exists public.purchases (
  id bigserial primary key,
  user_id text references public.users(id) on delete cascade,
  boost_id text references public.boosts(id),
  status text default 'pending',
  created_at timestamp with time zone default now()
);
