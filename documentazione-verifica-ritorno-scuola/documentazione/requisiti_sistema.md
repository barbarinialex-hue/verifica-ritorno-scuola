# Requisiti di sistema

Specifiche da soddisfare e verificare durante il ripristino e lo sviluppo. La presenza di codice o di un modello non equivale a una verifica positiva.

## Requisiti funzionali

| ID | Requisito del sistema | Requisiti utente |
| --- | --- | --- |
| RF-01 | Gestire registrazione, login e profilo autenticato con token JWT a scadenza | RU-02, RU-03 |
| RF-02 | Salvare un hash della password; non restituire password o hash nelle risposte | RU-02, RU-03 |
| RF-03 | Autorizzare ogni operazione in base a utente, proprietà e ruolo; impedire l'autoassegnazione di ruoli privilegiati | RU-05, RU-09, RU-12 |
| RF-04 | Creare, leggere, aggiornare ed eliminare segnalazioni, validando campi e riferimenti | RU-01, RU-04, RU-05 |
| RF-05 | Filtrare segnalazioni per quartiere, categoria e stato e limitare il numero dei risultati | RU-08 |
| RF-06 | Gestire file JPEG, PNG, WebP, MP4, QuickTime e WebM con limite configurabile | RU-06 |
| RF-07 | Garantire un solo sostegno per coppia utente-segnalazione anche con richieste simultanee | RU-07 |
| RF-08 | Gestire stati, duplicati e dossier con autorizzazione del comitato o amministratore | RU-09, RU-10, RU-11 |
| RF-09 | Consentire l'aggiornamento dei ruoli solo agli amministratori | RU-12 |
| RF-10 | Esporre controlli di salute del servizio e della connessione MySQL | Gestione tecnica |

## Dati e vincoli

- Persistenza in MySQL delle otto tabelle descritte nel modello logico e gestite tramite Alembic/Flask-Migrate.
- Email univoca; normalizzazione in minuscolo prima della memorizzazione.
- Chiavi esterne valide e campi obbligatori non nulli.
- Coordinate comprese negli intervalli [-90, 90] e [-180, 180].
- Ruoli ammessi: Cittadino, MembroComitato, Admin.
- Stati ammessi: Inviata, Approvata, Presa in Carico, Inclusa nel Dossier, Risolta.
- Tipi di allegato: Foto e Video.
- Duplicati senza autoriferimenti o cicli: il CREATE blocca l'autoriferimento diretto; i cicli richiedono validazione applicativa o un trigger futuro.
- Le regole sui ruoli, sul contenuto dei file e sulle transizioni di stato non sono garantite dai soli CREATE TABLE.

## Requisiti non funzionali

| ID | Requisito | Verifica prevista |
| --- | --- | --- |
| RNF-01 | Messaggi di errore strutturati e comprensibili | Richieste non valide restituiscono un codice HTTP e un errore senza segreti |
| RNF-02 | Credenziali e segreti fuori dal codice versionato | Controllo delle variabili d'ambiente e dei file esclusi da Git |
| RNF-03 | Query parametrizzate e accessi autorizzati | Revisione delle query e test di accesso negato |
| RNF-04 | Integrità dei dati in caso di errori | Operazioni collegate in transazione; rollback verificato |
| RNF-05 | Upload controllati e consistenti con i metadati | Verifica di dimensione e contenuto; pulizia dei file se il salvataggio fallisce |
| RNF-06 | Documentazione facilmente consultabile | Indice unico e collegamenti relativi validi |
| RNF-07 | Recuperabilità di database e allegati | Procedura di backup e prova di ripristino da definire prima dell'esercizio |

Non sono definiti obiettivi numerici di utenti simultanei, latenza o disponibilità: occorre misurarli e concordarli, senza presentarli come prestazioni già garantite.

## Ambiente tecnico previsto

| Componente | Requisito |
| --- | --- |
| Sistema operativo di sviluppo | Linux, macOS o Windows con ambiente Python compatibile |
| Runtime | Python >= 3.11 |
| Gestione dipendenze | pip e `requirements.txt` |
| Backend | Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-JWT-Extended e Flask-WTF |
| Database | MySQL 8.0/8.4 in sviluppo e produzione; SQLite isolato nei test |
| Interfaccia | HTML/Jinja, CSS, JavaScript e Bootstrap 5, renderizzati dal server |
| Container | Docker e Docker Compose; MySQL e upload usano volumi persistenti |
| Test | pytest; la suite corrente usa SQLite e non sostituisce i test d'integrazione MySQL |
| Server | Flask per sviluppo; Gunicorn dietro HTTPS/reverse proxy in produzione |
| Porte predefinite | Flask 5000 in locale; Docker 8000 per l'app e 3306 per MySQL |
| Archiviazione | Directory configurabile per gli upload; volume persistente in Compose |

Le variabili d'ambiente, l'avvio locale, Docker, migrazioni e test sono descritti nel [README](../../README.md). Non sono disponibili misurazioni per stabilire minimi hardware attendibili di RAM, CPU e spazio disco.
