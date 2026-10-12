# Requisiti utente

Questi requisiti descrivono cosa deve poter fare chi usa la piattaforma. Sono una specifica del comportamento atteso: lo stato del repository non permette di considerarli tutti implementati.

## Attori

| Attore | Obiettivo |
| --- | --- |
| Visitatore | Consultare le segnalazioni pubbliche |
| Cittadino registrato | Segnalare un problema e sostenerne altri |
| Membro del comitato | Moderare le segnalazioni e preparare dossier |
| Amministratore | Gestire privilegi e supervisione del sistema |

## Funzioni richieste

| ID | Attore | Requisito | Criterio di accettazione |
| --- | --- | --- | --- |
| RU-01 | Visitatore | Consultare elenco e dettaglio delle segnalazioni | La consultazione pubblica non richiede login |
| RU-02 | Visitatore | Registrarsi indicando nome, cognome, email, password e quartiere | Un'email già presente viene rifiutata; il nuovo account è Cittadino |
| RU-03 | Utente registrato | Accedere e consultare il proprio profilo | Credenziali corrette consentono accesso; credenziali errate vengono rifiutate |
| RU-04 | Cittadino | Inviare una segnalazione con titolo, descrizione, coordinate, indirizzo, categoria e quartiere | La segnalazione viene associata all'autore con stato iniziale Inviata |
| RU-05 | Cittadino | Consultare e gestire le proprie segnalazioni | Un utente non può modificare o eliminare quelle di altri senza autorizzazione |
| RU-06 | Autore, comitato, admin | Allegare fotografie o video alle segnalazioni autorizzate | File supportati entro il limite vengono associati alla segnalazione |
| RU-07 | Cittadino | Esprimere e rimuovere un sostegno | Una seconda richiesta non produce un secondo voto; la rimozione aggiorna il conteggio |
| RU-08 | Visitatore | Cercare per categoria, quartiere e stato | I risultati rispettano i filtri selezionati |
| RU-09 | Comitato, admin | Moderare le segnalazioni e aggiornarne lo stato | Un cittadino non può attribuirsi privilegi di moderazione |
| RU-10 | Comitato, admin | Collegare segnalazioni duplicate a una principale | Il collegamento non può essere verso sé stessa né formare cicli |
| RU-11 | Comitato, admin | Creare dossier e inserirvi segnalazioni | La stessa segnalazione compare una sola volta nello stesso dossier |
| RU-12 | Admin | Gestire l'attribuzione dei ruoli | Solo un'operazione amministrativa autorizzata modifica i privilegi |

## Flusso di utilizzo

1. Il cittadino consulta le segnalazioni già presenti per evitare duplicati.
2. Si registra o effettua il login.
3. Descrive il problema e indica posizione, categoria e quartiere.
4. Aggiunge eventuali prove fotografiche o video.
5. Altri cittadini possono sostenere la segnalazione.
6. Il comitato verifica, prende in carico e può includere la segnalazione in un dossier.
7. Lo stato viene aggiornato fino alla risoluzione.

## Regole da confermare con il committente

Gli allegati sono facoltativi al momento dell'inserimento: il precedente diagramma indicava almeno un allegato, ma le API previste separano creazione e upload. Un dossier può essere vuoto mentre è in preparazione; prima della sua finalizzazione dovrà contenere almeno una segnalazione. Non è ancora definito un processo di pubblicazione/finalizzazione dei dossier.
Le transizioni ammesse tra stati e l'eventuale limitazione delle modifiche dell'autore dopo la presa in carico richiedono una decisione di prodotto.
