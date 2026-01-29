-- SQL-схема для таблицы пользователей.
-- Этот код нужно выполнить в вашем редакторе Supabase SQL.

CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY, -- ID пользователя из Telegram
    username TEXT, -- Username пользователя из Telegram
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Краткое резюме о пользователе, обновляется LLM
    summary TEXT,
    
    -- Текущая тема для терапии
    focus TEXT DEFAULT 'общее',
    
    -- Цель на текущую сессию
    session_goal TEXT,
    
    -- Результат последней сессии
    last_outcome TEXT,

    -- Профиль пользователя
    display_name TEXT,
    gender TEXT,
    age INT,
    about TEXT,
    
    -- Флаги состояний FSM (Finite State Machine)
    awaiting_checkin BOOLEAN DEFAULT FALSE,
    awaiting_goal BOOLEAN DEFAULT FALSE,
    awaiting_outcome BOOLEAN DEFAULT FALSE,
    awaiting_gender BOOLEAN DEFAULT FALSE,
    awaiting_name BOOLEAN DEFAULT FALSE,
    awaiting_age BOOLEAN DEFAULT FALSE,
    awaiting_about BOOLEAN DEFAULT FALSE,

    -- Данные для управления состоянием пользователя
    distress_streak INT DEFAULT 0,
    last_distress_at TIMESTAMPTZ,
    last_support_offer_at TIMESTAMPTZ,
    last_checkin_prompt_at TIMESTAMPTZ,
    last_message_at TIMESTAMPTZ,

    -- Данные для суммаризации
    messages_since_summary INT DEFAULT 0,
    last_summary_at TIMESTAMPTZ
);

-- Таблица для хранения истории сообщений
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    role TEXT NOT NULL, -- 'user' или 'assistant'
    content TEXT NOT NULL
);

-- Индекс для ускорения выборки сообщений по пользователю
CREATE INDEX IF NOT EXISTS idx_messages_user_id_created_at ON messages(user_id, created_at DESC);

-- Таблица для хранения чек-инов (оценок состояния)
CREATE TABLE IF NOT EXISTS checkins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    mood INT NOT NULL,
    anxiety INT NOT NULL,
    energy INT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_checkins_user_id_created_at ON checkins(user_id, created_at DESC);


-- Политики безопасности Supabase (Row Level Security)
-- Убедитесь, что RLS включен для таблиц.

-- Включаем RLS (если еще не включен)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE checkins ENABLE ROW LEVEL SECURITY;

-- Политика для users: разрешает пользователям читать и изменять только свои собственные данные.
DROP POLICY IF EXISTS "Users can view and manage their own data." ON users;
CREATE POLICY "Users can view and manage their own data."
ON users
FOR ALL
USING (auth.uid()::text = id::text)
WITH CHECK (auth.uid()::text = id::text);

-- Политика для messages: разрешает пользователям работать только со своими сообщениями.
DROP POLICY IF EXISTS "Users can view and manage their own messages." ON messages;
CREATE POLICY "Users can view and manage their own messages."
ON messages
FOR ALL
USING (
    EXISTS (
        SELECT 1
        FROM users
        WHERE users.id = messages.user_id
          AND users.id::text = auth.uid()::text
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1
        FROM users
        WHERE users.id = messages.user_id
          AND users.id::text = auth.uid()::text
    )
);

-- Политика для checkins: разрешает пользователям работать только со своими чек-инами.
DROP POLICY IF EXISTS "Users can view and manage their own checkins." ON checkins;
CREATE POLICY "Users can view and manage their own checkins."
ON checkins
FOR ALL
USING (
    EXISTS (
        SELECT 1
        FROM users
        WHERE users.id = checkins.user_id
          AND users.id::text = auth.uid()::text
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1
        FROM users
        WHERE users.id = checkins.user_id
          AND users.id::text = auth.uid()::text
    )
);


-- ПРИМЕЧАНИЕ: Для аутентификации на уровне строк (RLS) вам потребуется
-- настроить JWT-токен от Telegram для аутентификации в Supabase.
-- На начальном этапе миграции можно временно отключить RLS для таблиц,
-- пока не будет настроена полная аутентификация.
-- В коде бота мы будем использовать сервисный ключ (service_role_key),
-- который обходит RLS, но настройка RLS - это хорошая практика безопасности.

-- RPC-функция для атомарного инкремента счетчика сообщений
CREATE OR REPLACE FUNCTION increment_messages_counter(user_id_param BIGINT)
RETURNS void AS $$
BEGIN
  UPDATE users
  SET messages_since_summary = messages_since_summary + 1
  WHERE id = user_id_param;
END;
$$ LANGUAGE plpgsql;
