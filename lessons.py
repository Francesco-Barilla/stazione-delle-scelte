"""Original explanations and prediction challenges about misconceptions."""
from dataclasses import dataclass
from engine import COMMANDS, FIELDS, LANGUAGES, generate, parse
from logic import NOTES
from missions import Case

LANGUAGE_NOTES = {
    'Python': '''Python usa if, elif, else. I due punti aprono il blocco e il rientro ne stabilisce l’appartenenza. Un else deve essere allineato all’if corrispondente. else if non è la forma della catena: scrivi elif.

Confronti: ==, !=, <, <=, >, >=. Logica: and, or, not. I booleani si scrivono True e False. = assegna un valore, == lo confronta: if batteria = 30 non è sintassi valida. L’operatore := esiste in Python, ma non è previsto in questo laboratorio.

Un numero può essere usato come condizione: 0 è falso e un intero diverso da 0 è vero. Per rendere chiara l’intenzione usa un confronto esplicito. Python permette confronti concatenati: 10 <= peso <= 20 controlla entrambi i confini. La forma con and rende più semplice confrontare i quattro linguaggi.

not si applica dopo i confronti e prima di and/or. Usa parentesi per dichiarare il raggruppamento: not (batteria >= 30). and e or valutano da sinistra e saltano la parte destra quando il risultato è già deciso.''',
    'JavaScript': '''JavaScript usa if (...), else if (...) ed else. Le graffe delimitano i blocchi; il punto e virgola conclude le azioni. else if è un else seguito da un nuovo if. Il laboratorio mostra sempre le graffe per rendere chiara l’appartenenza dei rami.

Logica: &&, ||, !. Booleani: true e false. Per gli interi della stazione sono disponibili == e ===; === confronta anche il tipo, mentre == può effettuare conversioni. Nella programmazione generale è utile preferire confronti espliciti e conoscere questa differenza. Qui non ci sono stringhe, null o undefined.

= assegna, non confronta. if (batteria = 30) in JavaScript assegna 30 e usa il valore assegnato come condizione: è una possibile istruzione del linguaggio, ma è bloccata qui perché i dati della missione sono di sola lettura.

0 è falso e gli altri interi sono veri. 10 <= peso <= 20 non controlla un intervallo: viene prima prodotto un booleano e poi confrontato con 20. Scrivi peso >= 10 && peso <= 20. ! ha precedenza sui confronti: !(batteria >= 30) rende esplicito che cosa stai negando.

&& e || hanno cortocircuito. L’else senza graffe si lega all’if più vicino che può ancora ricevere un else, indipendentemente dall’allineamento visivo. Una ; subito dopo if (...) costituisce un corpo vuoto.''',
    'C': '''C usa if (...), else if (...) ed else. Le graffe delimitano un blocco e le azioni terminano con ;. In C11 true e false sono forniti da stdbool.h: nel frammento didattico i dati booleani sono già disponibili.

Logica: &&, ||, !. Confronti: ==, !=, <, <=, >, >=. = assegna: if (batteria = 30) modifica il dato e verifica il valore assegnato; non chiede se era 30. Il linguaggio lo consente per questo tipo di dato, ma il laboratorio blocca le assegnazioni perché i sensori sono di sola lettura.

Nella condizione 0 è falso, un intero diverso da 0 è vero. Un confronto produce 0 o 1. Perciò 10 <= peso <= 20 non esprime un intervallo: prima confronta 10 con peso e poi confronta 0 oppure 1 con 20. Scrivi peso >= 10 && peso <= 20.

! ha precedenza sui confronti; usa !(batteria >= 30). && e || hanno cortocircuito. Senza graffe, un else si associa all’if precedente più vicino che può riceverlo. L’indentazione da sola non cambia questa regola. if (condizione); contiene un’istruzione vuota: l’azione scritta dopo non è il suo corpo.''',
    'Java': '''Java usa if (...), else if (...) ed else. Graffe e punto e virgola delimitano blocchi e azioni. else if è un else seguito da un nuovo if; le graffe rendono esplicita la struttura.

Logica: &&, ||, !. Booleani: true e false. Confronti: ==, !=, <, <=, >, >=. La condizione di if deve essere booleana: if (batteria) non è valido quando batteria è un intero. Scrivi batteria != 0 oppure il confronto necessario.

= assegna, == confronta. Un’assegnazione intera come if (batteria = 30) non produce il booleano richiesto. Java consente alcune assegnazioni booleane nelle condizioni, ma i dati della missione sono tutti di sola lettura e il laboratorio non consente assegnazioni.

10 <= peso <= 20 non è un confronto concatenato valido: il primo confronto produce un booleano che non può essere confrontato con un intero tramite <=. Scrivi peso >= 10 && peso <= 20. ! richiede un booleano; !(batteria >= 30) nega l’intero confronto.

&& e || hanno cortocircuito. Senza graffe, l’else si lega all’if più vicino che può riceverlo. Una ; subito dopo if (...) è un corpo vuoto; l’azione successiva non diventa condizionata soltanto perché è rientrata.''',
}

