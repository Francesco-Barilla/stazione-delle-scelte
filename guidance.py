"""Explicit learner tasks, separate from sensor values and computer actions."""
from dataclasses import dataclass
import re
from native_io import output_statement, output_explanation
from engine import COMMANDS, FIELDS, format_expression, generate, parse, placeholder_index

RULES = {
    'ricarica': ('Batteria sotto 30: "ricarica".', 'Da 30 in su: nessuna azione.', 'Usa un if senza else.'),
    'portello': ('Badge vero: "apri".', 'Badge falso: "nega".', 'Scegli un solo ramo con if/else.'),
    'soglia': ('Batteria da 30 in su: "parti".', 'Batteria sotto 30: "ricarica".', 'Il valore 30 deve far partire il drone.'),
    'indipendenti': ('Prima: se batteria < 30, "ricarica".', 'Poi: se fragile è vero, "proteggi".', 'Usa due if: possono servire due azioni.'),
    'catena': ('Sotto 20: "ricarica".', 'Da 20 a meno di 60: "controlla".', 'Da 60 in su: "parti". Una sola scelta.'),
    'priorita': ('Urgente: "soccorso", anche con badge.', 'Solo se non urgente, con badge: "corsia_rapida".', 'Negli altri casi: "corsia_normale".'),
    'and': ('Badge e autorizzato entrambi veri: "apri".', 'In tutti gli altri casi: "nega".', 'Usa AND: un solo permesso non basta.'),
    'or': ('Temperatura da 70 in su o fumo: "allarme".', 'Senza nessun pericolo: "parti".', 'Usa OR: due pericoli danno un solo allarme.'),
    'intervallo': ('Peso da 10 a 20 compresi: "carica".', 'Fuori da questi limiti: "controlla".', 'Unisci i due confronti con AND.'),
    'annidato': ('Senza badge: "nega".', 'Con badge, livello da 2 in su: "apri".', 'Con badge, livello sotto 2: "accompagna".'),
    'soccorso': ('Urgente: da 30 "soccorso", sotto 30 "ricarica".', 'Non urgente: da 30 "parti", sotto 30 "attendi".', 'Usa un if dentro ciascun ramo esterno.'),
    'turno': ('Senza badge: "nega".', 'Con badge: scegli secondo le priorità in alto.', 'Dopo la scelta: "registra" sempre, una volta.'),
    'not': ('Autorizzato falso: "nega".', 'Autorizzato vero: "apri".', 'Usa NOT per capovolgere il permesso.'),
    'bit_and': ('Due segnali a 1: "parti".', 'Se almeno uno è 0: "attendi".', 'Usa AND fra due confronti con 1.'),
    'bit_or': ('Almeno un segnale a 1: "allarme".', 'Due segnali a 0: "parti".', 'Usa OR: anche 1 e 1 richiede allarme.'),
    'xor': ('Un solo permesso vero: "apri".', 'Due veri o due falsi: "attendi".', 'Usa XOR (^): richiede valori diversi.'),
    'bit_not': ('Segnale a 0: "ricarica".', 'Segnale a 1: "parti".', 'Usa NOT sul confronto segnale_a == 1.'),
    'campo': ('Testo presente: "registra".', 'Zero caratteri: "attendi".', 'Nel codice controlla il sensore campo_a.'),
    'campi_and': ('Due campi compilati: "registra".', 'Almeno un campo vuoto: "attendi".', 'Usa AND fra campo_a e campo_b.'),
    'campi_xor': ('Un solo campo compilato: "parti".', 'Due pieni o due vuoti: "attendi".', 'Usa XOR fra campo_a e campo_b.'),
}

STRUCTURES = {
    'if': 'Usa un if per decidere se eseguire un’azione.',
    'else': 'Usa if/else: una strada quando è vero, l’altra quando è falso.',
    'chain': 'Usa una catena: if, poi elif/else if, infine else. Vince il primo ramo vero.',
    'independent': 'Usa due if allo stesso livello: il secondo controllo avviene comunque.',
    'nested': 'Metti il controllo interno dentro il ramo del controllo esterno.',
    'and': 'Nella condizione usa AND: devono essere vere entrambe le parti.',
    'or': 'Nella condizione usa OR: basta almeno una parte vera.',
    'not': 'Nella condizione usa NOT: inverte vero e falso.',
    'xor': 'Nella condizione usa XOR (^): esattamente una parte vera.',
}


