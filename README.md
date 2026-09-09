# Stazione delle scelte

Laboratorio offline sulla struttura selettiva, per una prima superiore.
Realizzato dal **Prof. Barillà Francesco**.

Guida cinque droni per turno e poi programma la stazione: accessi ai moduli,
energia, carichi e soccorsi rendono visibili le conseguenze delle condizioni.
Il progetto è separato dai laboratori di ordinamento e dei cicli.

## Avvio Windows

Apri **StazioneScelte.exe** nella cartella principale, oppure **Avvia_Stazione.cmd**.
Per gli alunni distribuisci **dist/StazioneScelte-Windows.zip**: estrarre tutto
in una cartella scrivibile prima dell'avvio. Non servono Python, compilatori,
account o connessione. Eseguibile Windows x64.

Preferenze, progressi e bozze vengono creati localmente in
`progressi_selezione.json`, accanto all'eseguibile. Il file non è incluso negli
archivi. Se il salvataggio non è possibile, l'app mostra un avviso.

## Tre percorsi

- **Impara facendo**: 20 missioni introdotte da tre piccoli esperimenti.
  Prevedi un ordine, osserva la decisione, riprova quando cambiano i dati.
  La sequenza include contrasti e casi al limite scelti per il concetto.
  **Perché?** collega il risultato alla regola e all'equivoco da evitare.
- **Gioca**: nel livello Facile dai ordini a cinque droni. I portelli reagiscono
  alla scelta; con attesa, rifiuto o nessuna azione il drone resta fermo.
  Gli errori forniscono indizi e permettono di riprovare. Il quinto drone ha
  dati a sorpresa. Non c'è un limite di tempo. Il **Laboratorio del codice**
  aggiunge blocchi guidati; Medio propone completamenti dei `???`, Difficile
  un editor libero. La verifica del codice confronta tutte le combinazioni
  del dominio, inclusi i confini, e mostra un controesempio se trova un errore.
  Dopo una verifica riuscita puoi collaudare il tuo programma con cinque droni.
- **Scova l'equivoco**: 20 previsioni su programmi concreti. Prima rispondi,
  poi osserva la traccia e leggi il perché. Non tutte le domande mostrano un
  programma corretto rispetto a una consegna: devi prevedere il codice effettivo.

Il **Banco logico** è accessibile dalla Home e durante le attività. Cambia AND,
OR, NOT e XOR; usa booleani, bit 0/1 oppure due campi di testo. Il risultato e
la riga della tabella di verità cambiano subito. Il codice mostra la preparazione
degli ingressi in Python, JavaScript, C e Java. La lingua scelta nel banco
non modifica la bozza della missione. Prova `"0"`, `"false"`, uno spazio e un
campo davvero vuoto: la differenza si può osservare, non solo leggere.

Nella traccia **VERO**, **FALSO** e **NON VALUTATA** sono stati distinti.
Le etichette riportano il numero di riga. Clicca la striscia degli stati o
**Dettagli** per leggere tutto il passo, le sostituzioni numeriche e le azioni
eseguite. I tempi dell'animazione sono didattici, non misure di prestazioni.

Le missioni sono tutte accessibili. Completamenti e bozze sono separati per
missione, difficoltà e linguaggio; le scelte a blocchi sono condivise tra i
linguaggi. Il cambio di lingua recupera la relativa bozza o il suo esercizio
iniziale: non traduce automaticamente programmi arbitrari. Impara e la
consultazione delle soluzioni non sovrascrivono il tentativo e non assegnano
completamenti. Una struttura richiesta ma mai raggiunta non basta a vincere.

## Missioni

