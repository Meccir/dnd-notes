create table if not exists encounters (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  round int not null default 1,
  turn_index int not null default 0,   -- кто сейчас ходит (индекс в списке)
  created_at timestamptz not null default now()
);

create table if not exists combatants (
  id uuid primary key default gen_random_uuid(),
  encounter_id uuid not null references encounters(id) on delete cascade,
  name text not null,
  initiative int not null default 0,
  hp int not null default 1,
  max_hp int not null default 1,
  side text not null default 'enemy' check (side in ('party','enemy')),
  conditions text[] not null default '{}'
);

create index if not exists combatants_encounter_idx on combatants(encounter_id);

-- Партии (кампании): список и заметки
create table if not exists campaigns (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  notes text not null default '',
  created_at timestamptz not null default now()
);

-- Отдельные кампании лора и карточки справочника
create table if not exists lore_campaigns (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  created_at timestamptz not null default now()
);

create table if not exists lore_cards (
  id uuid primary key default gen_random_uuid(),
  campaign_id uuid not null references lore_campaigns(id) on delete cascade,
  kind text not null check (kind in ('character', 'place', 'description')),
  title text not null,
  content text not null default '',
  created_at timestamptz not null default now()
);

create index if not exists lore_cards_campaign_idx on lore_cards(campaign_id);