@dataclass(frozen=True)
class Gap:
    start: int
    end: int
    line: int
    kind: str


def first_gap(code, language):
    index = placeholder_index(code, language)
    if index < 0:
        return None
    left = code[code.rfind('\n', 0, index) + 1:index]
    kind = 'condition' if re.match(r'\s*(if|elif|else\s+if)\b', left) else 'action' if not left.strip() else 'fragment'
    return Gap(index, index + 3, code[:index].count('\n') + 1, kind)


def meaningful_code(code):
    return '\n'.join(line for line in code.splitlines() if line.strip() and not line.lstrip().startswith(('#', '//'))).strip()


def objective_for(mission, language):
    return mission.objective.replace('if/elif/else', 'if/elif/else' if language == 'Python' else 'if/else if/else')


def writing_issue(code, language):
    if not meaningful_code(code):
        return 'La zona di scrittura è vuota. Premi Scrivi qui e inserisci una regola con if e le azioni richieste.'
    gap = first_gap(code, language)
    if gap:
        noun = 'la condizione' if gap.kind == 'condition' else 'l’azione' if gap.kind == 'action' else 'una parte di codice'
        return f'Alla riga {gap.line} manca {noun}. Premi Completa i ??? e scrivi nella selezione.'
    if meaningful_code(code).rstrip(';') in ('0', '1', 'true', 'false', 'True', 'False'):
        return 'Hai scritto un valore. Qui serve la regola con if, la condizione e le azioni per i diversi casi.'
    return ''


def writing_task(mission, code, language):
    gap = first_gap(code, language)
    if gap and gap.kind == 'condition':
        return 'Scrivi la condizione: il controllo che può essere vero o falso.', 'Sostituisci solo ???. Lascia ' + ('if e i due punti già presenti.' if language == 'Python' else 'if, parentesi e graffe già presenti.')
    if gap and gap.kind == 'action':
        return 'Scrivi l’istruzione di stampa, per esempio ' + output_statement('apri', language).rstrip(';') + '.', 'Sostituisci solo ???. Mantieni il rientro' + (' e il ; già presente.' if language != 'Python' else ' già presente.')
    if gap:
        return 'Completa soltanto la parte segnata con ???.', 'Premi Completa i ??? per selezionarla, poi usa la tastiera.'
    if not meaningful_code(code):
        return 'Scrivi una regola che scelga le azioni in base ai sensori.', 'Premi Scrivi qui. I dati sono già forniti dal gioco: usa i loro nomi nelle condizioni.'
    return 'Modifica la tua regola, poi premi Controlla il mio codice.', 'Scrivi qui porta il cursore in fondo alla bozza. Puoi anche cliccare una riga da correggere.'


def syntax_example(mission, language):
    """Valid examples of the needed structure, using different conditions."""
    expression = {'and': 'urgente and fragile', 'or': 'urgente or fragile',
                  'not': 'not fragile', 'xor': 'urgente ^ fragile'}.get(mission.target, 'batteria < 40')
    source = f'if {expression}:\n    print("controlla")\n'
    if mission.target == 'chain':
        source += 'elif batteria < 80:\n    print("attendi")\nelse:\n    print("parti")\n'
    elif mission.target == 'independent':
        source += 'if fragile:\n    print("proteggi")\n'
    elif mission.target == 'nested':
        source = 'if badge:\n    if fragile:\n        print("controlla")\n    else:\n        print("parti")\nelse:\n    print("attendi")\n'
    elif mission.target != 'if':
        source += 'else:\n    print("parti")\n'
    return generate(parse(source, 'Python'), language)


