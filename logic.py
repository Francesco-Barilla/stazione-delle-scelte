from native_io import output_statement
"""Boolean laboratory: normalize inputs before applying logical operators."""
OPERATORS = ('AND', 'OR', 'NOT', 'XOR')
REPRESENTATIONS = ('Booleani', '0/1', 'Campi')


def present(value):
    """Presence means at least one character, including whitespace; not validity."""
    if not isinstance(value, str):
        raise TypeError('Il campo deve essere un testo.')
    return len(value) > 0


def normalize(value, representation):
    if representation == 'Campi':
        return present(value)
    if representation == 'Booleani':
        if type(value) is not bool:
            raise ValueError('Qui servono True o False.')
        return value
    if representation == '0/1':
        if type(value) is not int or value not in (0, 1):
            raise ValueError('Qui i soli valori ammessi sono 0 e 1.')
        return value == 1
    raise ValueError('Rappresentazione sconosciuta.')


def compute(operator, a, b=False):
    if type(a) is not bool or type(b) is not bool:
        raise ValueError('Normalizza gli ingressi in booleani prima dell’operazione.')
    if operator == 'AND':
        return a and b
    if operator == 'OR':
        return a or b
    if operator == 'NOT':
        return not a
    if operator == 'XOR':
        return a != b
    raise ValueError('Operatore sconosciuto.')


def truth_table(operator):
    return [(a, b, compute(operator, a, b)) for a, b in ((False, False), (True, False))] if operator == 'NOT' else [(a, b, compute(operator, a, b)) for a, b in ((False, False), (False, True), (True, False), (True, True))]


def expression(operator, language):
    if operator == 'NOT':
        return 'not a' if language == 'Python' else '!a'
    symbol = {'AND': 'and' if language == 'Python' else '&&',
              'OR': 'or' if language == 'Python' else '||', 'XOR': '^'}[operator]
    return f'a {symbol} b'


def sample_source(operator, representation, language):
    names = ('a',) if operator == 'NOT' else ('a', 'b')
    setup = []
    for name in names:
        if representation == 'Campi':
            rhs = {'Python': f'bool(testo_{name})', 'JavaScript': f'testo_{name}.length > 0',
                   'C': f"testo_{name}[0] != '\\0'", 'Java': f'!testo_{name}.isEmpty()'}[language]
        elif representation == '0/1':
            rhs = f'segnale_{name} == 1'
        else:
            rhs = f'ingresso_{name}'
        prefix = {'Python': '', 'JavaScript': 'const ', 'C': 'bool ', 'Java': 'boolean '}[language]
        setup.append(prefix + name + ' = ' + rhs + ('' if language == 'Python' else ';'))
    exp = expression(operator, language)
    if language == 'Python':
        setup += [f'if {exp}:', '    ' + output_statement('apri', language), 'else:', '    ' + output_statement('attendi', language)]
    else:
        setup += [f'if ({exp}) {{', '    ' + output_statement('apri', language), '} else {', '    ' + output_statement('attendi', language), '}']
    return '\n'.join(setup) + '\n'


EXPLANATIONS = {
    'AND': 'Vero soltanto se entrambi gli ingressi sono veri. Il caso 1 AND 0 è falso. Dopo la normalizzazione, gli operatori and / && possono saltare la seconda valutazione se la prima è falsa.',
    'OR': 'Vero con almeno un ingresso vero, anche quando sono veri entrambi. 1 OR 1 è vero: OR è inclusivo. Dopo la normalizzazione, or / || possono saltare la seconda valutazione se la prima è vera.',
    'NOT': 'Inverte un solo valore: NOT 0 = 1; NOT 1 = 0. Il secondo ingresso non partecipa. Non significa “negativo”: è la negazione di un valore logico.',
    'XOR': 'Vero con esattamente un ingresso vero: 0 XOR 1 = 1 e 1 XOR 0 = 1. Con ingressi uguali è falso: 1 XOR 1 = 0. Qui ^ usa ingressi booleani normalizzati e valuta entrambi, senza cortocircuito.',
}

NOTES = '''DAL DATO AL VALORE LOGICO
Booleani: false / False equivale a 0; true / True equivale a 1.
Ingressi binari: i soli numeri ammessi in questo banco sono 0 e 1. Il confronto segnale == 1 produce un booleano valido anche in Java.
Campi: nessun carattere significa falso; almeno un carattere significa vero. Anche il testo "0", il testo "false" e un solo spazio sono contenuti. Questa regola verifica la presenza, non la validità del dato. Non si eliminano automaticamente gli spazi.

LA PRESENZA È UNA REGOLA ESPLICITA
Nel banco puoi compilare o svuotare i campi. Nelle missioni i sensori campo_a e campo_b espongono già il risultato di questa verifica. I testi sono sempre disponibili: non si simulano null o puntatori nulli.
In Python bool(testo) verifica una stringa vuota; in JavaScript si può usare testo.length > 0; in Java !testo.isEmpty(); in C, per una stringa valida terminata da zero, testo[0] != '\\0'. Una stringa C vuota non va verificata usando il puntatore come se fosse il contenuto.

LOGICA E OPERATORI SUI BIT
XOR logico significa “esattamente uno vero”. ^ su interi esegue invece XOR bit per bit. Con i soli bit 0/1 i risultati coincidono. Con altri interi no: 2 ^ 1 vale 3, non un booleano. Per lo XOR logico normalizza prima gli ingressi. In Python e Java ^ su due booleani produce un booleano; in C e JavaScript produce un numero 0/1. In Java if richiede il risultato booleano.
~ non è il NOT logico: inverte i bit di un intero. Per negare una condizione usa not in Python e ! negli altri linguaggi.

CODICE MOSTRATO NEL BANCO
Il codice illustra anche la preparazione dei dati nel linguaggio completo. In C si assume incluso stdbool.h; i testi C sono stringhe valide. Nell’editor delle missioni i dati sono già predisposti e restano di sola lettura: usa direttamente campo_a, campo_b e i segnali.
'''
