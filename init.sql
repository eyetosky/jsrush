-- JS Rush Database Initialization
-- Run this on first database creation

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create indexes for better performance
-- These will be created by SQLAlchemy but we add them here for reference

-- User indexes
-- CREATE INDEX IF NOT EXISTS ix_user_email ON "user" (email);
-- CREATE INDEX IF NOT EXISTS ix_user_username ON "user" (username);
-- CREATE INDEX IF NOT EXISTS ix_user_email_verified ON "user" (email_verified);
-- CREATE INDEX IF NOT EXISTS ix_user_kyc_status ON "user" (kyc_status);
-- CREATE INDEX IF NOT EXISTS ix_user_is_active ON "user" (is_active);

-- Transaction indexes
-- CREATE INDEX IF NOT EXISTS ix_transaction_user_id ON "transaction" (user_id);
-- CREATE INDEX IF NOT EXISTS ix_transaction_type ON "transaction" (type);
-- CREATE INDEX IF NOT EXISTS ix_transaction_timestamp ON "transaction" (timestamp DESC);
-- CREATE INDEX IF NOT EXISTS ix_transaction_reference ON "transaction" (reference);
-- CREATE INDEX IF NOT EXISTS ix_transaction_gateway_reference ON "transaction" (gateway_reference);

-- Game session indexes
-- CREATE INDEX IF NOT EXISTS ix_game_session_user_id ON "game_session" (user_id);
-- CREATE INDEX IF NOT EXISTS ix_game_session_game_type ON "game_session" (game_type);
-- CREATE INDEX IF NOT EXISTS ix_game_session_started_at ON "game_session" (started_at DESC);

-- Audit log indexes
-- CREATE INDEX IF NOT EXISTS ix_audit_log_user_id ON "audit_log" (user_id);
-- CREATE INDEX IF NOT EXISTS ix_audit_log_admin_id ON "audit_log" (admin_id);
-- CREATE INDEX IF NOT EXISTS ix_audit_log_timestamp ON "audit_log" (timestamp DESC);

-- KYC document indexes
-- CREATE INDEX IF NOT EXISTS ix_kyc_document_user_id ON "kyc_document" (user_id);
-- CREATE INDEX IF NOT EXISTS ix_kyc_document_status ON "kyc_document" (status);

-- Game session indexes
-- CREATE INDEX IF NOT EXISTS ix_game_session_user_id_started ON "game_session" (user_id, started_at DESC);

-- Responsible gambling log indexes
-- CREATE INDEX IF NOT EXISTS ix_responsible_gambling_log_user_id ON "responsible_gambling_log" (user_id);
-- CREATE INDEX IF NOT EXISTS ix_responsible_gambling_log_timestamp ON "responsible_gambling_log" (timestamp DESC);

-- Create a view for user stats
CREATE OR REPLACE VIEW user_stats AS
SELECT 
    u.id,
    u.username,
    u.email,
    u.balance,
    u.kyc_status,
    u.kyc_level,
    u.created_at,
    u.last_login,
    COUNT(t.id) as total_transactions,
    COALESCE(SUM(CASE WHEN t.type = 'deposit' THEN t.amount ELSE 0 END), 0) as total_deposits,
    COALESCE(SUM(CASE WHEN t.type = 'withdraw' THEN t.amount ELSE 0 END), 0) as total_withdrawals,
    COALESCE(SUM(CASE WHEN t.type = 'game' THEN t.amount ELSE 0 END), 0) as total_game_winnings,
    COUNT(CASE WHEN t.type = 'game' AND t.amount > 0 THEN 1 END) as game_wins,
    COUNT(CASE WHEN t.type = 'game' AND t.amount < 0 THEN 1 END) as game_losses
FROM "user" u
LEFT JOIN "transaction" t ON u.id = t.user_id
GROUP BY u.id;

-- Create a view for daily stats
CREATE OR REPLACE VIEW daily_stats AS
SELECT 
    DATE(timestamp) as date,
    COUNT(DISTINCT user_id) as active_users,
    COUNT(*) FILTER (WHERE type = 'deposit' AND amount > 0) as deposit_count,
    COALESCE(SUM(amount) FILTER (WHERE type = 'deposit' AND amount > 0), 0) as total_deposits,
    COUNT(*) FILTER (WHERE type = 'withdraw' AND amount < 0) as withdrawal_count,
    COALESCE(ABS(SUM(amount)) FILTER (WHERE type = 'withdraw' AND amount < 0), 0) as total_withdrawals,
    COUNT(*) FILTER (WHERE type = 'game') as game_count,
    COALESCE(SUM(amount) FILTER (WHERE type = 'game'), 0) as game_net
FROM "transaction"
GROUP BY DATE(timestamp)
ORDER BY date DESC;

-- Grant permissions (run as superuser if needed)
-- GRANT SELECT ON user_stats TO jsrush;
-- GRANT SELECT ON daily_stats TO jsrush;