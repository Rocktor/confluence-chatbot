-- Migration script for v2 features
-- Run this on existing databases to add new tables and columns

-- Add new columns to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'user';
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP;

-- Add new columns to conversations table
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS confluence_page_id INTEGER;
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS context_type VARCHAR(50) DEFAULT 'general';

-- Add new column to messages table
ALTER TABLE messages ADD COLUMN IF NOT EXISTS file_urls JSONB DEFAULT '[]';

-- Create user_files table
CREATE TABLE IF NOT EXISTS user_files (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(500) NOT NULL,
    file_path TEXT NOT NULL,
    file_type VARCHAR(100),
    file_size INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create token_usages table
CREATE TABLE IF NOT EXISTS token_usages (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    model VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create login_logs table
CREATE TABLE IF NOT EXISTS login_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    login_type VARCHAR(50) DEFAULT 'dingtalk',
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create system_logs table
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    level VARCHAR(20),
    module VARCHAR(100),
    message TEXT,
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_user_files_user_id ON user_files(user_id);
CREATE INDEX IF NOT EXISTS idx_token_usages_user_id ON token_usages(user_id);
CREATE INDEX IF NOT EXISTS idx_token_usages_created_at ON token_usages(created_at);
CREATE INDEX IF NOT EXISTS idx_login_logs_user_id ON login_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_login_logs_created_at ON login_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level);
CREATE INDEX IF NOT EXISTS idx_system_logs_created_at ON system_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_conversations_confluence_page_id ON conversations(confluence_page_id);

-- Add foreign key constraint (ignore if already exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_conversations_confluence_page'
    ) THEN
        ALTER TABLE conversations
            ADD CONSTRAINT fk_conversations_confluence_page
            FOREIGN KEY (confluence_page_id)
            REFERENCES confluence_pages(id)
            ON DELETE SET NULL;
    END IF;
END $$;

-- Set first user as admin if no admin exists
UPDATE users SET role = 'admin'
WHERE id = (SELECT MIN(id) FROM users)
AND NOT EXISTS (SELECT 1 FROM users WHERE role = 'admin');
