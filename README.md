
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

Aggiorna `DATABASE_URL`, `SECRET_KEY` e `JWT_SECRET_KEY` in `.env`. Usa valori casuali e non inserire il file `.env` in Git. In produzione imposta `APP_ENV=production`, secret stabili e robusti, `JWT_COOKIE_SECURE=1` e `RATELIMIT_STORAGE_URI` verso uno storage condiviso Redis; l'app rifiuta l'avvio se i secret o lo storage condiviso non sono configurati correttamente.

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

Apri http://127.0.0.1:5000. Login e registrazione hanno limiti per indirizzo IP; lo storage in memoria e adatto solo a sviluppo/test. Per produzione usa HTTPS, `APP_ENV=production`, `JWT_COOKIE_SECURE=1`, uno storage Redis condiviso, chiavi segrete stabili e Gunicorn dietro un reverse proxy.

## Avvio con Docker Compose

Copia `.env.example` in `.env`, imposta anche `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD` e `MYSQL_ROOT_PASSWORD`, poi avvia. Per un deployment HTTPS imposta inoltre `APP_ENV=production`, `JWT_COOKIE_SECURE=1` e `RATELIMIT_STORAGE_URI` con l'URI di un Redis raggiungibile dal container web:

```bash
docker compose up --build -d
```

L’applicazione è disponibile su `http://localhost:8000` (o sulla porta definita da `APP_PORT`). Per creare il primo amministratore:

```bash
docker compose exec web flask --app run.py create-admin
```

I dati MySQL e gli upload sono conservati in volumi Docker. Per fermare i servizi senza cancellare i dati usa `docker compose down`; non usare `-v` se vuoi conservarli.

## Accesso Google e recupero password

Il login Google è facoltativo. Crea credenziali OAuth 2.0 di tipo applicazione web nella Google Cloud Console e registra come redirect URI autorizzato `https://DOMINIO/accesso/google/callback`. Imposta `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` e `PUBLIC_BASE_URL` nel `.env`; quest'ultimo deve essere l'origine pubblica esatta, senza slash finale. Per sviluppo locale usa `http://127.0.0.1:5000` e registra lo stesso callback URI in Google. L'accesso associa solo email verificate a un account già registrato: prima crea l'account con la stessa email.

Per il recupero password configura un server SMTP in `.env`: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_USE_TLS`, `SMTP_USE_SSL` e `MAIL_FROM`. Usa TLS sulla porta 587 (`SMTP_USE_TLS=1`, `SMTP_USE_SSL=0`) oppure SSL sulla porta 465 (`SMTP_USE_TLS=0`, `SMTP_USE_SSL=1`). Imposta `PUBLIC_BASE_URL` all'indirizzo pubblico dell'app affinché i link email puntino al dominio corretto. I link sono firmati, validi 30 minuti e vengono invalidati quando la password cambia. Senza SMTP configurato la richiesta mantiene una risposta generica ma non può spedire email.

L'app usa cookie tecnici necessari per sessione, CSRF e autenticazione; non include analytics o cookie pubblicitari. Il banner informa l'utente senza bloccare le funzioni essenziali.

## Mappa, ricerca e foto

Nel form la posizione si sceglie cliccando o spostando il marker, usando la geolocalizzazione oppure cercando l'indirizzo. La ricerca invia l'indirizzo digitato al servizio pubblico Nominatim di OpenStreetMap solo quando si preme il pulsante; le richieste sono distanziate per rispettarne i limiti d'uso. In elenco si può alternare mappa e risultati su mobile, centrare un marker dalla relativa riga e rimuovere singolarmente i filtri attivi. Le foto si aprono in una galleria interna a schermo ampio e non in una nuova scheda.

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
- Nuove segnalazioni con almeno una foto JPG, PNG o WebP verificata lato server; upload successivi con limite configurabile e controllo dei formati. Le segnalazioni già esistenti non vengono modificate.
- Sostegni univoci per utente/segnalazione; la chiave univoca nel database gestisce anche richieste concorrenti.
- Moderazione, collegamento dei duplicati con controllo dei cicli, gestione dei dossier e dei ruoli amministrativi.
- Endpoint `/health` per verificare la disponibilità del database.

I riferimenti a PostgreSQL/Node.js presenti in alcuni documenti descrivono lo stato precedente del progetto: il codice applicativo e questo README usano MySQL e Python come richiesto. Le transizioni di stato non definite nella documentazione sono attualmente affidate a membri del comitato e amministratori senza workflow più restrittivi.