for language in LANGUAGES:
    LANGUAGE_NOTES[language] += '\n\nBOOLEANI, BIT E CAMPI DI TESTO\n' + NOTES

PROCEDURE = '''1. Leggi i dati del caso. La stessa regola deve funzionare con dati diversi.
2. Raggiungi il primo if e valuta la sua condizione.
3. Se è vera, entra nel ramo vero. Se è falsa, salta quel corpo e cerca l’alternativa.
4. In una catena elif/else if, controlla la condizione successiva soltanto se le precedenti erano false. Il primo ramo vero esclude le alternative restanti.
5. Un if dentro un ramo viene raggiunto soltanto se quel ramo è stato scelto.
6. Finito il blocco, continua con le istruzioni successive. Un altro if indipendente è una nuova decisione.

Nella traccia VERO e FALSO significano che la condizione è stata valutata. NON VALUTATA significa che il flusso non ha raggiunto quel controllo. Non è sinonimo di falso.

I pulsanti Caso cambiano i dati. Esegui avvia l’animazione; Pausa la ferma; Un passo avanza di una decisione o azione; Indietro permette di rileggere la traccia. I passaggi sono eventi didattici, non tempi di calcolo.'''

MISCONCEPTIONS = '''IF NON È UN CICLO
Un if controlla una condizione quando il programma lo raggiunge. Non ripete il suo corpo finché la condizione resta vera. Ogni caso della stazione avvia una nuova esecuzione.

IF NON RICHIEDE ELSE
Se la condizione è falsa e non c’è else, il corpo viene saltato. Il resto del programma può continuare normalmente.

ELSE NON HA UNA NUOVA CONDIZIONE
È l’alternativa dell’if a cui appartiene. Non significa automaticamente “sbagliato”: un rifiuto o un’attesa possono essere risultati corretti.

IF INDIPENDENTI E CATENE NON SONO INTERCAMBIABILI
Due if possono eseguire due azioni. Una catena sceglie al massimo un ramo. Un altro if scritto dopo la catena rimane indipendente.

L’ORDINE NON È DECISO DAL SIGNIFICATO DEI NOMI
La stazione non sa che urgente è più importante di badge. Questa priorità deve essere scritta mettendo il controllo opportuno prima.

NON VALUTATA NON È FALSA
Un controllo saltato potrebbe essere vero con quei dati, ma il programma non lo ha esaminato.

ANNIDAMENTO E APPARTENENZA DELL’ELSE
Un controllo interno richiede di essere entrati nel ramo esterno. In Python conta il rientro; in C, Java e JavaScript contano la struttura e le graffe. Senza graffe l’else si lega all’if più vicino che può riceverlo.

I CONFINI CONTANO
“Almeno 30” include 30; “più di 30” lo esclude. Prova sempre un valore sotto, uno esatto e uno sopra ogni soglia.

AND E OR
AND richiede entrambe le condizioni. OR ne richiede almeno una e comprende anche il caso vero/vero. Con AND una prima parte falsa evita il secondo controllo; con OR una prima parte vera lo evita.

ASSEGNAZIONE E UGUAGLIANZA
= e == hanno significati diversi. La validità di un’assegnazione dentro if dipende dal linguaggio e dal tipo: leggi la scheda Linguaggi. Qui i dati non vengono modificati dal programma.

DOPO IL BLOCCO SI PROSEGUE
Le istruzioni dopo tutta la selezione vengono eseguite qualunque sia il ramo scelto. Rientrare un’azione sotto un solo ramo cambia il programma.'''

