"""Twenty authored missions, with exhaustive finite test domains."""
from dataclasses import dataclass
from native_io import output_statement, output_explanation
from itertools import product
from engine import COMMANDS, FIELDS, CodeError, describe, generate, parse, run, structure_ok, walk
from logic import present

DIFFICULTIES = ('Facile', 'Medio', 'Difficile')
GROUPS = ('Tutte', 'Prime scelte', 'Più condizioni', 'Annidamento', 'Logica e dati')
DEFAULT_DATA = dict(batteria=50, temperatura=20, peso=15, livello=1,
                    badge=False, autorizzato=False, urgente=False, fragile=False, fumo=False,
                    segnale_a=0, segnale_b=0, campo_a=False, campo_b=False)


@dataclass(frozen=True)
class Case:
    label: str
    values: dict

    @property
    def data(self):
        data = DEFAULT_DATA | self.values
        for suffix in ('a', 'b'):
            if 'testo_' + suffix in self.values:
                data['campo_' + suffix] = present(self.values['testo_' + suffix])
        return data


@dataclass(frozen=True)
class Slot:
    label: str
    kind: str
    options: tuple
    answer: str
    depth: int = 0


def condition(label, answer, alternatives, depth=0):
    return Slot(label, 'condition', tuple(alternatives), answer, depth)


def command(label, answer, alternatives, depth=0):
    return Slot(label, 'action', tuple(alternatives), answer, depth)


@dataclass(frozen=True)
class Mission:
    key: str
    title: str
    subtitle: str
    group: str
    target: str
    objective: str
    concept: str
    trap: str
    template: str
    slots: tuple
    cases: tuple
    domain: dict
    rule: object
    hints: tuple

    @property
    def fields(self):
        return tuple(self.domain)

    def program(self, choices, language):
        code = self.template
        for index, slot in enumerate(self.slots):
            selected = choices[index] if index < len(choices) else -1
            if type(selected) is not int or not 0 <= selected < len(slot.options):
                raise CodeError('Completa tutti i blocchi: fai clic su ogni scelta e seleziona una condizione o un’azione.')
            code = code.replace('{' + str(index) + '}', slot.options[selected])
        return generate(parse(code, 'Python'), language)

    def correct_choices(self):
        return [slot.options.index(slot.answer) for slot in self.slots]

    def solution(self, language):
        return self.program(self.correct_choices(), language)

    def starter(self, language, difficulty):
        if difficulty == 'Difficile':
            return ''
        code = self.solution(language)
        nodes = list(walk(parse(code, language)))
        lines = code.splitlines()
        first_if = next(n for n in nodes if n.kind == 'if')
        if language == 'Python':
            lines[first_if.line - 1] = 'if ???:'
        else:
            lines[first_if.line - 1] = 'if (???) {'
        first_action = next(n for n in nodes if n.kind == 'action')
        lines[first_action.line - 1] = lines[first_action.line - 1].replace(output_statement(first_action.value, language).rstrip(';'), '???')
        return '\n'.join(lines) + '\n'

    def all_cases(self):
        for index, values in enumerate(product(*self.domain.values())):
            yield Case(f'Verifica {index + 1}', dict(zip(self.domain, values)))


def cases(*rows):
    return tuple(Case(label, data) for label, data in rows)


