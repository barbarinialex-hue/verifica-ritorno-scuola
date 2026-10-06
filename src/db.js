# Verifica Ritorno Scuola

## Stato del progetto

Questa repository è stata avviata come foundation per la piattaforma di segnalazioni civiche `Verifica Ritorno Scuola`.

La prima fase implementata è la base tecnica del progetto: configurazione del runtime, scaffolding dell'applicazione web, endpoint di salute del servizio, gestione centralizzata degli errori e documentazione di setup.

La seconda fase implementata riguarda il modello dati reale e la base del database PostgreSQL: schema completo delle entità previste dal progetto, migrazione iniziale, inizializzazione automatica dello schema e verifica di salute del database.

La terza fase implementata aggiunge l'autenticazione reale degli utenti. È ora possibile registrare un account, effettuare il login, ricevere un token JWT, e recuperare il profilo autenticato tramite endpoint protetti.

La quarta fase implementata riguarda la gestione delle segnalazioni: creazione, lista, dettaglio, modifica e cancellazione di segnalazioni con autenticazione e validazione dei campi.

L'obiettivo di questa base è rendere il repository pronto per lo sviluppo delle funzionalità reali: autenticazione, gestione delle segnalazioni, upload multimediale, moderazione, dossier e dashboard amministrativa.

## Stack scelto

- Node.js 20+
- Express 4
- PostgreSQL 16 (via Docker Compose per il setup locale)
- JWT + bcrypt per autenticazione e password hashing
- Supertest + Node test runner per la verifica automatica

## Struttura del repository

```text
.
├── src/
│   ├── app.js                # applicazione Express + route principali
│   ├── auth.js               # register/login/JWT + validazione utenti
│   ├── config.js             # configurazione e validazione env
│   ├── db/
│   │   ├── init.js           # utility CLI per inizializzare il database
│   │   └── schema.sql        # schema PostgreSQL con entità e vincoli
│   ├── db.js                 # connessione e health check del database
│   ├── errors.js             # gestione centralizzata degli errori
│   ├── segnalazioni.js       # CRUD delle segnalazioni e validazione
│   └── server.js             # bootstrap del server
├── test/
│   ├── auth.test.js          # test di registrazione, login e autenticazione
│   ├── db.test.js            # test di inizializzazione e schema del database
│   ├── health.test.js        # test del servizio e gestione errori
│   └── segnalazioni.test.js  # test di CRUD segnalazioni
├── .env.example              # variabili d'ambiente di esempio
├── .gitignore
├── docker-compose.yml        # database PostgreSQL locale
├── package.json
├── README.md
└── LICENSE (se aggiunto in futuro)
```

## Requisiti

- Node.js >= 20
- Docker Desktop (opzionale ma consigliato per il database PostgreSQL locale)

## Setup locale

1. Installa le dipendenze:

```bash
npm install
```

2. Copia il file delle variabili d'ambiente:

```bash
cp .env.example .env
```

3. Avvia il database PostgreSQL locale:

```bash
docker compose up -d postgres
```

4. Inizializza lo schema del database:

```bash
npm run db:init
```

5. Avvia il servizio:

```bash
npm run dev
```

Oppure in modalità production:

```bash
npm start
```

## Autenticazione

Elenco delle API introdotte per la fase di auth:

### Registrazione

```bash
curl -X POST http://localhost:3000/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{
    "nome": "Mario",
    "cognome": "Rossi",
    "email": "mario.rossi@example.com",
    "password": "Password123!",
    "tipoRuolo": "Cittadino",
    "quartiereId": 1
  }'
```

### Login

```bash
curl -X POST http://localhost:3000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "mario.rossi@example.com",
    "password": "Password123!"
  }'
```

### Profilo autenticato

```bash
curl http://localhost:3000/api/auth/me \
  -H 'Authorization: Bearer <token>'
```

## Gestione segnalazioni

Le segnalazioni supportano il ciclo completo CRUD:

### Creazione di una segnalazione

```bash
curl -X POST http://localhost:3000/api/segnalazioni \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <token>' \
  -d '{
    "titolo": "Lampione guasto",
    "descrizioneTestuale": "Il lampione del viale principale non funziona da diversi giorni.",
    "latitudine": 45.123456,
    "longitudine": 9.123456,
    "indirizzo": "Via Roma 12",
    "categoriaId": 1,
    "quartiereId": 1
  }'
```

### Lista delle segnalazioni

```bash
curl http://localhost:3000/api/segnalazioni
```

### Dettaglio di una segnalazione

```bash
curl http://localhost:3000/api/segnalazioni/1
```

### Aggiornamento

```bash
curl -X PATCH http://localhost:3000/api/segnalazioni/1 \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <token>' \
  -d '{
    "titolo": "Lampione guasto - urgente",
    "statoAttuale": "Approvata"
  }'
```

### Cancellazione

```bash
curl -X DELETE http://localhost:3000/api/segnalazioni/1 \
  -H 'Authorization: Bearer <token>'
```

Le segnalazioni richiedono autenticazione per creare, aggiornare e cancellare; la lettura della lista e del dettaglio è accessibile in lettura pubblica.

La password viene salvata in formato hash con bcrypt; i token JWT sono firmati con `JWT_SECRET` e hanno scadenza configurabile con `JWT_EXPIRES_IN`.

## Database e modello dati

Questo progetto implementa la struttura logica prevista dal modello di dominio del sistema:

- `quartiere`: aree geografiche di riferimento
- `utente`: profili cittadini, comitato e amministratori
- `categoria`: classificazione delle criticità urbane
- `segnalazione`: richiesta di segnalazione con coordinate geografiche
- `allegato_multimediale`: foto e video associati a una segnalazione
- `sostegno`: appoggio di un utente a una segnalazione
- `dossier`: aggregazione di segnalazioni rilevanti
- `dossier_segnalazione`: relazione molti-a-molti tra dossier e segnalazioni

Le relazioni e i vincoli sono definiti in `src/db/schema.sql` e includono:

- unicità email per utente;
- unicità della coppia utente + segnalazione per il sostegno;
- vincoli di integrità referenziale tra le entità;
- enumerazioni per ruoli, stati e tipi file;
- indici sulle chiavi di accesso più frequenti.

## Verifica del servizio

Il backend offre un endpoint di health check e una root endpoint informativa:

```bash
curl http://localhost:3000/api/health
curl http://localhost:3000/
```

Per inizializzare lo schema del database in una configurazione locale:

```bash
curl -X POST http://localhost:3000/api/database/init
```

## Test

```bash
npm test
```

## State of the project

Questo commit implementa la quarta fase della roadmap: il lifecycle completo delle segnalazioni.

In particolare:

- creazione di una segnalazione con validazione dei campi;
- lettura pubblica di lista e dettaglio;
- aggiornamento delle informazioni e degli stati;
- cancellazione con autorizzazione per autore o ruoli amministrativi;
- gestione degli errori per dati non validi, route mancanti e interferenze di permessi;
- test automatici per CRUD segnalazioni;
- documentazione aggiornata con esempi diretti dell'API.

## Prossimi passi previsti

1. aggiungere upload foto/video e validazione dei file;
2. introdurre moderazione, sostegni e dossier;
3. completare dashboard cittadino, comitato e admin.

## Nota metodologica

Il progetto è stato analizzato in profondità e la quarta attività fondamentale da implementare è il ciclo di vita delle segnalazioni. Senza la capacità di creare, controllare e aggiornare segnalazioni in modo sicuro, la piattaforma non può far davvero emergere il valore del servizio. L'implementazione attuale fornisce la base funzionale per il resto del prodotto.