MISCONCEPTIONS += '''\n\nOR NON È XOR
Prova prima A=1 e B=0: entrambi danno vero. Poi accendi anche B: OR resta vero, XOR diventa falso. XOR richiede esattamente un ingresso vero. Il simbolo ^ valuta entrambi gli ingressi, senza cortocircuito.

NOT NON CAMBIA IL SEGNO
NOT 0 dà vero e NOT 1 dà falso. Non dà -1 e non usa ~. In Java trasforma prima il bit in un confronto: !(segnale_a == 1).

UN TESTO NON È IL NUMERO CHE CONTIENE
Nel banco seleziona Campi e scrivi 0: il campo è pieno e il sensore dà vero. Cancella il carattere: ora è falso. Anche la parola false e uno spazio sono contenuto. Controllare la presenza non significa controllare se il contenuto è valido.

CAMPO PIENO NON È UNA CONVERSIONE UNIVERSALE
Per conservare la stessa regola nei quattro linguaggi, prepara un booleano di presenza. Il banco mostra il codice adatto: in C non basta verificare il puntatore a una stringa; in Java una stringa non è una condizione booleana.'''

HOW_TO_PLAY = '''IMPARA FACENDO · TRE ESPERIMENTI
Leggi la regola e prevedi l’ordine per il primo drone. Osserva la decisione e il portello. Nel secondo caso cambiano i dati: la tua previsione cambia? Con il terzo metti alla prova quello che hai scoperto. Perché? collega il risultato alla regola e all’equivoco da evitare.

FACILE · IL TURNO DEI CINQUE DRONI
Sei al controllo della stazione. Per ogni drone leggi i sensori e scegli l’ordine corretto. Un errore mantiene il drone al sicuro e aggiunge un indizio: puoi riprovare. Il quinto drone porta un caso a sorpresa. Non c’è un conto alla rovescia: ragionare vale più della velocità.

IL BANCO LOGICO
Accendi e spegni A e B. Confronta AND, OR, NOT e XOR, poi prova 0/1, booleani e campi di testo. Scrivi 0 oppure uno spazio, poi cancella tutto. La tabella evidenzia il caso che stai provando; il codice mostra come preparare gli ingressi nei quattro linguaggi.

DALLE SCELTE AL CODICE
Laboratorio del codice apre la costruzione a blocchi nel livello Facile. Scegli le condizioni e le azioni, poi verifica la regola. Il rientro dei blocchi rende visibile l’annidamento.

MEDIO · COMPLETA
Sostituisci tutti i ???. La struttura è già presente, ma devi completare una condizione e un’azione. La scheda Comandi rimane disponibile.

DIFFICILE · PROGRAMMA
Scrivi il frammento con selezioni e azioni. Non servono import, classi, main, compilatori o installazioni di altri linguaggi. La scheda Comandi elenca il sottoinsieme accettato.

VERIFICA MISSIONE
La verifica usa tutti i valori del dominio dichiarato, non soltanto il caso visibile. Se trova un problema, mostra un controesempio riproducibile con atteso e ottenuto. Anche la struttura richiesta deve essere raggiunta: inserirla in un ramo morto non basta.

SCOVA L’EQUIVOCO
Leggi il programma e i dati, scegli una previsione e verificala. Poi osserva la traccia per capire il motivo. Le domande riguardano il comportamento effettivo, anche quando il programma è diverso dalla soluzione della missione.

Le sfide sono tutte accessibili. I progressi sono separati per missione, difficoltà e linguaggio. Le bozze restano disponibili tornando alla stessa combinazione. Cambiare lingua apre la relativa bozza o un nuovo esercizio: i tentativi arbitrari non vengono tradotti automaticamente.

Aprire spiegazioni, banco logico o impostazioni mette in pausa la simulazione. Usa Riprendi il volo per continuare. Consultare una soluzione non assegna il completamento né sostituisce la tua bozza.'''


