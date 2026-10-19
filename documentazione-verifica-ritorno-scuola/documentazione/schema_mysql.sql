-- Schema-only recreation of verifica_ritorno_scuola.
-- No application data is included and no existing database is dropped.
-- Requires MySQL 8.0.16+ for enforced CHECK constraints.

CREATE DATABASE IF NOT EXISTS `verifica_ritorno_scuola`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `verifica_ritorno_scuola`;

CREATE TABLE `alembic_version` (
  `version_num` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `categoria` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nome_categoria` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `descrizione` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_categoria_nome` (`nome_categoria`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `quartiere` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nome_quartiere` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
  `cap_zona` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '00000',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_quartiere_nome_cap` (`nome_quartiere`, `cap_zona`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `utente` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nome` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `cognome` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(254) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password_hash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `tipo_ruolo` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'Cittadino',
  `data_registrazione` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `fk_quartiere` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_utente_email` (`email`),
  KEY `idx_utente_email` (`email`),
  KEY `fk_utente_quartiere` (`fk_quartiere`),
  CONSTRAINT `fk_utente_quartiere` FOREIGN KEY (`fk_quartiere`)
    REFERENCES `quartiere` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `ck_utente_ruolo`
    CHECK (`tipo_ruolo` IN ('Cittadino', 'MembroComitato', 'Admin'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `dossier` (
  `id` int NOT NULL AUTO_INCREMENT,
  `titolo` varchar(180) COLLATE utf8mb4_unicode_ci NOT NULL,
  `data_creazione` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `note_comitato` text COLLATE utf8mb4_unicode_ci,
  `fk_utente_creatore` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_utente_creatore` (`fk_utente_creatore`),
  CONSTRAINT `dossier_ibfk_1` FOREIGN KEY (`fk_utente_creatore`)
    REFERENCES `utente` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `segnalazione` (
  `id` int NOT NULL AUTO_INCREMENT,
  `titolo` varchar(180) COLLATE utf8mb4_unicode_ci NOT NULL,
  `descrizione_testuale` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `latitudine` decimal(9,6) NOT NULL,
  `longitudine` decimal(9,6) NOT NULL,
  `indirizzo` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `data_creazione` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `stato_attuale` varchar(40) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'Inviata',
  `fk_utente_autore` int NOT NULL,
  `fk_categoria` int NOT NULL,
  `fk_quartiere` int NOT NULL,
  `fk_segnalazione_padre` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_segnalazione_filtri` (`fk_quartiere`, `fk_categoria`, `stato_attuale`, `data_creazione`),
  KEY `fk_segnalazione_autore` (`fk_utente_autore`),
  KEY `fk_segnalazione_categoria` (`fk_categoria`),
  KEY `fk_segnalazione_padre` (`fk_segnalazione_padre`),
  CONSTRAINT `fk_segnalazione_autore` FOREIGN KEY (`fk_utente_autore`)
    REFERENCES `utente` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_segnalazione_categoria` FOREIGN KEY (`fk_categoria`)
    REFERENCES `categoria` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_segnalazione_quartiere` FOREIGN KEY (`fk_quartiere`)
    REFERENCES `quartiere` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_segnalazione_padre` FOREIGN KEY (`fk_segnalazione_padre`)
    REFERENCES `segnalazione` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `ck_segnalazione_latitudine`
    CHECK (`latitudine` >= -90 AND `latitudine` <= 90),
  CONSTRAINT `ck_segnalazione_longitudine`
    CHECK (`longitudine` >= -180 AND `longitudine` <= 180),
  CONSTRAINT `ck_segnalazione_stato`
    CHECK (`stato_attuale` IN ('Inviata', 'Approvata', 'Presa in Carico', 'Inclusa nel Dossier', 'Risolta'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `allegato_multimediale` (
  `id` int NOT NULL AUTO_INCREMENT,
  `url_file` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `tipo_file` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `data_upload` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `fk_segnalazione` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_allegato_segnalazione` (`fk_segnalazione`),
  CONSTRAINT `fk_allegato_segnalazione` FOREIGN KEY (`fk_segnalazione`)
    REFERENCES `segnalazione` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `ck_allegato_tipo` CHECK (`tipo_file` IN ('Foto', 'Video'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `dossier_segnalazione` (
  `fk_dossier` int NOT NULL,
  `fk_segnalazione` int NOT NULL,
  `data_inserimento` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`fk_dossier`, `fk_segnalazione`),
  KEY `fk_segnalazione` (`fk_segnalazione`),
  CONSTRAINT `dossier_segnalazione_ibfk_1` FOREIGN KEY (`fk_dossier`)
    REFERENCES `dossier` (`id`) ON DELETE CASCADE,
  CONSTRAINT `dossier_segnalazione_ibfk_2` FOREIGN KEY (`fk_segnalazione`)
    REFERENCES `segnalazione` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sostegno` (
  `id` int NOT NULL AUTO_INCREMENT,
  `data_voto` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `fk_utente` int NOT NULL,
  `fk_segnalazione` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sostegno_utente_segnalazione` (`fk_utente`, `fk_segnalazione`),
  KEY `fk_segnalazione` (`fk_segnalazione`),
  CONSTRAINT `sostegno_ibfk_1` FOREIGN KEY (`fk_utente`)
    REFERENCES `utente` (`id`) ON DELETE CASCADE,
  CONSTRAINT `sostegno_ibfk_2` FOREIGN KEY (`fk_segnalazione`)
    REFERENCES `segnalazione` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- The inspected database had no Alembic revision recorded.
-- After importing this file into the intended empty database, point DATABASE_URL
-- to it and run: flask --app run.py db stamp head