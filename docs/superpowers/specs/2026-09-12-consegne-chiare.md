# Consegne chiare nella Stazione delle scelte

## Obiettivo e analisi
Applicare il percorso già approvato nell'Officina dei dati. L'utente chiede lo stesso intervento su if/else: indicare cosa fare, dove agire e perché una risposta è corretta o errata. Conservare stazione, droni, venti missioni, tre difficoltà, quattro linguaggi e operatori AND/OR/NOT/XOR.

Problemi osservati: due lacune di natura diversa senza istruzioni vicine; commento iniziale che può assorbire la digitazione; Esegui e Verifica entrambi prominenti; risultato della verifica in un riquadro piccolo; risposta errata dei droni senza selezione persistente; dati dei sensori lontani dalla richiesta; guida ai comandi troppo generale.

## Disegno scelto
La schermata di programmazione segue due pannelli numerati: a sinistra costruisci/completa/scrivi, a destra controlla. La verifica è il comando principale. L'esecuzione passo per passo si apre in una vista dedicata e conserva la bozza.

Medio seleziona il prossimo `???` e distingue condizione senza if, azione con parentesi, punto e virgola già presente. Difficile parte vuoto e offre esempi della struttura richiesta. I sensori sono forniti dal gioco: non si digitano valori, letture o assegnazioni. I campi di testo diventano `campo_a`/`campo_b` prima dell'esecuzione.

Impara e turni dei droni mostrano prima i dati e una richiesta di scelta esplicita. La risposta sbagliata resta evidenziata, quella corretta resta dichiarata anche durante l'animazione. La traccia distingue VERO, FALSO e NON VALUTATA.

## Vincoli
- Python/Pygame e distribuzione Windows offline esistenti; nessuna dipendenza nuova.
- Bozze, progressi, domini esaustivi e criteri di completamento conservati.
- Esempi e aiuti nel linguaggio selezionato; stringhe presenti, bit e booleani distinti.
- Verifiche con click/digitazione reali, errori/riprova, ridimensionamento e controllo visivo.
- Ricostruire EXE e ZIP, aggiornare la cartella sorella e GitHub come già autorizzato.