def commands_text(mission, language):
    boolean = ('True / False' if language == 'Python' else 'true / false')
    def field_description(name):
        if name.startswith('testo_'):
            return f'• {name}: testo del caso. Nel codice usa {name.replace("testo_", "campo_")}: {boolean}. Vuoto = falso, almeno un carattere = vero.'
        return f'• {name}: ' + (boolean if FIELDS[name] is bool else 'intero: solo 0 o 1' if name.startswith('segnale_') else 'intero')
    fields = '\n'.join(field_description(name) for name in mission.fields)
    actions = '\n'.join(f'• {name}()' + ('' if language == 'Python' else ';') + ' — ' + label for name, label in COMMANDS.items())
    domains = '\n'.join(f'• {name}: ' + (f'da {values.start} a {values.stop - 1}' if isinstance(values, range) else ', '.join(repr(value) for value in values)) for name, values in mission.domain.items())
    return f'''DATI DI QUESTA MISSIONE
{fields}

DOMINIO DELLA VERIFICA
{domains}
Si verificano tutte le combinazioni di questi valori. Non è una prova su numeri o tipi esterni al dominio.

AZIONI DELLA STAZIONE
{actions}

AMBITO DELL’EDITOR
Scrivi un frammento: if, alternative, annidamenti e azioni senza argomenti. Condizioni con dati, interi, confronti, AND, OR, NOT, XOR (^) e parentesi. I testi sono trasformati nei sensori booleani campo_a e campo_b prima della selezione: il banco logico mostra questa preparazione nel linguaggio scelto. Nell’editor non si scrivono assegnazioni, cicli, funzioni, stringhe o librerie. Un limite del laboratorio non implica che il costrutto sia vietato nel linguaggio completo.

I dati rappresentano una fotografia dei sensori all’inizio del caso. Le azioni non modificano questi dati durante la traccia. Cambiare caso simula una nuova lettura. Limiti: 12000 caratteri, 180 righe, 10 livelli e 300 istruzioni.'''


@dataclass(frozen=True)
class Quiz:
    key: str
    title: str
    mission: str
    code: str
    case: Case
    question: str
    choices: tuple
    answer: int
    explanation: str

    def source(self, language):
        return generate(parse(self.code, 'Python'), language)


