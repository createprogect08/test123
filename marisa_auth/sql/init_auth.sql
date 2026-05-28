-- ============================================================
-- MARISA AUTH — Tabelle specifiche del servizio auth
-- Eseguito dopo init_db.sql (che crea token_blacklist)
-- Questo file è un placeholder per eventuali migrazioni future.
-- ============================================================

USE marisa_express_db;

-- Token invalidati al logout (CREATE IF NOT EXISTS per sicurezza)
CREATE TABLE IF NOT EXISTS token_blacklist (
    id          INT             AUTO_INCREMENT PRIMARY KEY,
    token       TEXT            NOT NULL,
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_token_blacklist_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
