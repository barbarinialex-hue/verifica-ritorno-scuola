CREATE TABLE IF NOT EXISTS quartiere (
  id SERIAL PRIMARY KEY,
  nome_quartiere VARCHAR(120) NOT NULL,
  cap_zona VARCHAR(20) NOT NULL,
  CONSTRAINT uq_quartiere UNIQUE (nome_quartiere, cap_zona)
);

CREATE TABLE IF NOT EXISTS utente (
  id SERIAL PRIMARY KEY,
  nome VARCHAR(80) NOT NULL,
  cognome VARCHAR(80) NOT NULL,
  email VARCHAR(180) NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  tipo_ruolo VARCHAR(40) NOT NULL DEFAULT 'Cittadino'
    CHECK (tipo_ruolo IN ('Cittadino', 'MembroComitato', 'Admin')),
  data_registrazione TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  fk_quartiere INTEGER NOT NULL,
  CONSTRAINT fk_utente_quartiere
    FOREIGN KEY (fk_quartiere) REFERENCES quartiere(id)
    ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS categoria (
  id SERIAL PRIMARY KEY,
  nome_categoria VARCHAR(80) NOT NULL UNIQUE,
  descrizione TEXT
);

CREATE TABLE IF NOT EXISTS segnalazione (
  id SERIAL PRIMARY KEY,
  titolo VARCHAR(160) NOT NULL,
  descrizione_testuale TEXT NOT NULL,
  latitudine DECIMAL(9,6) NOT NULL,
  longitudine DECIMAL(9,6) NOT NULL,
  indirizzo VARCHAR(200) NOT NULL,
  data_creazione TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  stato_attuale VARCHAR(40) NOT NULL DEFAULT 'Inviata'
    CHECK (stato_attuale IN ('Inviata', 'Approvata', 'Presa in carico', 'Inclusa nel dossier', 'Risolta')),
  fk_utente_autore INTEGER NOT NULL,
  fk_categoria INTEGER NOT NULL,
  fk_quartiere INTEGER NOT NULL,
  fk_segnalazione_padre INTEGER,
  CONSTRAINT fk_segnalazione_utente
    FOREIGN KEY (fk_utente_autore) REFERENCES utente(id)
    ON DELETE RESTRICT,
  CONSTRAINT fk_segnalazione_categoria
    FOREIGN KEY (fk_categoria) REFERENCES categoria(id)
    ON DELETE RESTRICT,
  CONSTRAINT fk_segnalazione_quartiere
    FOREIGN KEY (fk_quartiere) REFERENCES quartiere(id)
    ON DELETE RESTRICT,
  CONSTRAINT fk_segnalazione_padre
    FOREIGN KEY (fk_segnalazione_padre) REFERENCES segnalazione(id)
    ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS allegato_multimediale (
  id SERIAL PRIMARY KEY,
  url_file TEXT NOT NULL,
  tipo_file VARCHAR(20) NOT NULL
    CHECK (tipo_file IN ('Foto', 'Video')),
  data_upload TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  fk_segnalazione INTEGER NOT NULL,
  CONSTRAINT fk_allegato_segnalazione
    FOREIGN KEY (fk_segnalazione) REFERENCES segnalazione(id)
    ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sostegno (
  id SERIAL PRIMARY KEY,
  data_voto TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  fk_utente INTEGER NOT NULL,
  fk_segnalazione INTEGER NOT NULL,
  CONSTRAINT uq_sostegno_utente_segnalazione UNIQUE (fk_utente, fk_segnalazione),
  CONSTRAINT fk_sostegno_utente
    FOREIGN KEY (fk_utente) REFERENCES utente(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_sostegno_segnalazione
    FOREIGN KEY (fk_segnalazione) REFERENCES segnalazione(id)
    ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS dossier (
  id SERIAL PRIMARY KEY,
  titolo VARCHAR(200) NOT NULL,
  data_creazione TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  note_comitato TEXT,
  fk_utente_creatore INTEGER NOT NULL,
  CONSTRAINT fk_dossier_utente
    FOREIGN KEY (fk_utente_creatore) REFERENCES utente(id)
    ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS dossier_segnalazione (
  fk_dossier INTEGER NOT NULL,
  fk_segnalazione INTEGER NOT NULL,
  data_inserimento TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (fk_dossier, fk_segnalazione),
  CONSTRAINT fk_dossier_relazione
    FOREIGN KEY (fk_dossier) REFERENCES dossier(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_segnalazione_relazione
    FOREIGN KEY (fk_segnalazione) REFERENCES segnalazione(id)
    ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_segnalazione_fk_quartiere ON segnalazione (fk_quartiere);
CREATE INDEX IF NOT EXISTS idx_segnalazione_fk_categoria ON segnalazione (fk_categoria);
CREATE INDEX IF NOT EXISTS idx_segnalazione_stato ON segnalazione (stato_attuale);
CREATE INDEX IF NOT EXISTS idx_sostegno_fk_segnalazione ON sostegno (fk_segnalazione);
CREATE INDEX IF NOT EXISTS idx_dossier_fk_utente_creatore ON dossier (fk_utente_creatore);
CREATE INDEX IF NOT EXISTS idx_allegato_fk_segnalazione ON allegato_multimediale (fk_segnalazione);