QUIZZES = (
    Quiz('senza_else', 'Se non succede nulla…', 'ricarica', 'if batteria < 30:\n    ricarica()\n', Case('Batteria sufficiente', {'batteria': 80}),
         'Che cosa esegue questo programma?', ('Ricarica comunque una volta', 'Nessuna azione', 'Va in errore perché manca else'), 1,
         '80 < 30 è falso. Il corpo viene saltato e il programma finisce. Else è facoltativo: nessuna azione può essere il risultato corretto.'),
    Quiz('non_ciclo', 'Quante ricariche?', 'ricarica', 'if batteria < 30:\n    ricarica()\n', Case('Batteria scarica', {'batteria': 10}),
         'Quante volte viene chiamata ricarica() in questa esecuzione?', ('Finché la batteria raggiunge 30', 'Zero volte', 'Una volta'), 2,
         'If non ripete. Il programma raggiunge una volta la selezione ed esegue una volta l’azione. Qui i dati dei sensori sono la fotografia iniziale del caso.'),
    Quiz('confine', 'Il 30 dimenticato', 'soglia', 'if batteria > 30:\n    parti()\nelse:\n    ricarica()\n', Case('Confine esatto', {'batteria': 30}),
         'Con questo codice, che cosa succede esattamente a 30?', ('Ricarica', 'Parte', 'Esegue entrambi i rami'), 0,
         '30 > 30 è falso: viene eseguito else. Se la consegna dice “almeno 30”, serve >=. I casi sotto e sopra non bastano a scoprire questo errore.'),
    Quiz('due_if', 'Due controlli, due azioni', 'indipendenti', 'if batteria < 20:\n    ricarica()\nif batteria < 60:\n    controlla()\n', Case('Entrambe vere', {'batteria': 10}),
         'Quale sequenza viene eseguita?', ('Soltanto Ricarica', 'Ricarica → Ispeziona', 'Soltanto Ispeziona'), 1,
         'I due if sono indipendenti. Con 10 entrambe le condizioni sono vere e le azioni vengono eseguite nell’ordine scritto.'),
    Quiz('saltata', 'Falsa o non valutata?', 'catena', 'if batteria < 20:\n    ricarica()\nelif batteria < 60:\n    controlla()\nelse:\n    parti()\n', Case('Prima fascia', {'batteria': 10}),
         'Che stato ha il controllo batteria < 60 nella traccia?', ('Falso', 'Vero e quindi eseguito', 'Non valutato'), 2,
         'La prima condizione è già vera. La catena esclude le alternative; il secondo controllo non viene eseguito, anche se 10 < 60 sarebbe vero.'),
    Quiz('ordine', 'La priorità non si indovina', 'priorita', 'if badge:\n    corsia_rapida()\nelif urgente:\n    soccorso()\nelse:\n    corsia_normale()\n', Case('Urgenza con badge', {'badge': True, 'urgente': True}),
         'Questo programma dà davvero priorità all’urgenza?', ('No: sceglie Corsia rapida', 'Sì: urgente è più importante', 'Esegue Corsia rapida e Soccorso'), 0,
         'Viene scelto il primo ramo vero, badge. Per dare priorità all’urgenza bisogna controllarla per prima. I nomi delle variabili non attribuiscono priorità.'),
    Quiz('and_or', 'Un permesso non basta', 'and', 'if badge or autorizzato:\n    apri()\nelse:\n    nega()\n', Case('Un solo permesso', {'badge': True, 'autorizzato': False}),
         'Il codice apre il portello anche senza autorizzazione?', ('No, servono sempre entrambi', 'Sì, perché usa OR', 'Dipende dall’ordine delle parole'), 1,
         'OR richiede almeno una condizione vera, e badge è vero. La regola che richiede entrambi i permessi deve usare AND.'),
    Quiz('or_inclusivo', 'Due pericoli si annullano?', 'or', 'if temperatura >= 70 or fumo:\n    allarme()\nelse:\n    parti()\n', Case('Due segnali', {'temperatura': 90, 'fumo': True}),
         'Caldo e fumo sono entrambi presenti. Che cosa succede?', ('Parte: OR esclude il caso vero/vero', 'Attiva l’allarme due volte', 'Attiva l’allarme una volta'), 2,
         'OR è inclusivo: almeno una comprende anche entrambe. Il corpo dell’if viene eseguito una volta. Il primo confronto è vero e, per cortocircuito, fumo non viene letto.'),
    Quiz('intervallo_or', 'Una fascia troppo larga', 'intervallo', 'if peso >= 10 or peso <= 20:\n    carica()\nelse:\n    controlla()\n', Case('Fuori fascia', {'peso': 35}),
         'Questo programma imbarca un contenitore da 35 kg?', ('Sì: il primo confronto è vero', 'No: 35 non è tra 10 e 20', 'No: OR richiede entrambi i limiti'), 0,
         '35 >= 10 è vero. OR basta già per scegliere carica. Per richiedere contemporaneamente i due limiti si usa AND.'),
    Quiz('interno', 'Un controllo mai raggiunto', 'annidato', 'if badge:\n    if livello >= 2:\n        apri()\n    else:\n        accompagna()\nelse:\n    nega()\n', Case('Esperto senza badge', {'badge': False, 'livello': 3}),
         'Che cosa succede al controllo livello >= 2?', ('Viene valutato e apre', 'Non viene valutato; viene negato l’accesso', 'È falso perché badge è falso'), 1,
         'Il livello non dipende dal valore del badge: vale ancora 3. Tuttavia il programma non raggiunge quel controllo, perché il ramo esterno vero viene saltato.'),
    Quiz('else_interno', 'A quale if appartiene?', 'annidato', 'if badge:\n    if livello >= 2:\n        apri()\n    else:\n        accompagna()\n', Case('Nessun badge', {'badge': False, 'livello': 0}),
         'Con badge falso, viene eseguito accompagna()?', ('Sì: qualunque if falso attiva else', 'Sì: else vale per tutti gli if', 'No: quell’else appartiene all’if interno'), 2,
         'L’intero ramo badge viene saltato, compreso l’else dell’if interno. Non c’è un else esterno. In Python segui il rientro; negli altri linguaggi segui le graffe.'),
    Quiz('dopo', 'Il programma continua', 'turno', 'if badge:\n    apri()\nelse:\n    nega()\nregistra()\n', Case('Accesso negato', {'badge': False}),
         'Qual è la sequenza completa?', ('Nega accesso → Registra passaggio', 'Soltanto Nega accesso', 'Registra soltanto se il badge è valido'), 0,
         'Registra è dopo tutta la selezione. Viene eseguita anche dopo il ramo else. Se la rientrassi dentro un ramo, cambieresti il comportamento.'),
    Quiz('xor_entrambi', 'Due sì fanno un no?', 'xor', 'if badge ^ autorizzato:\n    apri()\nelse:\n    attendi()\n', Case('Due comandi accesi', {'badge': True, 'autorizzato': True}),
         'Con XOR, che ordine riceve il drone?', ('Apri: basta un vero', 'Attendi: sono veri entrambi', 'Apri due volte'), 1,
         'XOR vuole esattamente un vero. Vero/vero dà falso: il drone attende. Con OR il risultato sarebbe vero. Prova il cambio nel banco.'),
    Quiz('xor_nessuno', 'Sono uguali, ma falsi', 'xor', 'if badge ^ autorizzato:\n    apri()\nelse:\n    attendi()\n', Case('Entrambi spenti', {'badge': False, 'autorizzato': False}),
         'Falso XOR falso produce…', ('Vero, perché i valori coincidono', 'Due ordini opposti', 'Falso: manca l’unico vero richiesto'), 2,
         'XOR verifica la differenza dei valori booleani. Anche falso/falso è una coppia uguale e dà falso. Attendi è l’unica azione.'),
    Quiz('not_falso', 'Il no che diventa sì', 'not', 'if not autorizzato:\n    nega()\nelse:\n    apri()\n', Case('Permesso assente', {'autorizzato': False}),
         'Quale ramo viene scelto?', ('Il ramo if: nega', 'Il ramo else: apri', 'Nessuno: falso blocca tutto'), 0,
         'Prima leggi False, poi applica NOT: ottieni True. È la condizione completa a decidere il ramo. Si esegue nega.'),
    Quiz('not_bit', 'Inverti, non cambiare segno', 'bit_not', 'if not (segnale_a == 1):\n    ricarica()\nelse:\n    parti()\n', Case('Segnale a zero', {'segnale_a': 0}),
         'NOT (0 == 1) è vero oppure falso?', ('Falso: zero resta zero', 'Vero: il drone ricarica', 'Vale meno uno'), 1,
         '0 == 1 è falso; NOT lo trasforma in vero. Il drone ricarica. Non è una negazione aritmetica e non è l’operatore ~.'),
    Quiz('testo_zero', 'Lo zero scritto nel campo', 'campo', 'if campo_a:\n    registra()\nelse:\n    attendi()\n', Case('Un carattere presente', {'testo_a': '0'}),
         'Il sensore di presenza campo_a è…', ('Falso: il testo è zero', 'Falso: il testo non è un nome', 'Vero: contiene un carattere'), 2,
         'Il testo "0" non è il numero 0. Il campo contiene un carattere: campo_a è vero e registra viene eseguito. Qui si controlla la presenza, non la validità.'),
    Quiz('testo_spazio', 'Sembra vuoto, ma contiene…', 'campo', 'if campo_a:\n    registra()\nelse:\n    attendi()\n', Case('Un solo spazio', {'testo_a': ' '}),
         'Uno spazio conta come campo pieno?', ('Sì: è presente un carattere', 'No: non si vede', 'Solo in Python'), 0,
         'La regola conta anche gli spazi: campo_a è vero e registra viene eseguito. Se volessimo ignorarli dovremmo introdurre un’altra regola esplicita.'),
    Quiz('testi_diversi', 'Due nomi diversi, due campi pieni', 'campi_xor', 'if campo_a ^ campo_b:\n    parti()\nelse:\n    attendi()\n', Case('Luna e Marte', {'testo_a': 'LUNA', 'testo_b': 'MARTE'}),
         'XOR fa partire la navetta?', ('Sì: i testi sono diversi', 'No: entrambi i sensori sono veri', 'Sì: c’è almeno un campo pieno'), 1,
         'Si confrontano i booleani di presenza, non le parole. Entrambi i campi sono pieni: vero XOR vero è falso. La navetta attende.'),
    Quiz('numero_zero', 'Questo zero è un numero', 'bit_and', 'if segnale_a == 1 and segnale_b == 1:\n    parti()\nelse:\n    attendi()\n', Case('Un motore spento', {'segnale_a': 0, 'segnale_b': 1}),
         'Il valore 0 è scritto sul sensore: basta per partire?', ('Sì: il sensore contiene qualcosa', 'Sì: OR accende entrambi', 'No: il numero 0 significa falso'), 2,
         'Qui gli ingressi sono numeri binari, non campi di testo. A vale 0: il confronto con 1 è falso e AND non consente la partenza.'),
)
