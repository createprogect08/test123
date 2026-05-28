-- ============================================================
-- MARISA EXPRESS — Schema unificato
-- Database: marisa_express_db
-- ============================================================

CREATE DATABASE IF NOT EXISTS marisa_express_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE marisa_express_db;

-- ------------------------------------------------------------
-- UTENTI
-- Tabella centrale: utenti normali, rider e ristoratori
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS utenti (
    id              INT             AUTO_INCREMENT PRIMARY KEY,
    nome            VARCHAR(100)    NOT NULL,
    email           VARCHAR(150)    NOT NULL UNIQUE,
    password_hash   VARCHAR(255)    NOT NULL,
    telefono        VARCHAR(20),
    tipo            ENUM('utente','rider','ristoratore') NOT NULL DEFAULT 'utente',
    crediti         DECIMAL(10,2)   NOT NULL DEFAULT 0.00,
    foto_profilo    VARCHAR(255),
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- RISTORANTI
-- Un utente di tipo 'ristoratore' possiede uno o più ristoranti
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ristoranti (
    id              INT             AUTO_INCREMENT PRIMARY KEY,
    id_utente       INT             NOT NULL,
    nome            VARCHAR(150)    NOT NULL,
    descrizione     VARCHAR(300),
    via             VARCHAR(255),
    lat             DECIMAL(10,7),
    lng             DECIMAL(10,7),
    foto_profilo    VARCHAR(255)    NULL,
    partita_iva     VARCHAR(20),
    categoria       VARCHAR(100),
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_ristoranti_utente
        FOREIGN KEY (id_utente) REFERENCES utenti(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- MENU ITEMS
-- Ogni piatto/prodotto appartiene a un ristorante
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS menu_items (
    id              INT             AUTO_INCREMENT PRIMARY KEY,
    id_ristorante   INT             NOT NULL,
    nome            VARCHAR(150)    NOT NULL,
    descrizione     TEXT,
    prezzo          DECIMAL(8,2)    NOT NULL,
    foto            VARCHAR(255),
    categoria       VARCHAR(100),
    disponibile     TINYINT(1)      NOT NULL DEFAULT 1,
    CONSTRAINT fk_menu_ristorante
        FOREIGN KEY (id_ristorante) REFERENCES ristoranti(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- ORDINI
-- Ogni ordine è collegato a utente, ristorante e (opzionalmente) rider
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ordini (
    id                  INT             AUTO_INCREMENT PRIMARY KEY,
    id_utente           INT             NOT NULL,
    id_ristorante       INT             NOT NULL,
    id_rider            INT,
    stato               ENUM(
                            'pending_stripe',
                            'in_attesa',
                            'accettato',
                            'in_consegna',
                            'sotto_casa',
                            'consegnato',
                            'rifiutato'
                        ) NOT NULL DEFAULT 'in_attesa',
    totale              DECIMAL(10,2)   NOT NULL,
    indirizzo_consegna  VARCHAR(255),
    lat_consegna        DECIMAL(10,7),
    lng_consegna        DECIMAL(10,7),
    token_consegna      VARCHAR(10),
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_ordini_utente
        FOREIGN KEY (id_utente) REFERENCES utenti(id),
    CONSTRAINT fk_ordini_ristorante
        FOREIGN KEY (id_ristorante) REFERENCES ristoranti(id),
    CONSTRAINT fk_ordini_rider
        FOREIGN KEY (id_rider) REFERENCES utenti(id)
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- ORDINI ITEMS
-- Righe di dettaglio di ogni ordine (prodotti + quantità + prezzo snapshot)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ordini_items (
    id              INT             AUTO_INCREMENT PRIMARY KEY,
    id_ordine       INT             NOT NULL,
    id_menu_item    INT             NOT NULL,
    quantita        INT             NOT NULL DEFAULT 1,
    prezzo_unitario DECIMAL(8,2)    NOT NULL,
    CONSTRAINT fk_ordini_items_ordine
        FOREIGN KEY (id_ordine) REFERENCES ordini(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_ordini_items_menu
        FOREIGN KEY (id_menu_item) REFERENCES menu_items(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- WALLET TRANSAZIONI
-- Storico movimenti crediti: ricariche, pagamenti, rimborsi
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS wallet_transazioni (
    id                  INT             AUTO_INCREMENT PRIMARY KEY,
    id_utente           INT             NOT NULL,
    importo             DECIMAL(10,2)   NOT NULL,
    tipo                ENUM('ricarica','pagamento','rimborso') NOT NULL,
    stripe_session_id   VARCHAR(255)    NULL,
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_wallet_utente
        FOREIGN KEY (id_utente) REFERENCES utenti(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- RIDERS
-- Profilo completo del rider: anagrafica, veicolo, posizione, disponibilità
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS riders (
    id              INT             AUTO_INCREMENT PRIMARY KEY,
    id_utente       INT             NOT NULL UNIQUE,
    nome            VARCHAR(30),
    codice_fiscale  VARCHAR(16)     NOT NULL UNIQUE,
    veicolo         VARCHAR(100),
    targa           VARCHAR(20),
    foto_profilo    VARCHAR(255),
    telefono        VARCHAR(20),
    zona            VARCHAR(100),
    lat             DECIMAL(10,7),
    lng             DECIMAL(10,7),
    disponibile     TINYINT(1)      NOT NULL DEFAULT 1,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_riders_utente
        FOREIGN KEY (id_utente) REFERENCES utenti(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- TOKEN BLACKLIST
-- JWT invalidati al logout (pulizia periodica consigliata)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS token_blacklist (
    id          INT             AUTO_INCREMENT PRIMARY KEY,
    token       TEXT            NOT NULL,
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_token_blacklist_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- INDICI AGGIUNTIVI (performance)
-- ============================================================

-- Ricerca ordini per stato
CREATE INDEX idx_ordini_stato        ON ordini(stato);
-- Ordini di un utente ordinati per data
CREATE INDEX idx_ordini_utente_data  ON ordini(id_utente, created_at DESC);
-- Ordini assegnati a un rider
CREATE INDEX idx_ordini_rider        ON ordini(id_rider);
-- Prodotti di un ristorante disponibili
CREATE INDEX idx_menu_disponibile    ON menu_items(id_ristorante, disponibile);
-- Transazioni wallet per utente
CREATE INDEX idx_wallet_utente       ON wallet_transazioni(id_utente, created_at DESC);
-- Ricerca ristoranti per categoria
CREATE INDEX idx_ristoranti_cat      ON ristoranti(categoria);
