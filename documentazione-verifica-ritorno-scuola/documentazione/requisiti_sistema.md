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
| RF-10 | Esporre controlli di salute del servizio e della connessione PostgreSQL | Gestione tecnica |

## Dati e vincoli

- Persistenza in PostgreSQL delle otto tabelle descritte nel modello logico.
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
| Sistema operativo di sviluppo | Windows, macOS o Linux compatibile con il runtime scelto |
| Runtime | Node.js >= 20, come indicato nel materiale del repository; compatibilità effettiva da verificare dopo il ripristino |
| Gestione pacchetti | npm con un package.json valido |
| Backend | Express 4; pg; dotenv; bcryptjs; jsonwebtoken; multer per upload |
| Database | PostgreSQL 16, scelta documentata nel progetto |
| Strumenti SQL | psql oppure un client PostgreSQL equivalente |
| Container | Docker e Compose opzionali; il file Compose attuale richiede correzione |
| Test | Node test runner e Supertest |
| Client attuale previsto | Client HTTP per le API; un'interfaccia web non è presente nell'albero esaminato |
| Porte previste | Applicazione 3000 e PostgreSQL 5432, configurabili |
| Archiviazione | Spazio scrivibile per allegati e spazio persistente per PostgreSQL |

Non sono disponibili misurazioni per stabilire minimi hardware attendibili di RAM, CPU e spazio disco.
