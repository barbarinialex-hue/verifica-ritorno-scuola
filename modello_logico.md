# Modello logico

## Introduzione
Il modello logico descrive come i dati del sistema sono organizzati in modo strutturato, definendo le entità, gli attributi e le relazioni tra di loro. In questo modello non si parla più del comportamento dell'applicazione, ma della struttura dei dati che la sostengono.

---

## 1. Entità principali

### 1.1 QUARTIERE
- ID_Quartiere (PK)
- NomeQuartiere
- Cap_Zona

Descrizione:
Rappresenta il quartiere di residenza dell'utente e la zona geografica in cui si trovano le segnalazioni.

### 1.2 UTENTE
- ID_Utente (PK)
- Nome
- Cognome
- Email
- PasswordHash
- TipoRuolo
- DataRegistrazione
- FK_Quartiere (FK -> QUARTIERE)

Descrizione:
Rappresenta il cittadino, il membro del comitato o l'amministratore che usa la piattaforma.

### 1.3 CATEGORIA
- ID_Categoria (PK)
- NomeCategoria
- Descrizione

Descrizione:
Classifica il tipo di problema segnalato, ad esempio buche, illuminazione, verde pubblico o movida.

### 1.4 SEGNALAZIONE
- ID_Segnalazione (PK)
- Titolo
- DescrizioneTestuale
- Latitudine
- Longitudine
- Indirizzo
- DataCreazione
- StatoAttuale
- FK_Utente_Autore (FK -> UTENTE)
- FK_Categoria (FK -> CATEGORIA)
- FK_Quartiere (FK -> QUARTIERE)
- FK_SegnalazionePadre (FK -> SEGNALAZIONE, opzionale)

Descrizione:
Rappresenta una segnalazione inviata da un utente relativa a un problema della città.

### 1.5 ALLEGATO_MULTIMEDIALE
- ID_Allegato (PK)
- UrlFile
- TipoFile
- DataUpload
- FK_Segnalazione (FK -> SEGNALAZIONE)

Descrizione:
Contiene foto o video allegati a una segnalazione per confermare la criticità riportata.

### 1.6 SOSTEGNO
- ID_Sostegno (PK)
- DataVoto
- FK_Utente (FK -> UTENTE)
- FK_Segnalazione (FK -> SEGNALAZIONE)

Descrizione:
Rappresenta il supporto dato da un utente a una segnalazione. Un utente non può sostenere due volte la stessa segnalazione.

### 1.7 DOSSIER
- ID_Dossier (PK)
- Titolo
- DataCreazione
- NoteComitato
- FK_Utente_Creatore (FK -> UTENTE)

Descrizione:
Raccoglie le segnalazioni che sono state giudicate rilevanti e organizzate in un documento finale.

### 1.8 DOSSIER_SEGNALAZIONE
- FK_Dossier (PK, FK -> DOSSIER)
- FK_Segnalazione (PK, FK -> SEGNALAZIONE)
- DataInserimento

Descrizione:
Tabella di relazione che collega una segnalazione a uno o più dossier.

---

## 2. Relazioni principali

### 2.1 QUARTIERE - UTENTE
- Un quartiere può avere molti utenti.
- Un utente appartiene a un solo quartiere.

Cardinalità:
- QUARTIERE: 1 -> N
- UTENTE: N -> 1

### 2.2 QUARTIERE - SEGNALAZIONE
- Un quartiere può contenere molte segnalazioni.
- Una segnalazione appartiene a un solo quartiere.

Cardinalità:
- QUARTIERE: 1 -> N
- SEGNALAZIONE: N -> 1

### 2.3 CATEGORIA - SEGNALAZIONE
- Una categoria può essere associata a molte segnalazioni.
- Una segnalazione appartiene a una sola categoria.

Cardinalità:
- CATEGORIA: 1 -> N
- SEGNALAZIONE: N -> 1

### 2.4 UTENTE - SEGNALAZIONE
- Un utente può creare molte segnalazioni.
- Una segnalazione è creata da un solo utente.

Cardinalità:
- UTENTE: 1 -> N
- SEGNALAZIONE: N -> 1

### 2.5 SEGNALAZIONE - ALLEGATO_MULTIMEDIALE
- Una segnalazione può avere molti allegati.
- Un allegato appartiene a una sola segnalazione.

Cardinalità:
- SEGNALAZIONE: 1 -> N
- ALLEGATO_MULTIMEDIALE: N -> 1

### 2.6 UTENTE - SOSTEGNO
- Un utente può esprimere molti sostegni.
- Un sostegno è espresso da un solo utente.

Cardinalità:
- UTENTE: 1 -> N
- SOSTEGNO: N -> 1

### 2.7 SEGNALAZIONE - SOSTEGNO
- Una segnalazione può avere molti sostegni.
- Un sostegno riguarda una sola segnalazione.

Cardinalità:
- SEGNALAZIONE: 1 -> N
- SOSTEGNO: N -> 1

### 2.8 SEGNALAZIONE - SEGNALAZIONE (ricorsiva)
- Una segnalazione può essere collegata a un'altra segnalazione principale.
- Questo permette di unire segnalazioni duplicate o simili.

Cardinalità:
- SEGNALAZIONE: 1 -> N (rispetto alla relazione padre/figlio)

### 2.9 UTENTE - DOSSIER
- Un utente può creare molti dossier.
- Un dossier viene creato da un solo utente.

Cardinalità:
- UTENTE: 1 -> N
- DOSSIER: N -> 1

### 2.10 DOSSIER - SEGNALAZIONE
- Un dossier può contenere molte segnalazioni.
- Una segnalazione può essere inserita in molti dossier.

Cardinalità:
- DOSSIER: N -> N
- relazione mediata da DOSSIER_SEGNALAZIONE

---

## 3. Vincoli principali
- Email dell'utente deve essere unica.
- La coppia Utente + Segnalazione in SOSTEGNO deve essere unica.
- Una segnalazione può avere più allegati, ma ogni allegato è collegato a una sola segnalazione.
- La segnalazione padre è opzionale e serve a gestire eventuali duplicati.
- Un dossier può includere più segnalazioni, e una segnalazione può comparire in più dossier.

---

## 4. Schema concettuale in forma sintetica

UTENTE \n       |
       | 1:N
       v
QUARTIERE

UTENTE 1:N SEGNALAZIONE
CATEGORIA 1:N SEGNALAZIONE
SEGNALAZIONE 1:N ALLEGATO_MULTIMEDIALE
SEGNALAZIONE 1:N SOSTEGNO
UTENTE 1:N SOSTEGNO
UTENTE 1:N DOSSIER
DOSSIER N:N SEGNALAZIONE

---

## 5. Obiettivo del modello logico
Il modello logico serve a definire in modo preciso come i dati sono organizzati, senza entrare nel dettaglio tecnico della programmazione. L'obiettivo è rendere chiaro:
- quali informazioni vengono memorizzate;
- quali entità esistono;
- come si collegano tra loro;
- quali regole devono essere rispettate per mantenere il sistema coerente.

Questo modello è la base utile per poi passare alla progettazione del database fisico e allo sviluppo dell'applicazione.
