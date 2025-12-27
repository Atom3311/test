-- Seed data for boosts
insert into public.boosts (id, title, description, price_rub, is_paid)
values
  ('frostpack', 'Набор Мороза', 'x3 на 60 сек', 99, true),
  ('aurora', 'Северное сияние', '+20 монет/сек', 149, true),
  ('legend', 'Легендарный снег', 'Супер-награды 5 мин', 249, true)
ON CONFLICT (id) DO NOTHING;