def inline_example(mission, code, language):
    gap = first_gap(code, language)
    if gap and gap.kind == 'action':
        return 'Esempio di stampa: testo tra virgolette; non aggiungere if.', [output_statement('controlla', language).rstrip(';')]
    expression = {'and': 'urgente and fragile', 'or': 'urgente or fragile',
                  'not': 'not fragile', 'xor': 'urgente ^ fragile'}.get(mission.target, 'batteria < 40')
    if gap:
        return 'Esempio di condizione: adatta dati e confronto alla tua missione.', [format_expression(expression, language)]
    return 'Prime due righe di esempio. Cosa devo scrivere? mostra la struttura completa.', syntax_example(mission, language).splitlines()[:2]


def mission_brief(mission, language, code, blocks=False):
    title, task = writing_task(mission, code, language)
    sections = [('COSA FARE\nFai clic sui blocchi e scegli dal menu. Prossimo blocco vuoto ti porta alla scelta mancante. In questo livello scegli con il mouse.' if blocks else 'COSA SCRIVERE\n' + title + '\n' + task),
                'LA REGOLA DELLA MISSIONE\n' + objective_for(mission, language),
                'LA STRUTTURA DA USARE\n' + STRUCTURES[mission.target].replace('elif/else if', 'elif' if language == 'Python' else 'else if'),
                'COME SI SCRIVE IN ' + language.upper() + '\nQuesto esempio mostra la forma. Adatta dati, soglie e azioni alla consegna.\n\n' + syntax_example(mission, language)]
    descriptions = []
    for name in mission.fields:
        if name.startswith('testo_'):
            sensor = name.replace('testo_', 'campo_')
            descriptions.append(f'{sensor}: vero se {name} contiene almeno un carattere. Vuoto = falso; "0", "false" e spazio = vero.')
        else:
            descriptions.append(name + ': ' + ('vero/falso' if FIELDS[name] is bool else 'intero, solo 0 o 1' if name.startswith('segnale_') else 'numero intero'))
    sections.append('DATI GIÀ FORNITI DAL GIOCO\nUsa questi nomi nelle condizioni. I valori cambiano da un caso all’altro.\n' + '\n'.join(descriptions))
    actions = sorted({slot.answer for slot in mission.slots if slot.kind == 'action'})
    sections.append('AZIONI RICHIESTE IN QUESTA MISSIONE\n' + '\n'.join(output_statement(name, language) + ' = ' + COMMANDS[name] for name in actions))
    logic = [('AND: entrambe vere', 'urgente and fragile'), ('OR: almeno una vera', 'urgente or fragile'),
             ('NOT: capovolgi', 'not fragile'), ('XOR: esattamente una vera', 'urgente ^ fragile'), ('Bit: confronta con 1', 'segnale_a == 1')]
    sections.append('CONFRONTI E LOGICA\n< minore; <= minore o uguale; > maggiore; >= maggiore o uguale; == uguale; != diverso.\n' +
                    '\n'.join(label + ': ' + format_expression(expr, language) for label, expr in logic))
    sections.append('NELLA VISTA A BLOCCHI\nScegli condizioni e azioni dai menu dei blocchi. La struttura è già preparata; gli esempi qui sopra ti aiutano a leggerla.' if blocks else 'MENTRE SCRIVI\n' + ('Invio va a capo. Tab inserisce quattro spazi. Allinea ogni else all’if a cui appartiene.' if language == 'Python' else
                    'Invio va a capo. Le graffe racchiudono i rami; ogni comando termina con ;. Dopo else non si aggiunge una condizione.') +
                    '\n' + output_explanation(language) + ' I dati iniziali sono già preparati; nell’editor scrivi selezioni e stampe.')
    sections.append('CONTROLLA E CORREGGI\n' + ('Controlla i blocchi' if blocks else 'Controlla il mio codice') + ' verifica tutte le combinazioni del dominio. Se una fallisce, confronta richiesto e ottenuto con i dati indicati.\n' +
                    'Guarda l’esecuzione mostra i singoli passi; osservare una traccia non completa la missione.\n\nEQUIVOCO DA EVITARE\n' + mission.trap)
    sections.append('FUNZIONI STANDARD\n' + output_explanation(language) + '\nMostra una soluzione → Programma completo con lettura dei dati mostra input/scanf/prompt/Scanner, dichiarazioni e intestazioni nel linguaggio selezionato. Nell’editor della sfida questi dati sono già forniti.')
    return '\n\n'.join(sections)
