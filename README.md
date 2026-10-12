
Puoi aggiungere i dati territoriali reali con i comandi:

```bash
flask --app run.py add-quartiere --nome "Centro Storico" --cap "00100"
flask --app run.py add-categoria --nome "Mobilità" --descrizione "Strade, marciapiedi e trasporto pubblico"
```
# Verifica Ritorno Scuola

Applicazione web civica in italiano per segnalazioni territoriali, sostegni, moderazione e dossier. Lo stack implementato è Python/Flask, MySQL 8, HTML/Jinja, CSS, JavaScript e Bootstrap 5.

## Requisiti

- Python 3.11 o superiore
- MySQL 8.0 o 8.4, oppure Docker con Docker Compose
- Facoltativo: un browser moderno

## Avvio locale con MySQL

1. Crea un database e un utente MySQL con permessi sul database:

```sql
CREATE DATABASE verifica_ritorno_scuola CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'verifica_user'@'127.0.0.1' IDENTIFIED BY 'imposta-una-password-locale';
GRANT ALL PRIVILEGES ON verifica_ritorno_scuola.* TO 'verifica_user'@'127.0.0.1';
```

2. Crea un ambiente virtuale, installa le dipendenze e configura le variabili:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Aggiorna `DATABASE_URL`, `SECRET_KEY` e `JWT_SECRET_KEY` in `.env`. Usa valori casuali e non inserire il file `.env` in Git.

3. Crea lo schema e i dati iniziali:

```bash
flask --app run.py db upgrade
flask --app run.py seed-data
flask --app run.py create-admin
```

Il comando `seed-data` crea categorie generiche e un quartiere segnaposto (`Da configurare`, CAP `00000`). Prima dell’uso reale, sostituisci il segnaposto con i quartieri e CAP del comune tramite il database.

4. Avvia il server di sviluppo:

```bash
flask --app run.py run --debug
```

Apri http://127.0.0.1:5000. Per produzione usa HTTPS, imposta `JWT_COOKIE_SECURE=1`, configura chiavi segrete robuste e avvia Gunicorn dietro un reverse proxy.

## Avvio con Docker Compose

Copia `.env.example` in `.env`, imposta anche `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD` e `MYSQL_ROOT_PASSWORD`, poi avvia:

```bash
docker compose up --build -d
```

L’applicazione è disponibile su `http://localhost:8000` (o sulla porta definita da `APP_PORT`). Per creare il primo amministratore:

```bash
docker compose exec web flask --app run.py create-admin
```

I dati MySQL e gli upload sono conservati in volumi Docker. Per fermare i servizi senza cancellare i dati usa `docker compose down`; non usare `-v` se vuoi conservarli.

## Migrazioni

Dopo una modifica ai modelli:

```bash
flask --app run.py db migrate -m "descrizione modifica"
flask --app run.py db upgrade
```

Rivedi sempre la migrazione generata prima di applicarla a dati esistenti.

## Test

```bash
pytest
```

I test usano SQLite isolato e non richiedono MySQL. In produzione l’applicazione usa MySQL tramite `DATABASE_URL`.

## Funzioni incluse

- Consultazione pubblica con filtri per quartiere, categoria e stato e paginazione.
- Registrazione, login JWT con cookie HttpOnly, profilo e protezione CSRF per i form.
- Segnalazioni con autorizzazione per proprietario/ruolo, upload con limite configurabile e controllo dei formati.
- Sostegni univoci per utente/segnalazione; la chiave univoca nel database gestisce anche richieste concorrenti.
- Moderazione, collegamento dei duplicati con controllo dei cicli, gestione dei dossier e dei ruoli amministrativi.
- Endpoint `/health` per verificare la disponibilità del database.

I riferimenti a PostgreSQL/Node.js presenti in alcuni documenti descrivono lo stato precedente del progetto: il codice applicativo e questo README usano MySQL e Python come richiesto. Le transizioni di stato non definite nella documentazione sono attualmente affidate a membri del comitato e amministratori senza workflow più restrittivi.