MISSIONS = (
    Mission('ricarica', '01 · Una ricarica se serve', 'Un if può anche non fare nulla.', 'Prime scelte', 'if',
        'Se la batteria è sotto il 30%, stampa "ricarica". Negli altri casi non eseguire azioni.',
        'La condizione viene controllata una volta. Se è falsa e non c’è else, si salta il corpo e si continua dopo l’if.',
        'Non vedere un’azione non significa che il programma sia guasto: con batteria al 30% o più è proprio il risultato richiesto. If non ripete come un ciclo.',
        'if {0}:\n    print("{1}")\n',
        (condition('SE · energia insufficiente', 'batteria < 30', ('batteria > 30', 'batteria < 30', 'batteria <= 30')),
         command('ALLORA · una sola azione', 'ricarica', ('parti', 'attendi', 'ricarica'), 1)),
        cases(('Scarico', {'batteria': 10}), ('Appena sotto', {'batteria': 29}), ('Sulla soglia', {'batteria': 30}), ('Carico', {'batteria': 90})),
        {'batteria': range(101)}, lambda d: ('ricarica',) if d['batteria'] < 30 else (),
        ('Sotto il 30 esclude il valore 30.', 'Se la condizione è falsa non serve inventare un’azione.', 'Prova 29, 30 e 31: solo 29 richiede una ricarica.')),
    Mission('portello', '02 · Il portello di bordo', 'Due alternative, una decisione.', 'Prime scelte', 'else',
        'Se badge è vero, "apri". Altrimenti "nega". Devi scegliere esattamente una delle due azioni.',
        'If/else seleziona uno dei due rami. Else non ha una condizione propria: è l’alternativa quando l’if a cui appartiene è falso.',
        'Else non significa “errore”: dipende dalla regola. Un accesso negato può essere la decisione corretta. I due rami non vengono eseguiti entrambi.',
        'if {0}:\n    print("{1}")\nelse:\n    print("{2}")\n',
        (condition('SE · leggi il badge', 'badge', ('not badge', 'True', 'badge')),
         command('ALLORA', 'apri', ('nega', 'apri', 'attendi'), 1),
         command('ALTRIMENTI', 'nega', ('nega', 'parti', 'apri'), 1)),
        cases(('Badge valido', {'badge': True}), ('Senza badge', {'badge': False})),
        {'badge': (False, True)}, lambda d: ('apri',) if d['badge'] else ('nega',),
        ('Badge è già un dato vero/falso.', 'Metti apri nel ramo vero e nega nell’alternativa.', 'Else non si scrive con una condizione tra parentesi.')),
    Mission('soglia', '03 · Pronti al decollo', 'Il confine è un caso da provare.', 'Prime scelte', 'else',
        'Con almeno il 30% di batteria stampa "parti". Con meno del 30% stampa "ricarica".',
        '“Almeno 30” comprende 30. Il confronto >= è vero anche quando i due valori sono uguali.',
        'Provare soltanto 10 e 90 non distingue > da >=. Il caso decisivo è esattamente 30.',
        'if {0}:\n    print("{1}")\nelse:\n    print("{2}")\n',
        (condition('SE · energia sufficiente', 'batteria >= 30', ('batteria > 30', 'batteria <= 30', 'batteria >= 30')),
         command('ALLORA', 'parti', ('parti', 'ricarica', 'attendi'), 1),
         command('ALTRIMENTI', 'ricarica', ('controlla', 'ricarica', 'parti'), 1)),
        cases(('Quasi pronto', {'batteria': 29}), ('Esattamente 30', {'batteria': 30}), ('Appena sopra', {'batteria': 31}), ('Pieno', {'batteria': 100})),
        {'batteria': range(101)}, lambda d: ('parti',) if d['batteria'] >= 30 else ('ricarica',),
        ('Scrivi a parole cosa deve succedere con batteria uguale a 30.', '“Almeno” corrisponde a >=.', 'Controlla anche 29: deve ancora ricaricare.')),
    Mission('indipendenti', '04 · Due controlli distinti', 'A volte servono entrambe le azioni.', 'Più condizioni', 'independent',
        'Prima "ricarica" se batteria < 30. Poi, con un altro if indipendente, "proteggi" se fragile è vero. Possono servire entrambe, una o nessuna azione.',
        'Due if consecutivi sono due decisioni. Il secondo viene controllato anche quando il primo era vero.',
        'Sostituire il secondo if con elif/else if impedisce la protezione del carico quando è già stata scelta la ricarica.',
        'if {0}:\n    print("{1}")\nif {2}:\n    print("{3}")\n',
        (condition('PRIMO IF', 'batteria < 30', ('batteria < 30', 'batteria >= 30', 'batteria == 30')),
         command('SE VERO · prima azione', 'ricarica', ('proteggi', 'ricarica', 'parti'), 1),
         condition('SECONDO IF · indipendente', 'fragile', ('not fragile', 'fragile', 'False')),
         command('SE VERO · seconda azione', 'proteggi', ('ricarica', 'parti', 'proteggi'), 1)),
        cases(('Entrambi i bisogni', {'batteria': 10, 'fragile': True}), ('Solo ricarica', {'batteria': 10, 'fragile': False}), ('Solo protezione', {'batteria': 80, 'fragile': True}), ('Nessun bisogno', {'batteria': 80, 'fragile': False})),
        {'batteria': range(101), 'fragile': (False, True)}, lambda d: (('ricarica',) if d['batteria'] < 30 else ()) + (('proteggi',) if d['fragile'] else ()),
        ('I due controlli devono poter essere entrambi veri.', 'Servono due if allo stesso livello.', 'Nel caso scarico e fragile la sequenza è Ricarica → Proteggi carico.')),
    Mission('catena', '05 · Tre fasce di energia', 'Si ferma alla prima condizione vera.', 'Più condizioni', 'chain',
        'Sotto il 20% "ricarica". Da 20% a meno di 60% "controlla". Dal 60% in su "parti". Usa una catena if/elif/else.',
        'Le condizioni di una catena vengono esaminate dall’alto. Dopo il primo ramo vero le alternative restanti non vengono valutate.',
        'Con batteria 10 anche batteria < 60 sarebbe vera, ma non viene controllata. “Non valutata” non significa “falsa”.',
        'if {0}:\n    print("{1}")\nelif {2}:\n    print("{3}")\nelse:\n    print("{4}")\n',
        (condition('IF · prima fascia', 'batteria < 20', ('batteria < 60', 'batteria < 20', 'batteria <= 20')),
         command('ALLORA', 'ricarica', ('parti', 'ricarica', 'controlla'), 1),
         condition('ALTRIMENTI SE · seconda fascia', 'batteria < 60', ('batteria <= 60', 'batteria > 60', 'batteria < 60')),
         command('ALLORA', 'controlla', ('controlla', 'parti', 'ricarica'), 1),
         command('ALTRIMENTI · terza fascia', 'parti', ('ricarica', 'parti', 'attendi'), 1)),
        cases(('Molto scarico', {'batteria': 10}), ('Confine 20', {'batteria': 20}), ('Quasi 60', {'batteria': 59}), ('Confine 60', {'batteria': 60}), ('Pieno', {'batteria': 100})),
        {'batteria': range(101)}, lambda d: ('ricarica',) if d['batteria'] < 20 else ('controlla',) if d['batteria'] < 60 else ('parti',),
        ('Metti la fascia più piccola prima di quella che la comprende.', 'Quando arrivi al secondo controllo sai già che batteria non è sotto 20.', 'Con 10 si esegue soltanto ricarica, non anche controlla.')),
    Mission('priorita', '06 · Prima il soccorso', 'Le condizioni possono sovrapporsi.', 'Più condizioni', 'chain',
        'Se urgente è vero, "soccorso". Altrimenti, se badge è vero, "corsia_rapida". Negli altri casi "corsia_normale". L’urgenza ha sempre priorità.',
        'Quando più condizioni possono essere vere, il loro ordine esprime una priorità. Un caso urgente con badge deve comunque ricevere soccorso.',
        'Una catena non sceglie la condizione “più importante” da sola: segue l’ordine scritto dal programmatore.',
        'if {0}:\n    print("{1}")\nelif {2}:\n    print("{3}")\nelse:\n    print("{4}")\n',
        (condition('IF · prima priorità', 'urgente', ('badge', 'urgente', 'not urgente')),
         command('ALLORA', 'soccorso', ('corsia_rapida', 'soccorso', 'attendi'), 1),
         condition('ALTRIMENTI SE', 'badge', ('badge', 'not badge', 'urgente')),
         command('ALLORA', 'corsia_rapida', ('soccorso', 'corsia_normale', 'corsia_rapida'), 1),
         command('ALTRIMENTI', 'corsia_normale', ('corsia_normale', 'nega', 'soccorso'), 1)),
        cases(('Urgenza con badge', {'urgente': True, 'badge': True}), ('Solo urgenza', {'urgente': True, 'badge': False}), ('Solo badge', {'urgente': False, 'badge': True}), ('Visita ordinaria', {'urgente': False, 'badge': False})),
        {'urgente': (False, True), 'badge': (False, True)}, lambda d: ('soccorso',) if d['urgente'] else ('corsia_rapida',) if d['badge'] else ('corsia_normale',),
        ('Prova il caso in cui urgente e badge sono entrambi veri.', 'Il controllo urgente deve venire per primo.', 'Else raccoglie tutti i casi rimasti, non controlla badge una seconda volta.')),
    Mission('and', '07 · Due permessi necessari', 'AND richiede entrambe le condizioni.', 'Più condizioni', 'and',
        'Esegui "apri" soltanto se badge e autorizzato sono entrambi veri. In ogni altro caso "nega". Usa AND nella condizione.',
        'AND è vero soltanto con due condizioni vere. Con la prima falsa, la seconda parte non serve e non viene valutata: è il cortocircuito.',
        'OR consentirebbe l’accesso anche con un solo permesso. “Entrambi” non significa “almeno uno”.',
        'if {0}:\n    print("{1}")\nelse:\n    print("{2}")\n',
        (condition('SE · entrambi i permessi', 'badge and autorizzato', ('badge or autorizzato', 'badge and autorizzato', 'badge')),
         command('ALLORA', 'apri', ('nega', 'apri', 'accompagna'), 1),
         command('ALTRIMENTI', 'nega', ('nega', 'apri', 'attendi'), 1)),
        cases(('Due permessi', {'badge': True, 'autorizzato': True}), ('Solo badge', {'badge': True, 'autorizzato': False}), ('Solo autorizzazione', {'badge': False, 'autorizzato': True}), ('Nessun permesso', {'badge': False, 'autorizzato': False})),
        {'badge': (False, True), 'autorizzato': (False, True)}, lambda d: ('apri',) if d['badge'] and d['autorizzato'] else ('nega',),
        ('I due casi con un solo permesso devono entrambi negare l’accesso.', 'In Python scrivi and; negli altri linguaggi &&.', 'Il risultato di AND è vero soltanto nel caso vero/vero.')),
    Mission('or', '08 · Basta un allarme', 'OR comprende anche due condizioni vere.', 'Più condizioni', 'or',
        'Attiva "allarme" se temperatura è almeno 70 oppure se fumo è vero. Altrimenti "parti". Usa OR.',
        'OR è vero quando almeno una condizione è vera, compreso il caso in cui lo sono entrambe. Se la prima è già vera, la seconda non viene valutata.',
        '“Oppure” qui è inclusivo. Non significa “una o l’altra ma non entrambe”. Due segnali di pericolo non annullano l’allarme.',
        'if {0}:\n    print("{1}")\nelse:\n    print("{2}")\n',
        (condition('SE · almeno un segnale', 'temperatura >= 70 or fumo', ('temperatura >= 70 and fumo', 'temperatura > 70 or fumo', 'temperatura >= 70 or fumo')),
         command('ALLORA', 'allarme', ('allarme', 'parti', 'controlla'), 1),
         command('ALTRIMENTI', 'parti', ('attendi', 'parti', 'allarme'), 1)),
        cases(('Caldo e fumo', {'temperatura': 90, 'fumo': True}), ('Solo caldo', {'temperatura': 70, 'fumo': False}), ('Solo fumo', {'temperatura': 20, 'fumo': True}), ('Tutto regolare', {'temperatura': 69, 'fumo': False})),
        {'temperatura': range(0, 101), 'fumo': (False, True)}, lambda d: ('allarme',) if d['temperatura'] >= 70 or d['fumo'] else ('parti',),
        ('Prova i casi con un solo segnale di pericolo.', 'In Python usa or; negli altri linguaggi ||.', 'La soglia include 70. Quando sono veri entrambi, l’allarme si attiva una volta.')),
    Mission('intervallo', '09 · Il carico giusto', 'Due confini, una fascia.', 'Più condizioni', 'and',
        'Esegui "carica" per i contenitori con peso da 10 a 20 kg, estremi inclusi. Per gli altri stampa "controlla". Usa due confronti collegati con AND.',
        'Per essere dentro un intervallo devono valere insieme il limite inferiore e quello superiore. “Da 10 a 20 inclusi” comprende entrambi gli estremi.',
        'peso >= 10 OR peso <= 20 è vero per qualunque peso. Inoltre 10 <= peso <= 20 non ha lo stesso significato in tutti i linguaggi: ripeti il dato nei due confronti.',
        'if {0}:\n    print("{1}")\nelse:\n    print("{2}")\n',
        (condition('SE · dentro la fascia', 'peso >= 10 and peso <= 20', ('peso >= 10 or peso <= 20', 'peso > 10 and peso < 20', 'peso >= 10 and peso <= 20')),
         command('ALLORA', 'carica', ('carica', 'controlla', 'parti'), 1),
         command('ALTRIMENTI', 'controlla', ('carica', 'controlla', 'attendi'), 1)),
        cases(('Troppo leggero', {'peso': 9}), ('Confine inferiore', {'peso': 10}), ('Dentro la fascia', {'peso': 15}), ('Confine superiore', {'peso': 20}), ('Troppo pesante', {'peso': 21})),
        {'peso': range(0, 41)}, lambda d: ('carica',) if 10 <= d['peso'] <= 20 else ('controlla',),
        ('Un contenitore deve superare entrambi i controlli.', 'Ripeti peso: peso >= 10 AND peso <= 20.', 'Verifica 9, 10, 20 e 21.')),
    Mission('annidato', '10 · Dentro il modulo', 'Il controllo interno ha una porta d’ingresso.', 'Annidamento', 'nested',
        'Senza badge stampa "nega". Con badge controlla il livello: se è almeno 2 "apri", altrimenti "accompagna". Usa un if dentro il ramo vero del primo.',
        'Il controllo esterno decide se raggiungere quello interno. Il livello viene esaminato soltanto quando il badge è valido.',
        'Se badge è falso, livello >= 2 è NON VALUTATA, anche con livello 3. L’else interno gestisce un livello insufficiente; l’else esterno gestisce il badge mancante.',
        'if {0}:\n    if {1}:\n        print("{2}")\n    else:\n        print("{3}")\nelse:\n    print("{4}")\n',
        (condition('IF ESTERNO · accesso', 'badge', ('not badge', 'badge', 'True')),
         condition('IF INTERNO · livello', 'livello >= 2', ('livello > 2', 'livello >= 2', 'livello < 2'), 1),
         command('VERO INTERNO', 'apri', ('accompagna', 'nega', 'apri'), 2),
         command('ELSE INTERNO', 'accompagna', ('accompagna', 'nega', 'parti'), 2),
         command('ELSE ESTERNO', 'nega', ('apri', 'nega', 'accompagna'), 1)),
        cases(('Senza badge, esperto', {'badge': False, 'livello': 3}), ('Badge, principiante', {'badge': True, 'livello': 1}), ('Badge, livello 2', {'badge': True, 'livello': 2}), ('Senza badge, principiante', {'badge': False, 'livello': 0})),
        {'badge': (False, True), 'livello': range(4)}, lambda d: ('nega',) if not d['badge'] else ('apri',) if d['livello'] >= 2 else ('accompagna',),
        ('Distingui il problema badge dal problema livello.', 'Il controllo del livello va dentro il ramo vero del controllo badge.', 'Segui i rientri: i due else appartengono a due if diversi.')),
    Mission('soccorso', '11 · Soccorso tra le stelle', 'La stessa energia in contesti diversi.', 'Annidamento', 'nested',
        'Se urgente: con batteria almeno 30 "soccorso", altrimenti "ricarica". Se non urgente: con batteria almeno 30 "parti", altrimenti "attendi". Usa decisioni annidate.',
        'Un annidamento organizza prima il contesto e poi la scelta al suo interno. La stessa condizione può avere conseguenze diverse in due rami.',
        'Mettere tutti gli if allo stesso livello può attivare azioni incompatibili. Il codice dentro un ramo non si esegue se il ramo non è stato scelto.',
        'if {0}:\n    if {1}:\n        print("{2}")\n    else:\n        print("{3}")\nelse:\n    if {4}:\n        print("{5}")\n    else:\n        print("{6}")\n',
        (condition('IF ESTERNO · urgenza', 'urgente', ('urgente', 'not urgente', 'badge')),
         condition('IF INTERNO · soccorso possibile', 'batteria >= 30', ('batteria > 30', 'batteria >= 30', 'batteria < 30'), 1),
         command('VERO · contesto urgente', 'soccorso', ('parti', 'soccorso', 'ricarica'), 2),
         command('ELSE · contesto urgente', 'ricarica', ('ricarica', 'attendi', 'parti'), 2),
         condition('NEL RAMO NON URGENTE · energia', 'batteria >= 30', ('batteria < 30', 'batteria >= 30', 'True'), 1),
         command('VERO · contesto ordinario', 'parti', ('soccorso', 'ricarica', 'parti'), 2),
         command('ELSE · contesto ordinario', 'attendi', ('attendi', 'soccorso', 'parti'), 2)),
        cases(('Urgenza, pronto', {'urgente': True, 'batteria': 30}), ('Urgenza, scarico', {'urgente': True, 'batteria': 29}), ('Ordinario, pronto', {'urgente': False, 'batteria': 60}), ('Ordinario, scarico', {'urgente': False, 'batteria': 10})),
        {'urgente': (False, True), 'batteria': range(101)}, lambda d: (('soccorso',) if d['batteria'] >= 30 else ('ricarica',)) if d['urgente'] else (('parti',) if d['batteria'] >= 30 else ('attendi',)),
        ('Prima separa urgente e non urgente.', 'In ciascun ramo controlla se batteria è almeno 30.', 'Con energia insufficiente l’urgenza richiede ricarica, il caso ordinario attesa.')),
    Mission('turno', '12 · Il turno completo', 'La selezione finisce; il programma prosegue.', 'Annidamento', 'nested',
        'Senza badge "nega". Con badge: sotto il 20% "ricarica"; altrimenti, se fragile, "proteggi"; altrimenti "parti". Alla fine esegui sempre "registra", una sola volta.',
        'Il codice dopo la selezione viene eseguito qualunque sia il ramo scelto. Una catena interna può essere contenuta nel ramo di un if esterno.',
        'Registra dentro un solo ramo non significa registra sempre. Un else non prende tutto il codice che lo segue: contano rientri e graffe.',
        'if {0}:\n    if {1}:\n        print("{2}")\n    elif {3}:\n        print("{4}")\n    else:\n        print("{5}")\nelse:\n    print("{6}")\nprint("{7}")\n',
        (condition('IF ESTERNO · badge', 'badge', ('badge', 'not badge', 'True')),
         condition('IF INTERNO · prima priorità', 'batteria < 20', ('batteria <= 20', 'batteria < 20', 'batteria >= 20'), 1),
         command('ALLORA', 'ricarica', ('proteggi', 'parti', 'ricarica'), 2),
         condition('ALTRIMENTI SE · carico', 'fragile', ('not fragile', 'fragile', 'True'), 1),
         command('ALLORA', 'proteggi', ('proteggi', 'parti', 'ricarica'), 2),
         command('ELSE INTERNO', 'parti', ('nega', 'parti', 'attendi'), 2),
         command('ELSE ESTERNO', 'nega', ('apri', 'attendi', 'nega'), 1),
         command('DOPO TUTTA LA SELEZIONE', 'registra', ('parti', 'registra', 'controlla'))),
        cases(('Senza badge', {'badge': False, 'batteria': 90, 'fragile': True}), ('Scarico e fragile', {'badge': True, 'batteria': 10, 'fragile': True}), ('Fragile, energia 20', {'badge': True, 'batteria': 20, 'fragile': True}), ('Pronto', {'badge': True, 'batteria': 90, 'fragile': False})),
        {'badge': (False, True), 'batteria': range(101), 'fragile': (False, True)}, lambda d: (('nega',) if not d['badge'] else ('ricarica',) if d['batteria'] < 20 else ('proteggi',) if d['fragile'] else ('parti',)) + ('registra',),
        ('Risolvi prima il badge, poi la catena di priorità interna.', 'La ricarica precede la protezione quando sono necessarie entrambe.', 'Metti registra fuori da tutti i rami, senza rientro in Python.')),
)
MISSIONS += (
    Mission('not', '13 · Il permesso capovolto', 'NOT cambia il verso della decisione.', 'Logica e dati', 'not',
        'Il drone arriva al modulo riservato. Se NON è autorizzato, "nega". Altrimenti "apri". Usa NOT.',
        'NOT inverte un booleano: not False è True e not True è False. Lavora su un ingresso solo.',
        'NOT non significa un numero negativo. Inverte il valore logico; il secondo ingresso non serve.',
        'if {0}:\n    print("{1}")\nelse:\n    print("{2}")\n',
        (condition('SE · manca il permesso', 'not autorizzato', ('autorizzato', 'not autorizzato', 'True')),
         command('ALLORA', 'nega', ('apri', 'nega', 'attendi'), 1), command('ALTRIMENTI', 'apri', ('nega', 'attendi', 'apri'), 1)),
        cases(('Permesso assente', {'autorizzato': False}), ('Permesso presente', {'autorizzato': True})),
        {'autorizzato': (False, True)}, lambda d: ('nega',) if not d['autorizzato'] else ('apri',),
        ('Prima leggi autorizzato, poi capovolgilo.', 'NOT falso diventa vero.', 'In Python usa not; negli altri linguaggi !.')),
    Mission('bit_and', '14 · Due motori pronti', 'AND con due soli valori: 0 e 1.', 'Logica e dati', 'and',
        'Per il decollo servono entrambi i motori pronti. segnale_a e segnale_b valgono 0 o 1. Se sono entrambi 1, "parti"; altrimenti "attendi".',
        '0 rappresenta falso e 1 vero. Due confronti == 1 producono booleani e AND richiede entrambi.',
        '1 e 0 non bastano: un motore pronto non rende pronto anche l’altro. In Java un intero da solo non è una condizione.',
        'if {0}:\n    print("{1}")\nelse:\n    print("{2}")\n',
        (condition('SE · entrambi pronti', 'segnale_a == 1 and segnale_b == 1', ('segnale_a == 1 or segnale_b == 1', 'segnale_a == 1 and segnale_b == 1', 'segnale_a == 0')),
         command('ALLORA', 'parti', ('parti', 'attendi', 'allarme'), 1), command('ALTRIMENTI', 'attendi', ('parti', 'attendi', 'ricarica'), 1)),
        cases(('Nessun motore', {'segnale_a': 0, 'segnale_b': 0}), ('Solo A', {'segnale_a': 1, 'segnale_b': 0}), ('Solo B', {'segnale_a': 0, 'segnale_b': 1}), ('Entrambi', {'segnale_a': 1, 'segnale_b': 1})),
        {'segnale_a': (0, 1), 'segnale_b': (0, 1)}, lambda d: ('parti',) if d['segnale_a'] == 1 and d['segnale_b'] == 1 else ('attendi',),
        ('Prova 1/0 e 0/1: la partenza deve restare bloccata.', 'Confronta ogni segnale con 1.', 'Unisci i confronti con AND.')),
    Mission('bit_or', '15 · Un segnale basta', 'OR include il caso 1 e 1.', 'Logica e dati', 'or',
        'Due sensori possono rilevare un guasto. Se almeno un segnale vale 1, "allarme". Solo con entrambi a 0 puoi "parti".',
        'OR è falso soltanto con 0 e 0. Anche 1 e 1 richiede l’allarme.',
        'Due segnali accesi non si annullano. Quello sarebbe il risultato di XOR, non di OR.',
        'if {0}:\n    print("{1}")\nelse:\n    print("{2}")\n',
        (condition('SE · almeno un guasto', 'segnale_a == 1 or segnale_b == 1', ('segnale_a == 1 and segnale_b == 1', 'segnale_a != segnale_b', 'segnale_a == 1 or segnale_b == 1')),
         command('ALLORA', 'allarme', ('parti', 'allarme', 'attendi'), 1), command('ALTRIMENTI', 'parti', ('parti', 'allarme', 'nega'), 1)),
        cases(('Nessun guasto', {'segnale_a': 0, 'segnale_b': 0}), ('Guasto A', {'segnale_a': 1, 'segnale_b': 0}), ('Guasto B', {'segnale_a': 0, 'segnale_b': 1}), ('Due guasti', {'segnale_a': 1, 'segnale_b': 1})),
        {'segnale_a': (0, 1), 'segnale_b': (0, 1)}, lambda d: ('allarme',) if d['segnale_a'] == 1 or d['segnale_b'] == 1 else ('parti',),
        ('L’unico caso tranquillo è 0/0.', 'Serve OR, non AND.', 'Controlla anche 1/1: allarme una volta.')),
    Mission('xor', '16 · Un solo pilota', 'XOR: uno oppure l’altro, non entrambi.', 'Logica e dati', 'xor',
        'La navetta ha due comandi: badge e autorizzato. Esegui "apri" se esattamente uno è vero; con entrambi veri o entrambi falsi "attendi". Usa XOR (^).',
        'XOR è vero con ingressi diversi e falso con ingressi uguali. Qui i due ingressi sono booleani.',
        'OR e XOR differiscono nel caso vero/vero: OR è vero, XOR è falso. ^ non ha cortocircuito: valuta entrambi.',
        'if {0}:\n    print("{1}")\nelse:\n    print("{2}")\n',
        (condition('SE · un solo comando', 'badge ^ autorizzato', ('badge or autorizzato', 'badge ^ autorizzato', 'badge and autorizzato')),
         command('ALLORA', 'apri', ('attendi', 'apri', 'nega'), 1), command('ALTRIMENTI', 'attendi', ('apri', 'attendi', 'parti'), 1)),
        cases(('Nessun comando', {'badge': False, 'autorizzato': False}), ('Solo A', {'badge': True, 'autorizzato': False}), ('Solo B', {'badge': False, 'autorizzato': True}), ('Comandi in conflitto', {'badge': True, 'autorizzato': True})),
        {'badge': (False, True), 'autorizzato': (False, True)}, lambda d: ('apri',) if d['badge'] != d['autorizzato'] else ('attendi',),
        ('Esattamente uno significa che i due valori devono essere diversi.', 'Con vero/vero devi attendere.', 'Il simbolo ^ calcola XOR sui booleani predisposti.')),
    Mission('bit_not', '17 · Inverti il segnale', 'NOT 0 = 1, NOT 1 = 0.', 'Logica e dati', 'not',
        'Il segnale di carica vale 0 o 1. Se NON vale 1, "ricarica"; altrimenti "parti".',
        'Prima confronta segnale_a con 1; poi NOT capovolge il risultato del confronto.',
        'Il NOT logico non è ~, che inverte i bit dell’intero. In Java usa !(segnale_a == 1), non !segnale_a.',
        'if {0}:\n    print("{1}")\nelse:\n    print("{2}")\n',
        (condition('SE · carica non pronta', 'not (segnale_a == 1)', ('segnale_a == 1', 'not (segnale_a == 1)', 'False')),
         command('ALLORA', 'ricarica', ('parti', 'ricarica', 'allarme'), 1), command('ALTRIMENTI', 'parti', ('parti', 'ricarica', 'attendi'), 1)),
        cases(('Segnale spento', {'segnale_a': 0}), ('Segnale acceso', {'segnale_a': 1})),
        {'segnale_a': (0, 1)}, lambda d: ('ricarica',) if d['segnale_a'] == 0 else ('parti',),
        ('0 significa che manca la carica.', 'Nega il confronto completo con parentesi.', 'NOT falso produce vero.')),
    Mission('campo', '18 · Il messaggio mancante', 'Campo vuoto = falso; compilato = vero.', 'Logica e dati', 'if',
        'La stazione aspetta un messaggio. Se campo_a è vero, "registra"; altrimenti "attendi". Il sensore è vero quando testo_a contiene almeno un carattere.',
        'Il sensore campo_a verifica la presenza di testo: vuoto dà falso, almeno un carattere dà vero.',
        'Il testo "0" è contenuto, quindi il campo è pieno. Anche "false" e uno spazio non sono stringhe vuote: presenza e validità sono controlli diversi.',
        'if {0}:\n    print("{1}")\nelse:\n    print("{2}")\n',
        (condition('SE · messaggio presente', 'campo_a', ('not campo_a', 'campo_a', 'True')),
         command('ALLORA', 'registra', ('attendi', 'registra', 'parti'), 1), command('ALTRIMENTI', 'attendi', ('registra', 'apri', 'attendi'), 1)),
        cases(('Nessun testo', {'testo_a': ''}), ('Un messaggio', {'testo_a': 'ORIONE'}), ('Testo zero', {'testo_a': '0'}), ('Parola false', {'testo_a': 'false'}), ('Un solo spazio', {'testo_a': ' '})),
        {'testo_a': ('', 'ORIONE', '0', 'false', ' ')}, lambda d: ('registra',) if d['campo_a'] else ('attendi',),
        ('Conta i caratteri, non interpretare la parola scritta.', 'campo_a espone già la verifica del testo.', 'Solo la stringa senza alcun carattere è vuota.')),
    Mission('campi_and', '19 · La scheda di missione', 'Due campi, entrambi necessari.', 'Logica e dati', 'and',
        'Per registrare una missione servono testo_a e testo_b compilati. Se campo_a AND campo_b, "registra"; altrimenti "attendi".',
        'Prima ogni testo diventa un booleano di presenza. Poi AND richiede entrambi veri.',
        'Un campo compilato non riempie anche l’altro. Il testo "0" conta come compilato; il numero 0 avrebbe un altro significato.',
        'if {0}:\n    print("{1}")\nelse:\n    print("{2}")\n',
        (condition('SE · scheda completa', 'campo_a and campo_b', ('campo_a or campo_b', 'campo_a ^ campo_b', 'campo_a and campo_b')),
         command('ALLORA', 'registra', ('registra', 'attendi', 'parti'), 1), command('ALTRIMENTI', 'attendi', ('registra', 'attendi', 'nega'), 1)),
        cases(('Scheda vuota', {'testo_a': '', 'testo_b': ''}), ('Solo destinazione', {'testo_a': 'LUNA', 'testo_b': ''}), ('Solo nominativo', {'testo_a': '', 'testo_b': 'ADA'}), ('Scheda completa', {'testo_a': 'LUNA', 'testo_b': 'ADA'}), ('Zero è un testo', {'testo_a': '0', 'testo_b': 'ADA'})),
        {'testo_a': ('', 'LUNA', '0', 'false', ' '), 'testo_b': ('', 'ADA', '0', 'false', ' ')}, lambda d: ('registra',) if d['campo_a'] and d['campo_b'] else ('attendi',),
        ('Verifica separatamente i due campi.', 'Unisci i due sensori con AND.', 'Nel banco logico puoi scrivere e cancellare il testo.')),
    Mission('campi_xor', '20 · Una destinazione sola', 'XOR sui campi compilati.', 'Logica e dati', 'xor',
        'La navetta accetta una sola destinazione. Se esattamente uno dei due campi contiene testo, "parti"; se nessuno o entrambi sono compilati, "attendi". Usa XOR.',
        'XOR riceve i due booleani di presenza. La scelta è valida quando sono diversi.',
        'Due campi diversi ma entrambi pieni producono vero/vero: XOR è falso. Qui confronti la presenza, non il contenuto dei testi.',
        'if {0}:\n    print("{1}")\nelse:\n    print("{2}")\n',
        (condition('SE · una sola destinazione', 'campo_a ^ campo_b', ('campo_a ^ campo_b', 'campo_a or campo_b', 'campo_a and campo_b')),
         command('ALLORA', 'parti', ('attendi', 'parti', 'registra'), 1), command('ALTRIMENTI', 'attendi', ('parti', 'attendi', 'nega'), 1)),
        cases(('Nessuna destinazione', {'testo_a': '', 'testo_b': ''}), ('Verso Luna', {'testo_a': 'LUNA', 'testo_b': ''}), ('Verso Marte', {'testo_a': '', 'testo_b': 'MARTE'}), ('Due destinazioni', {'testo_a': 'LUNA', 'testo_b': 'MARTE'}), ('Testo zero', {'testo_a': '0', 'testo_b': ''})),
        {'testo_a': ('', 'LUNA', '0', 'false', ' '), 'testo_b': ('', 'MARTE', '0', 'false', ' ')}, lambda d: ('parti',) if d['campo_a'] != d['campo_b'] else ('attendi',),
        ('Calcola prima se ogni campo è vuoto o pieno.', 'Due testi diversi non bastano: deve essere compilato un solo campo.', 'XOR è vero soltanto per vero/falso o falso/vero.')),
)
BY_KEY = {mission.key: mission for mission in MISSIONS}


