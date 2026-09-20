STAZIONE DELLE SCELTE
Realizzato dal Prof. Barillà Francesco

AVVIO
Fai doppio clic su StazioneScelte.exe oppure su Avvia_Stazione.cmd.
Per gli alunni distribuisci dist/StazioneScelte-Windows.zip.
Estrai tutto lo ZIP in una cartella personale prima di avviare il programma.
La versione Windows funziona offline e non richiede Python o compilatori.

IMPARA FACENDO
Scegli una delle 20 missioni e un linguaggio.
Tre piccoli esperimenti: prevedi un ordine, osserva, riprova con altri dati.
Leggi i dati nel pannello 1 e fai clic su una risposta nel pannello 2.
Da rivedere: riprova evidenzia l'errore e dà un indizio. Corretto resta visibile
anche quando il drone deve stare fermo. Spiegami il perché mostra il motivo.
La traccia distingue VERO, FALSO e NON VALUTATA.

GIOCA
Facile: guida cinque droni, con clic o tasti A-D. Il quinto ha dati a sorpresa.
Gli errori danno indizi e permettono di riprovare, senza limite di tempo.
Laboratorio del codice: costruisci la regola con condizioni e azioni a blocchi.
Medio: premi Completa i ???. La guida distingue condizione e istruzione standard di stampa.
Scrivi solo nella selezione; conserva il rientro e il ; quando è già presente.
Difficile: premi Scrivi qui e digita la regola, una istruzione per riga.
Cosa devo scrivere? mostra dati, comandi ed esempio nel linguaggio scelto.
I sensori sono già forniti dal gioco: usa i loro nomi nelle condizioni.
Controlla il mio codice o Ctrl+Invio verifica tutti i casi del dominio.
Richiesto e ottenuto mostrano la differenza. Guarda l'esecuzione apre i passi
in una vista separata, conservando la bozza e il cursore.
Se c'è un errore, puoi rigiocare il controesempio e leggere il perché.

BANCO LOGICO
Sperimenta AND, OR, NOT e XOR. Cambia booleani, 0/1 e campi di testo.
Prova 1 e 1 con OR e XOR, poi il testo "0", uno spazio e un campo vuoto.
La tabella di verità e il codice cambiano insieme agli ingressi.
0 numero significa falso; "0" testo è un campo pieno. Presenza e validità
sono controlli diversi. In Java converti i bit con un confronto.

SCOVA L'EQUIVOCO
20 sfide: prevedi l'effetto del codice, verifica la previsione e osserva.
If indipendenti, catene, annidamenti, AND/OR/NOT/XOR, testo e casi al limite.

LINGUAGGI
Python, JavaScript, C e Java. L'editor interpreta soltanto il sottoinsieme
descritto nella scheda Comandi. Non è un compilatore o un IDE completo.

F11: schermo intero. Esc: chiudi spiegazione o torna alla Home.
Aprire una spiegazione, il banco o le impostazioni mette il volo in pausa.
Riprendi la decisione continua dal punto in cui eri arrivato.
Editor: Ctrl+A/C/X/V, Ctrl+Z/Y, Tab; Shift+rotella per lo scorrimento orizzontale.
Progressi e bozze si salvano in progressi_selezione.json accanto all'app.

PRIMA LEZIONE
Impara: Una ricarica se serve; poi Il portello di bordo.
Passa a Gioca/Facile e infine a Scova l'equivoco.

Per i sorgenti: python -m pip install -r requirements.txt
Poi: python main.py
Istruzioni complete e riferimenti: README.md.


PROGRESSI E REPORT PER IL DOCENTE
Il pulsante Progressi e report è sempre in basso. Mostra missioni Gioca
completate, risposte corrette, errori e percentuale di errore:
errori / risposte effettivamente controllate x 100. Senza risposte compare —.
Impara, Gioca e Quiz sono distinti. Ogni verifica del programma conta come
un tentativo, non come un tentativo per ciascun caso automatico.
Ripetere lo stesso controllo senza cambiare risposta non aggiunge tentativi;
una risposta modificata viene contata. Rivedere una traccia non conta.
Sono visibili anche aiuti e soluzioni consultati. I vecchi completamenti
restano; non vengono inventati tentativi o errori antecedenti all'aggiornamento.
Inserisci facoltativamente un nome/codice: identifica l'intero storico di
questa copia. Esporta report CSV crea un file nella cartella report accanto
ai progressi, con tutti i linguaggi/livelli e dettaglio delle attività.
Il registro è locale e modificabile, non sincronizzato né una prova
antimanomissione. Per il controllo in classe, raccogli i CSV degli studenti.