| Missione | Concetto | Dominio verificato |
|---|---|---|
| Una ricarica se serve | if senza else, nessuna azione | batteria 0–100 |
| Il portello di bordo | if/else | badge falso/vero |
| Pronti al decollo | >= e confine esatto | batteria 0–100 |
| Due controlli distinti | if indipendenti | batteria 0–100 × fragile |
| Tre fasce di energia | if/elif/else, prima vera | batteria 0–100 |
| Prima il soccorso | priorità delle condizioni | urgente × badge |
| Due permessi necessari | AND e cortocircuito | badge × autorizzato |
| Basta un allarme | OR inclusivo e cortocircuito | temperatura 0–100 × fumo |
| Il carico giusto | intervallo inclusivo | peso 0–40 |
| Dentro il modulo | if annidato e appartenenza else | badge × livello 0–3 |
| Soccorso tra le stelle | contesti annidati | urgente × batteria 0–100 |
| Il turno completo | annidamento, catena e seguito | badge × batteria 0–100 × fragile |
| Il permesso capovolto | NOT su booleani | autorizzato falso/vero |
| Due motori pronti | AND su ingressi binari | segnale A 0/1 × segnale B 0/1 |
| Un segnale basta | OR con 0/1, incluso 1/1 | segnale A 0/1 × segnale B 0/1 |
| Un solo pilota | XOR su booleani | badge × autorizzato |
| Inverti il segnale | NOT, conversione esplicita del bit | segnale A 0/1 |
| Il messaggio mancante | presenza del testo | vuoto, testo, `"0"`, `"false"`, spazio |
| La scheda di missione | AND di due sensori di presenza | cinque testi A × cinque testi B |
| Una destinazione sola | XOR di due sensori di presenza | cinque testi A × cinque testi B |

Ogni campo booleano comprende falso e vero. La verifica è esaustiva **nel
dominio dichiarato**, non una dimostrazione per dati o tipi esterni ad esso.

## Gli equivoci sono parte del gioco

If non ripete; else è facoltativo e non ha una condizione propria; più if
indipendenti possono eseguire più azioni; una catena sceglie al massimo un ramo;
le condizioni saltate non sono false; l'annidamento dipende dal ramo esterno;
l'ordine stabilisce le priorità; OR comprende anche vero/vero; i confini vanno
provati esattamente; il codice dopo la selezione prosegue normalmente.
XOR richiede esattamente un vero; NOT non cambia il segno di un numero;
il testo `"0"` è presente mentre il numero `0` rappresenta falso; uno spazio
è un carattere; confrontare la presenza di due testi non confronta le parole.

Le schede Linguaggi trattano anche `=` rispetto a `==`, condizioni numeriche,
graffe e indentazione, associazione dell'else, istruzione vuota `if (...);`,
confronti concatenati e precedenza della negazione. Distinguono un errore del
linguaggio da un costrutto consentito dal linguaggio ma escluso dal laboratorio.

## Quattro linguaggi, un sottoinsieme esplicito

| Aspetto | Python | JavaScript | C | Java |
|---|---|---|---|---|
| Catena | `elif` | `else if` | `else if` | `else if` |
| Blocchi | rientri e `:` | graffe | graffe | graffe |
| Logica | `and`, `or`, `not` | `&&`, `||`, `!` | `&&`, `||`, `!` | `&&`, `||`, `!` |
| XOR con ingressi booleani | `a ^ b` | `a ^ b` (risultato 0/1) | `a ^ b` (risultato 0/1) | `a ^ b` |
| Booleani | `True`, `False` | `true`, `false` | dati bool predisposti | `true`, `false` |
| Intero usato come condizione | 0 falso | 0 falso | 0 falso | richiede booleano |

Si interpretano selezioni, alternative, annidamenti, azioni senza argomenti,
interi, booleani, confronti e operatori logici. `pass` in Python e l'istruzione
vuota `;` negli altri linguaggi sono gestiti. Non ci sono assegnazioni, cicli,
funzioni, stringhe, classi, import o accesso al sistema. In C, per i frammenti
didattici si considerano già disponibili i dati booleani che un programma C11
completo può dichiarare con `stdbool.h`.

I **testi** vengono predisposti fuori dall'editor: `campo_a` e `campo_b`
sono i booleani di presenza. La regola è esplicita: zero caratteri = falso,
almeno un carattere = vero, spazi compresi. Non verifica la validità del testo.
Il banco mostra `bool(testo)` in Python, `testo.length > 0` in JavaScript,
`!testo.isEmpty()` in Java e `testo[0] != '\0'` in C (stringa valida).
Non si simulano testi nulli o puntatori nulli.

