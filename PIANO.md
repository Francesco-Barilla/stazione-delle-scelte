# Stazione delle scelte — proposta e sviluppo

Applicazione separata per una prima superiore, offline e proiettabile in classe.
Continuità con i laboratori di ordinamenti e cicli: Impara, Gioca, quattro
linguaggi, tre difficoltà, spiegazioni scorrevoli, animazioni e salvataggi locali.
Ambientazione scelta: una stazione spaziale, con droni di bordo, portelli,
missioni di soccorso, gestione delle risorse e allarmi.

## Il punto didattico

Lo studente osserva i dati, prevede la decisione, segue il codice e costruisce
una regola valida per tutti i casi della missione. La traccia distingue
VERO, FALSO e NON VALUTATA: un ramo saltato non è una condizione falsa.

Percorsi:

- Impara facendo: tre previsioni con casi scelti per mettere in evidenza un
  contrasto. Prima una decisione, poi un cambio dei dati, infine una prova
  della regola. Il concetto emerge dalla conseguenza e dal perché del caso.
- Gioca: turni di cinque droni, portelli animati e dati a sorpresa nel quinto
  caso. Un errore ferma il drone e suggerisce cosa ricontrollare; si riprova
  senza perdere vite o correre contro il tempo. Dopo gli ordini manuali,
  lo studente costruisce la regola che automatizza la stazione.
- Laboratorio del codice: Facile a blocchi; Medio con completamento;
  Difficile con editor. Verifica di tutti i dati nel dominio dichiarato.
- Banco logico: commuta gli ingressi o compila i campi; osserva risultato,
  tabella di verità e preparazione dei dati nei quattro linguaggi.
- Scova l'equivoco: prevedi l'esito di un programma, controlla la traccia e
  leggi il controesempio. Le risposte scorrette non assegnano il completamento.

## Sfide

1. Ricarica se serve — if senza else, zero azioni può essere corretto.
2. Il cancello — if/else e alternative esclusive.
3. Pronti a partire — differenza tra > e >=.
4. Due controlli — if indipendenti e azioni cumulative.
5. Tre livelli di energia — if/elif/else e prima condizione vera.
6. Prima le urgenze — condizioni sovrapposte e priorità.
7. Doppio permesso — AND.
8. Basta un allarme — OR inclusivo.
9. Il carico giusto — intervallo chiuso e casi sui confini.
10. Dentro il cancello — if annidato, controllo esterno prima dell'interno.
11. Soccorso intelligente — decisioni annidate su dati diversi.
12. Il turno completo — annidamento, catena e istruzione dopo la selezione.
13. Il permesso capovolto — NOT su booleani.
14. Due motori pronti — AND su bit 0/1.
15. Un segnale basta — OR su bit 0/1, compreso 1/1.
16. Un solo pilota — XOR: esattamente un ingresso vero.
17. Inverti il segnale — NOT logico, conversione del bit in booleano.
18. Il messaggio mancante — campo vuoto o pieno.
19. La scheda di missione — AND di due sensori di presenza.
20. Una destinazione sola — XOR dei campi compilati.

## Una sequenza da provare in classe

1. Nel banco accendi A, lascia B spento, confronta OR e XOR. Poi accendi B:
   i risultati divergono. Chiedi di spiegare quale nuovo caso li distingue.
2. Passa a Campi, scrivi 0 e poi cancellalo. Conta i caratteri. Ripeti con
   uno spazio: la presenza non equivale alla validità del contenuto.
3. Apri Impara facendo / Dentro il modulo: senza badge il livello non è
   valutato; con badge diventa decisivo. Collega il percorso al codice.
4. Gioca un turno. Poi completa o scrivi il programma e chiedi alla verifica
   un caso che smentisca la regola. Il controesempio diventa un nuovo esperimento.

Il movimento del drone rappresenta l'esecuzione dell'ordine scelto. Attesa,
rifiuto e nessuna azione mantengono il drone fermo; il caso di zero azioni non
viene trasformato di nascosto in una chiamata ad attendi().

## Equivoci da rendere osservabili

If non ripete; if non richiede else; else non ha una propria condizione;
else non significa sempre errore; più if possono eseguire più azioni;
una catena sceglie al massimo un ramo; l'ordine delle condizioni conta;
non valutata è diverso da falsa; il controllo interno dipende dall'esterno;
else appartiene alla struttura determinata da indentazione o graffe;
uguaglianza e assegnazione sono operazioni diverse; OR include il caso in
cui entrambe le condizioni sono vere; la soglia va provata esattamente;
il codice dopo la selezione prosegue normalmente; AND/OR hanno cortocircuito.
XOR non coincide con OR quando entrambi sono veri; ^ valuta entrambi gli
ingressi; NOT non è il segno meno o ~; testo "0" e numero 0 sono diversi;
uno spazio è un carattere; due testi diversi possono essere entrambi presenti.

## Correttezza e verifica

Python usa elif e indentazione; JavaScript, C e Java usano else if e graffe.
L'editor interpreta un sottoinsieme dichiarato, con dati di sola lettura e
azioni della stazione. Non esegue codice dello studente tramite eval, exec o
runtime esterni. I messaggi distinguono un limite del laboratorio da un errore
del linguaggio. Le condizioni numeriche non sono valide in Java; gli operatori
logici e la precedenza devono mantenere il significato del linguaggio scelto.

Test delle soluzioni in tutti i linguaggi, dei programmi errati e dei confini;
verifica di feedback, progressi separati, modali, navigazione e rendering;
controllo del pacchetto Windows e degli archivi. L'eseguibile è nella radice.

Il laboratorio dei cicli verrà aggiornato in un'attività successiva.
