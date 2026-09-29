+---------------+   (1,1) [RISIEDE IN] (0,N)   +-------------------+   (0,N) [COMPILA] (1,1)   +-------------------+
|   QUARTIERE   |----------------------------->|      UTENTE       |---------------------------->|      DOSSIER      |
+---------------+                              +-------------------+                             +-------------------+
        |                                                |                                                 |
        | (1,1)                                          | (1,1)                                           | (1,1)
        | [LOCALIZZATA IN]                               | [CREA]                                          | [INCLUDE]
        v (0,N)                                          v (0,N)                                           v (1,N)
+---------------+   (1,1) [CLASSIFICA] (0,N)   +----------------------------------------+   (1,1) [RICEVE] (0,N)   +---------------+   (0,N) [COLLEGA] (1,1)   +-------------------+
|   CATEGORIA   |----------------------------->|              SEGNALAZIONE              |------------------------->|   SOSTEGNO    |-------------------------->|DOSSIER_SEGNALAZ.  |
+---------------+                              +----------------------------------------+                          +---------------+                           +-------------------+
                                                           |                        ^
                                                           | (1,1)                  | (0,1) [PADRE]
                                                           | [CONTIENE]             | (Relazione Ricorsiva
                                                           v (1,N) (Minimo 1)       |  [ACCORPA DUPLICATI])
                                               +------------------------+           | (0,N) [FIGLI]
                                               | ALLEGATO_MULTIMEDIALE  |-----------+
                                               +------------------------+





## Entità e attributi

### 1. QUARTIERE
Attributi:
- ID_Quartiere [PK] - identificativo univoco del quartiere
- NomeQuartiere - nome del quartiere (es. Centro Storico, Quartiere Nord)
- Cap_Zona - codice di riferimento della zona oppure CAP del territorio

### 2. UTENTE
Attributi:
- ID_Utente [PK] - identificativo univoco dell'utente
- Nome - nome dell'utente
- Cognome - cognome dell'utente
- Email [UNIQUE] - indirizzo email usato per il login
- PasswordHash - password cifrata per sicurezza
- TipoRuolo - ruolo dell'utente: Cittadino, MembroComitato, Admin
- DataRegistrazione - data di creazione dell'account
- FK_Quartiere [FK -> QUARTIERE] - quartiere di residenza dell'utente

### 3. CATEGORIA
Attributi:
- ID_Categoria [PK] - identificativo univoco della categoria
- NomeCategoria - nome della categoria (es. Buche Stradali, Illuminazione, Verde Pubblico, Movida)
- Descrizione - breve descrizione della categoria

### 4. SEGNALAZIONE
Attributi:
- ID_Segnalazione [PK] - identificativo univoco della segnalazione
- Titolo - titolo sintetico della segnalazione
- DescrizioneTestuale - testo descrittivo del problema
- Latitudine - coordinata geografica GPS
- Longitudine - coordinata geografica GPS
- Indirizzo - indirizzo o zona esatta dove si trova il problema
- DataCreazione - data di invio della segnalazione
- StatoAttuale - stato della segnalazione: Inviata, Approvata, Presa in Carico, Inclusa nel Dossier, Risolta
- FK_Utente_Autore [FK -> UTENTE] - utente che ha creato la segnalazione
- FK_Categoria [FK -> CATEGORIA] - categoria della segnalazione
- FK_Quartiere [FK -> QUARTIERE] - quartiere in cui si trova il problema
- FK_SegnalazionePadre [FK -> SEGNALAZIONE, opzionale] - riferimento alla segnalazione principale in caso di merge/duplicati

Nota:
- il campo FK_SegnalazionePadre serve a gestire i duplicati: se più segnalazioni riguardano lo stesso problema, possono essere collegate a una stessa segnalazione principale.

### 5. ALLEGATO_MULTIMEDIALE
Attributi:
- ID_Allegato [PK] - identificativo univoco dell'allegato
- UrlFile - percorso dove è salvata l'immagine o il video
- TipoFile - tipo di file: Foto o Video
- DataUpload - data dell'upload
- FK_Segnalazione [FK -> SEGNALAZIONE] - segnalazione a cui è collegato l'allegato

### 6. SOSTEGNO (VOTO)
Attributi:
- ID_Sostegno [PK] - identificativo univoco del sostegno
- DataVoto - data in cui è stato espresso il voto
- FK_Utente [FK -> UTENTE] - utente che ha espresso il sostegno
- FK_Segnalazione [FK -> SEGNALAZIONE] - segnalazione supportata

Vincolo:
- la coppia FK_Utente + FK_Segnalazione deve essere unica, così un utente non può sostenere più volte la stessa segnalazione.

### 7. DOSSIER
Attributi:
- ID_Dossier [PK] - identificativo univoco del dossier
- Titolo - titolo del dossier (es. Dossier Criticità Quartiere Sud - Elezioni 2026)
- DataCreazione - data di creazione del dossier
- NoteComitato - note aggiuntive o osservazioni del comitato
- FK_Utente_Creatore [FK -> UTENTE] - utente che ha creato il dossier

### 8. DOSSIER_SEGNALAZIONE (tabella di relazione N:M)
Attributi:
- FK_Dossier [PK, FK -> DOSSIER] - dossier a cui la segnalazione è collegata
- FK_Segnalazione [PK, FK -> SEGNALAZIONE] - segnalazione inclusa nel dossier
- DataInserimento - data in cui la segnalazione è stata aggiunta al dossier

Nota:
- questa tabella collega una segnalazione a uno o più dossier, permettendo di aggregare più segnalazioni in un unico documento finale.