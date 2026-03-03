CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password VARCHAR(255) NOT NULL
);

-- Chat threads table
CREATE TABLE IF NOT EXISTS chat_threads (
  id VARCHAR(36) PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Chat messages table
CREATE TABLE IF NOT EXISTS chat_messages (
  id VARCHAR(36) PRIMARY KEY,
  thread_id VARCHAR(36) REFERENCES chat_threads(id) ON DELETE CASCADE,
  role VARCHAR(20) NOT NULL,  -- 'user' or 'bot'
  content TEXT NOT NULL,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  api_role VARCHAR(50),
  suggestions JSONB,
  summary TEXT,
  need_clarify BOOLEAN,
  input_type VARCHAR(50)
);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_messages_thread_id ON chat_messages(thread_id);
CREATE INDEX IF NOT EXISTS idx_threads_user_id ON chat_threads(user_id);
