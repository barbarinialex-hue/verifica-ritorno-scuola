# Modello logico

Il modello seguente corrisponde ai [CREATE PostgreSQL](database/02_create_tables.sql). PK = chiave primaria; FK = chiave esterna. I nomi concettuali ID_Quartiere, ID_Utente ecc. diventano `id` nella rispettiva tabella fisica.

| Tabella | Attributi |
| --- | --- |
| quartiere | **id PK**, nome_quartiere, cap_zona |
| categoria | **id PK**, nome_categoria, descrizione |
| utente | **id PK**, nome, cognome, email, password_hash, tipo_ruolo, data_registrazione, **fk_quartiere FK** |
| segnalazione | **id PK**, titolo, descrizione_testuale, latitudine, longitudine, indirizzo, data_creazione, stato_attuale, **fk_utente_autore FK**, **fk_categoria FK**, **fk_quartiere FK**, **fk_segnalazione_padre FK** |
| allegato_multimediale | **id PK**, url_file, tipo_file, data_upload, **fk_segnalazione FK** |
| sostegno | **id PK**, data_voto, **fk_utente FK**, **fk_segnalazione FK** |
| dossier | **id PK**, titolo, data_creazione, note_comitato, **fk_utente_creatore FK** |
| dossier_segnalazione | **fk_dossier PK/FK**, **fk_segnalazione PK/FK**, data_inserimento |

## Relazioni e integrità referenziale

| Chiave esterna | Riferimento | Alla cancellazione del record riferito |
| --- | --- | --- |
| utente.fk_quartiere | quartiere.id | RESTRICT |
| segnalazione.fk_utente_autore | utente.id | RESTRICT |
| segnalazione.fk_categoria | categoria.id | RESTRICT |
| segnalazione.fk_quartiere | quartiere.id | RESTRICT |
| segnalazione.fk_segnalazione_padre | segnalazione.id | SET NULL |
| allegato_multimediale.fk_segnalazione | segnalazione.id | CASCADE |
| sostegno.fk_utente | utente.id | CASCADE |
| sostegno.fk_segnalazione | segnalazione.id | CASCADE |
| dossier.fk_utente_creatore | utente.id | RESTRICT |
| dossier_segnalazione.fk_dossier | dossier.id | CASCADE |
| dossier_segnalazione.fk_segnalazione | segnalazione.id | CASCADE |

Le relazioni 1:N sono realizzate dalla FK nella tabella dal lato N. La relazione N:M tra dossier e segnalazione viene risolta con dossier_segnalazione, la cui PK composta impedisce associazioni duplicate.

## Campi facoltativi

Sono nullable soltanto categoria.descrizione, segnalazione.fk_segnalazione_padre e dossier.note_comitato. Gli altri campi sono obbligatori o valorizzati automaticamente.

## Tipi e vincoli

- ID: INTEGER con generazione automatica; date: TIMESTAMPTZ con valore predefinito corrente.
- Coordinate: NUMERIC(9,6), con intervalli validi per latitudine e longitudine.
- Testi brevi: VARCHAR; descrizioni, hash, note e URL: TEXT.
- UNIQUE: utente.email, categoria.nome_categoria, coppia quartiere(nome_quartiere, cap_zona), coppia sostegno(fk_utente, fk_segnalazione).
- Valori ammessi per ruoli, stati e tipo allegato controllati tramite CHECK.
- Stato iniziale della segnalazione: Inviata; ruolo iniziale: Cittadino.
- La relazione ricorsiva può essere assente, ma non può puntare alla stessa riga. La prevenzione dei cicli fra più righe resta un requisito applicativo.

Gli indici supportano le FK e i filtri di stato/data. Il modello completo dei tipi, delle lunghezze e dei vincoli è lo script SQL collegato sopra; le cardinalità sono nel [modello ER](entita_relazione.md).
