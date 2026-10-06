# Verifica Ritorno Scuola

## Stato del progetto

Questa repository è stata avviata come foundation per la piattaforma di segnalazioni civiche `Verifica Ritorno Scuola`.

La prima fase implementata è la base tecnica del progetto: configurazione del runtime, scaffolding dell'applicazione web, endpoint di salute del servizio, gestione centralizzata degli errori e documentazione di setup.

L'obiettivo di questa base è rendere il repository pronto per lo sviluppo delle funzionalità reali: autenticazione, gestione delle segnalazioni, upload multimediale, moderazione, dossier e dashboard amministrativa.

## Stack scelto

- Node.js 20+
- Express 4
- PostgreSQL 16 (via Docker Compose per il setup locale)
- Supertest + Node test runner per la verifica automatica

## Struttura del repository

```text
.
├── src/
│   ├── app.js                # applicazione Express + route principali
│   ├── config.js             # configurazione e validazione env
│   ├── errors.js             # gestione centralizzata degli errori
│   └── server.js             # bootstrap del server
├── test/
│   └── health.test.js        # test del servizio e gestione errori
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

4. Avvia il servizio:

```bash
npm run dev
```

Oppure in modalità production:

```bash
npm start
```

## Verifica del servizio

Il backend offre un endpoint di health check e una root endpoint informativa:

```bash
curl http://localhost:3000/api/health
curl http://localhost:3000/
```

## Test

```bash
npm test
```

## State of the project

Questo commit implementa la base tecnica necessaria per la v1.0. In particolare:

- setup del progetto Node.js/Express;
- validazione della configurazione;
- endpoint `/api/health` per il monitoraggio;
- middleware di gestione errori e route 404;
- documentazione e configurazione del database locale;
- test di regressione per il comportamento base del servizio.

## Prossimi passi previsti

1. definire lo schema del database PostgreSQL;
2. implementare autenticazione e registrazione utenti;
3. sviluppare il CRUD delle segnalazioni;
4. aggiungere upload foto/video e validazione dei file;
5. introdurre moderazione, sostegni e dossier;
6. completare dashboard cittadino, comitato e admin.

## Nota metodologica

Il progetto è stato analizzato in profondità e la prima fase da implementare è stata identificata come la base tecnica indispensabile per poter proseguire con il resto del sistema. Non è ancora una piattaforma completa: è la fondazione che rende il resto sviluppabile in modo controllato e testabile.