@dataclass
class Review:
    success: bool
    passed: int
    total: int
    message: str
    case: object = None
    expected: tuple = ()
    actual: tuple = ()


def contains_operator(tree, operator):
    if not isinstance(tree, tuple) or not tree:
        return False
    return tree[0] == operator or any(contains_operator(child, operator) for child in tree[1:] if isinstance(child, tuple))


def validate(mission, code, language):
    nodes = parse(code, language)
    passed, total, first, reached = 0, 0, None, set()
    for case in mission.all_cases():
        frames = run(nodes, case.data, language)
        reached.update(frame.uid for frame in frames if frame.kind == 'condition')
        expected, actual = mission.rule(case.data), frames[-1].actions
        total += 1
        if actual == expected:
            passed += 1
        elif first is None:
            first = (case, expected, actual)
    if first:
        case, expected, actual = first
        values = ', '.join(f'{key}={value}' for key, value in case.values.items())
        message = f'Con {values}: atteso {describe(expected)}; ottenuto {describe(actual)}. {mission.trap}'
        return Review(False, passed, total, message, case, expected, actual)
    effective = [node for node in nodes if node.kind != 'if' or node.uid in reached]
    valid_structure = structure_ok(effective, mission.target)
    if mission.target == 'nested':
        valid_structure = any(n.kind == 'if' and n.uid in reached and any(c.kind == 'if' and c.uid in reached for c in walk(n.body)) for n in walk(nodes))
    if mission.target == 'chain':
        valid_structure = any(n.kind == 'if' and n.uid in reached and len(n.other) == 1 and n.other[0].kind == 'if' and n.other[0].uid in reached for n in walk(nodes))
    if mission.target in ('and', 'or', 'not', 'xor'):
        valid_structure = any(n.kind == 'if' and n.uid in reached and contains_operator(n.tree, mission.target) for n in walk(nodes))
    if not valid_structure:
        return Review(False, passed, total, 'Le azioni sono corrette, ma usa la struttura richiesta nell’obiettivo e fai in modo che venga raggiunta. Una struttura inutilizzata non completa la missione.')
    return Review(True, passed, total, f'Missione riuscita: {total} casi verificati, compresi i confini. La struttura richiesta è stata usata.')