XOR logico opera sui booleani normalizzati. `^` sugli interi è un operatore
bit per bit: con i soli 0 e 1 i risultati coincidono, con altri interi no.
`^` valuta entrambi gli ingressi. `~` non è NOT logico. Java richiede un
booleano in `if`: per i bit si usa un confronto come `segnale_a == 1`.

Il motore non passa codice dello studente a `eval`, `exec`, shell o runtime
esterni. Il parser Python legge l'AST; il parser degli altri linguaggi applica
la precedenza dei loro operatori. I controlli Java richiedono tipi compatibili
anche nei rami non eseguiti. In JavaScript sono supportati anche `===` e `!==`
per i soli interi e booleani del laboratorio. Non si riproducono tutti i tipi
e le conversioni dei linguaggi completi.

Limiti: 12000 caratteri, 180 righe, 1000 caratteri per condizione, 10 livelli,
300 istruzioni. L'editor rimane un ambiente didattico, non un IDE generale.

## Interazione

Tre temi: Notte, Giorno, Contrasto. Testo del codice e delle spiegazioni
regolabile. Velocità 0,5×, 1×, 2× e 3×. F11 alterna finestra/schermo intero.
Esc chiude una scheda o torna alla Home. Le finestre di spiegazione si leggono
con rotella, frecce, PagSu/PagGiù e Home/End. Aprire schede o impostazioni
mette in pausa; riprendere con Esegui.
Nei turni dei droni riprendi con **Riprendi il volo**. Puoi scegliere un ordine
anche con i tasti **A–D**. I campi del banco accettano fino a 40 caratteri.

I controlli cliccabili mostrano bordo e cursore a mano. I controlli disabilitati
non reagiscono. Tab ed Invio navigano tra i pulsanti. Nell'editor: Tab inserisce
quattro spazi; Ctrl+A/C/X/V seleziona e usa gli appunti; Ctrl+Z/Y annulla e
ripristina; Shift estende la selezione; Shift+rotella scorre orizzontalmente.
La grafica si adatta alla finestra mantenendo le proporzioni.

## Sorgenti e ricostruzione

Python 3.10 o successivo e Pygame. Verificato con Python 3.13.7 e Pygame 2.6.1.

```powershell
python -m pip install -r requirements.txt
python main.py
python -m unittest discover -s tests -v
python main.py --smoke-test smoke-source.json --screenshots screenshots
python -m pip install pyinstaller==6.20.0
python build_release.py
```

`build_release.py` esegue i test, costruisce `StazioneScelte.exe`, verifica
l'eseguibile senza aprire finestre e produce i due ZIP. Chiudere l'app prima
di ricostruirla. Gli archivi non contengono progressi, cache o file di build.

- `engine.py`: parser, semantica, tracce e stati dei controlli.
- `missions.py`: missioni, blocchi, domini, risultati attesi e verifica.
- `lessons.py`: spiegazioni, differenze di linguaggio e previsioni.
- `activities.py`: esperimenti guidati, turni dei droni e banco interattivo.
- `logic.py`: normalizzazione degli ingressi e tabelle di verità.
- `main.py`, `ui.py`, `scene.py`: interfaccia, editor e stazione vettoriale.
- `storage.py`: preferenze, bozze e progressi locali validati.
- `tests/`: comportamento, casi errati, percorsi completi, pause e salvataggi.
- `PIANO.md`: proposta didattica e scelte del progetto.

## Riferimenti

Sintassi e semantica sono state confrontate con le fonti dei linguaggi:
[Python: if](https://docs.python.org/3/reference/compound_stmts.html#if),
[ECMAScript: if](https://tc39.es/ecma262/multipage/ecmascript-language-statements-and-declarations.html#sec-if-statement),
[Java: if](https://docs.oracle.com/javase/specs/jls/se25/html/jls-14.html#jls-14.9),
[C11 N1570, §6.8.4.1](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf).
Per testo e valori logici:
[Python: truth value testing](https://docs.python.org/3/library/stdtypes.html#truth-value-testing),
[Java: XOR booleano](https://docs.oracle.com/javase/specs/jls/se25/html/jls-15.html#jls-15.22.2),
[Java: String.isEmpty](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/String.html#isEmpty()).
Spiegazioni e grafica del laboratorio sono originali. Le licenze dei componenti
distribuiti sono in `LICENZE.txt`.
