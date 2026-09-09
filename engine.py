"""Small, bounded interpreter for conditional classroom programs.

No student code is executed by Python or another host runtime. Python syntax
is read with ast; the three brace languages have their own precedence parser.
"""
import ast
from dataclasses import dataclass, field
import re

LANGUAGES = ('Python', 'JavaScript', 'C', 'Java')
COMMANDS = {
    'ricarica': 'Ricarica', 'parti': 'Parti', 'apri': 'Apri portello',
    'nega': 'Nega accesso', 'proteggi': 'Proteggi carico', 'controlla': 'Ispeziona',
    'soccorso': 'Invia soccorso', 'corsia_rapida': 'Corsia rapida',
    'corsia_normale': 'Corsia normale', 'allarme': 'Attiva allarme',
    'carica': 'Imbarca carico', 'accompagna': 'Richiedi guida',
    'attendi': 'Attendi', 'registra': 'Registra passaggio',
}
FIELDS = {'batteria': int, 'temperatura': int, 'peso': int, 'livello': int,
          'badge': bool, 'autorizzato': bool, 'urgente': bool, 'fragile': bool, 'fumo': bool,
          'segnale_a': int, 'segnale_b': int, 'campo_a': bool, 'campo_b': bool}
MAX_CODE, MAX_LINES, MAX_DEPTH, MAX_NODES = 12000, 180, 10, 300


class CodeError(Exception):
    def __init__(self, message, line=1):
        super().__init__(message)
        self.line = line


@dataclass
class Node:
    kind: str
    value: str = ''
    body: list = field(default_factory=list)
    other: list = field(default_factory=list)
    line: int = 1
    else_line: int = 1
    chain: bool = False
    tree: object = None
    uid: int = 0


def action(name):
    return Node('action', name)


def branch(condition, yes, no=(), chain=False):
    return Node('if', condition, list(yes), list(no), chain=chain)


def walk(nodes):
    for node in nodes:
        yield node
        yield from walk(node.body)
        yield from walk(node.other)


def py_expr(item, line):
    if isinstance(item, ast.Constant) and type(item.value) in (bool, int):
        if type(item.value) is int and abs(item.value) > 10000:
            raise CodeError('Usa interi tra -10000 e 10000.', line)
        return ('literal', item.value)
    if isinstance(item, ast.Name) and item.id in FIELDS:
        return ('name', item.id)
    if isinstance(item, ast.UnaryOp) and isinstance(item.op, (ast.Not, ast.USub, ast.UAdd)):
        return ('not' if isinstance(item.op, ast.Not) else 'neg' if isinstance(item.op, ast.USub) else 'pos', py_expr(item.operand, line))
    if isinstance(item, ast.BoolOp):
        op = 'and' if isinstance(item.op, ast.And) else 'or'
        result = py_expr(item.values[0], line)
        for child in item.values[1:]:
            result = (op, result, py_expr(child, line))
        return result
    if isinstance(item, ast.BinOp) and isinstance(item.op, ast.BitXor):
        return ('xor', py_expr(item.left, line), py_expr(item.right, line))
    if isinstance(item, ast.Compare):
        operators = {ast.Lt: '<', ast.LtE: '<=', ast.Gt: '>', ast.GtE: '>=', ast.Eq: '==', ast.NotEq: '!='}
        if all(type(op) in operators for op in item.ops):
            return ('compare', py_expr(item.left, line),
                    tuple((operators[type(op)], py_expr(child, line)) for op, child in zip(item.ops, item.comparators)))
    raise CodeError('Nelle condizioni usa i dati della missione, interi, confronti e operatori logici. Funzioni, stringhe e altri costrutti non sono previsti qui.', line)


TOKEN = re.compile(r'\s+|//[^\n]*|/\*[\s\S]*?\*/|===|!==|==|!=|<=|>=|&&|\|\||[A-Za-z_][A-Za-z_0-9]*|\d+|[{}();<>!+\-=^]')


def tokenize(code):
    result, pos, line = [], 0, 1
    for match in TOKEN.finditer(code):
        if match.start() != pos:
            raise CodeError('Simbolo non previsto. Usa i comandi e gli operatori della scheda Linguaggi.', line)
        word = match.group()
        if not word.isspace() and not word.startswith(('//', '/*')):
            result.append((word, line))
        line += word.count('\n')
        pos = match.end()
    if pos != len(code):
        raise CodeError('Simbolo non previsto o commento non chiuso.', line)
    return result


class ExpressionParser:
    precedence = {'||': 1, '&&': 2, '^': 3, '==': 4, '!=': 4, '===': 4, '!==': 4,
                  '<': 5, '<=': 5, '>': 5, '>=': 5}

    def __init__(self, tokens, language, line):
        self.tokens, self.language, self.line, self.pos = tokens, language, line, 0

    def peek(self):
        return self.tokens[self.pos][0] if self.pos < len(self.tokens) else ''

    def take(self):
        if not self.peek():
            raise CodeError('La condizione è incompleta.', self.line)
        result = self.peek()
        self.pos += 1
        return result

    def read(self, minimum=0, depth=0):
        if depth > 40:
            raise CodeError('La condizione è troppo complessa.', self.line)
        word = self.take()
        if word == '(':
            left = self.read(depth=depth + 1)
            if self.take() != ')':
                raise CodeError('Manca la parentesi ) nella condizione.', self.line)
        elif word in ('!', '-', '+'):
            left = ({'!': 'not', '-': 'neg', '+': 'pos'}[word], self.read(6, depth + 1))
        elif word in ('true', 'false'):
            left = ('literal', word == 'true')
        elif word.isdigit() and int(word) <= 10000:
            left = ('literal', int(word))
        elif word in FIELDS:
            left = ('name', word)
        else:
            raise CodeError('Usa un dato della missione o un confronto: per esempio batteria >= 30.', self.line)
        while self.peek() in self.precedence and self.precedence[self.peek()] >= minimum:
            op = self.take()
            if op in ('===', '!==') and self.language != 'JavaScript':
                raise CodeError('=== e !== sono operatori di JavaScript. Qui usa == oppure !=.', self.line)
            right = self.read(self.precedence[op] + 1, depth + 1)
            left = ({'&&': 'and', '||': 'or', '^': 'xor'}.get(op, op), left, right)
        return left


def parse_expression(value, language='Python', line=1):
    if len(value) > 1000:
        raise CodeError('Accorcia la condizione: massimo 1000 caratteri.', line)
    if re.search(r'(?<![<>=!])=(?!=)', value):
        raise CodeError('= assegna; == confronta. In questo laboratorio i dati sono di sola lettura. In C e JavaScript un’assegnazione può apparire in una condizione, ma non confronta i valori.', line)
    try:
        if language == 'Python':
            return py_expr(ast.parse(value, mode='eval').body, line)
        parser = ExpressionParser(tokenize(value), language, line)
        tree = parser.read()
        if parser.peek():
            raise CodeError('Controlla la condizione: usa &&, || e ! in questo linguaggio.', line)
        return tree
    except (SyntaxError, ValueError, RecursionError):
        raise CodeError('Condizione incompleta: controlla parentesi e operatori logici.', line)


def expr_type(tree, language, line):
    op = tree[0]
    if op == 'literal':
        return type(tree[1])
    if op == 'name':
        return FIELDS[tree[1]]
    if op in ('not', 'neg', 'pos'):
        child = expr_type(tree[1], language, line)
        if language == 'Java' and ((op == 'not' and child is not bool) or (op != 'not' and child is not int)):
            raise CodeError('In Java ! richiede un booleano; + e - richiedono un numero.', line)
        return bool if op == 'not' else int
    if op == 'compare':
        expr_type(tree[1], language, line)
        for _, child in tree[2]:
            expr_type(child, language, line)
        return bool
    left, right = expr_type(tree[1], language, line), expr_type(tree[2], language, line)
    if op == 'xor':
        if language == 'Java' and left is not right:
            raise CodeError('In Java ^ richiede due booleani oppure due interi. Converte i bit con segnale_a == 1 e segnale_b == 1.', line)
        return bool if language in ('Python', 'Java') and left is bool and right is bool else int
    if language == 'Java':
        if op in ('and', 'or') and (left is not bool or right is not bool):
            raise CodeError('In Java && e || richiedono condizioni booleane, non numeri.', line)
        if op in ('<', '<=', '>', '>=') and (left is not int or right is not int):
            raise CodeError('In Java <, <=, > e >= confrontano numeri. Ripeti il nome del dato: peso >= 10 && peso <= 20.', line)
        if op in ('==', '!=') and left is not right:
            raise CodeError('In Java non puoi confrontare un booleano con un intero.', line)
    return bool


def compare(op, left, right):
    if op in ('===', '!=='):
        same = type(left) is type(right) and left == right
        return same if op == '===' else not same
    return {'<': lambda: left < right, '<=': lambda: left <= right,
            '>': lambda: left > right, '>=': lambda: left >= right,
            '==': lambda: left == right, '!=': lambda: left != right}[op]()


def evaluate(tree, data, language, notes):
    op = tree[0]
    if op == 'literal':
        return tree[1]
    if op == 'name':
        return data[tree[1]]
    if op in ('not', 'neg', 'pos'):
        value = evaluate(tree[1], data, language, notes)
        return not value if op == 'not' else -value if op == 'neg' else +value
    left = evaluate(tree[1], data, language, notes)
    if op == 'xor':
        right = evaluate(tree[2], data, language, notes)
        notes.append('XOR valuta entrambi gli ingressi: è vero con esattamente uno vero (per booleani o bit 0/1).')
        return int(left) ^ int(right) if language in ('C', 'JavaScript') else left ^ right
    if op in ('and', 'or'):
        if (op == 'and' and not left) or (op == 'or' and left):
            notes.append('Cortocircuito: la parte destra non viene valutata.')
            return left if language in ('Python', 'JavaScript') else bool(left)
        right = evaluate(tree[2], data, language, notes)
        return right if language in ('Python', 'JavaScript') else bool(right)
    if op == 'compare':
        for symbol, child in tree[2]:
            right = evaluate(child, data, language, notes)
            if not compare(symbol, left, right):
                return False
            left = right
        return True
    return compare(op, left, evaluate(tree[2], data, language, notes))


def expr_source(tree, language):
    op = tree[0]
    if op == 'literal':
        if type(tree[1]) is bool:
            return str(tree[1]) if language == 'Python' else str(tree[1]).lower()
        return str(tree[1])
    if op == 'name':
        return tree[1]
    if op in ('not', 'neg', 'pos'):
        prefix = ('not ' if language == 'Python' else '!') if op == 'not' else '-' if op == 'neg' else '+'
        return prefix + '(' + expr_source(tree[1], language) + ')'
    if op == 'compare':
        parts, left = [], tree[1]
        for symbol, child in tree[2]:
            parts.append(f'{expr_source(left, language)} {symbol} {expr_source(child, language)}')
            left = child
        return parts[0] if len(parts) == 1 else '(' + (') and (' if language == 'Python' else ') && (').join(parts) + ')'
    symbol = ('and' if language == 'Python' else '&&') if op == 'and' else ('or' if language == 'Python' else '||') if op == 'or' else op
    if op == 'xor':
        symbol = '^'
    if language == 'Python' and op in ('===', '!=='):
        symbol = '==' if op == '===' else '!='
    return f'({expr_source(tree[1], language)} {symbol} {expr_source(tree[2], language)})'


def format_expression(value, language):
    return expr_source(parse_expression(value), language)


def generate(nodes, language, level=0):
    result = []
    def emit(items, depth):
        indent = '    ' * depth
        for node in items:
            if node.kind == 'action':
                result.append(indent + node.value + '()' + ('' if language == 'Python' else ';'))
            elif node.kind == 'pass':
                result.append(indent + ('pass' if language == 'Python' else ';'))
            else:
                keyword = 'elif' if language == 'Python' and node.chain else 'else if' if node.chain else 'if'
                value = expr_source(node.tree, language) if node.tree else format_expression(node.value, language)
                result.append(indent + (f'{keyword} {value}:' if language == 'Python' else f'{keyword} ({value}) {{'))
                emit(node.body or [Node('pass')], depth + 1)
                if language != 'Python':
                    result.append(indent + '}')
                if node.other:
                    if len(node.other) == 1 and node.other[0].kind == 'if' and node.other[0].chain:
                        emit(node.other, depth)
                    else:
                        result.append(indent + ('else:' if language == 'Python' else 'else {'))
                        emit(node.other, depth + 1)
                        if language != 'Python':
                            result.append(indent + '}')
    emit(nodes, level)
    return '\n'.join(result) + '\n'


def python_nodes(items, source, depth=0):
    if depth > MAX_DEPTH:
        raise CodeError('Troppi livelli annidati: massimo 10.')
    result = []
    for item in items:
        if isinstance(item, ast.If):
            node = Node('if', ast.unparse(item.test), python_nodes(item.body, source, depth + 1),
                        python_nodes(item.orelse, source, depth + 1), item.lineno,
                        item.orelse[0].lineno - 1 if item.orelse else item.lineno,
                        source[item.lineno - 1].lstrip().startswith('elif '))
            result.append(node)
        elif isinstance(item, ast.Expr) and isinstance(item.value, ast.Call) and isinstance(item.value.func, ast.Name) and not item.value.args and not item.value.keywords:
            result.append(Node('action', item.value.func.id, line=item.lineno))
        elif isinstance(item, ast.Pass):
            result.append(Node('pass', line=item.lineno))
        else:
            raise CodeError('Qui scrivi selezioni e azioni della stazione. Dati di sola lettura: cicli, assegnazioni, import e definizioni non fanno parte di questo laboratorio.', item.lineno)
    return result


class ProgramParser:
    def __init__(self, code):
        self.tokens, self.pos = tokenize(code), 0

    def peek(self):
        return self.tokens[self.pos][0] if self.pos < len(self.tokens) else ''

    def line(self):
        return self.tokens[self.pos][1] if self.pos < len(self.tokens) else self.tokens[-1][1] if self.tokens else 1

    def take(self, expected=None):
        word = self.peek()
        if not word or (expected and word != expected):
            raise CodeError(f'Manca «{expected or "un’istruzione"}» oppure il blocco è incompleto.', self.line())
        self.pos += 1
        return word

    def statement(self, depth=0):
        if depth > MAX_DEPTH:
            raise CodeError('Troppi livelli annidati: massimo 10.', self.line())
        line = self.line()
        word = self.take()
        if word == '{':
            items = []
            while self.peek() != '}':
                items.extend(self.statement(depth))
            self.take('}')
            return items
        if word == ';':
            return [Node('pass', line=line)]
        if word == 'if':
            self.take('(')
            parts, parentheses = [], 1
            while parentheses:
                part = self.take()
                parentheses += (part == '(') - (part == ')')
                if parentheses:
                    parts.append(part)
            body = self.statement(depth + 1)
            node = Node('if', ' '.join(parts), body, line=line)
            if self.peek() == 'else':
                node.else_line = self.line()
                self.take('else')
                chain = self.peek() == 'if'
                node.other = self.statement(depth + 1)
                if chain:
                    node.other[0].chain = True
            return [node]
        if word in COMMANDS:
            self.take('(')
            self.take(')')
            self.take(';')
            return [Node('action', word, line=line)]
        raise CodeError('Scrivi if, else if, else e i comandi della stazione. Le azioni vogliono () e ;. I dati non possono essere modificati qui.', line)


def parse(code, language):
    if language not in LANGUAGES:
        raise CodeError('Linguaggio non riconosciuto.')
    if len(code) > MAX_CODE or len(code.splitlines()) > MAX_LINES:
        raise CodeError('Programma troppo lungo: massimo 12000 caratteri e 180 righe.')
    if '???' in code:
        raise CodeError('Completa i punti segnati con ??? prima di eseguire.', code[:code.index('???')].count('\n') + 1)
    try:
        if language == 'Python':
            nodes = python_nodes(ast.parse(code).body, code.splitlines())
        else:
            parser, nodes = ProgramParser(code), []
            while parser.peek():
                nodes.extend(parser.statement())
        all_nodes = list(walk(nodes))
        if len(all_nodes) > MAX_NODES:
            raise CodeError('Troppe istruzioni: semplifica il programma.')
        for uid, node in enumerate(all_nodes, 1):
            node.uid = uid
            if node.kind == 'action' and node.value not in COMMANDS:
                raise CodeError('Comando sconosciuto: apri la scheda Comandi.', node.line)
            if node.kind == 'if':
                node.tree = parse_expression(node.value, language, node.line)
                kind = expr_type(node.tree, language, node.line)
                if language == 'Java' and kind is not bool:
                    raise CodeError('In Java if richiede un booleano: scrivi per esempio batteria != 0. Un numero da solo non è una condizione valida.', node.line)
        return nodes
    except (SyntaxError, IndentationError) as error:
        raise CodeError('Controlla rientri, due punti e parentesi. In Python scrivi elif, non else if. Per confrontare usa ==, non =.', getattr(error, 'lineno', 1) or 1)
    except (ValueError, RecursionError):
        raise CodeError('Programma non leggibile o troppo complesso.')


@dataclass(frozen=True)
class Frame:
    line: int
    kind: str
    title: str
    message: str
    actions: tuple
    statuses: tuple
    depth: int = 0
    uid: int = 0


def run(nodes, data, language):
    frames, actions, statuses = [], [], {}
    def frame(line, kind, title, message, depth=0, uid=0):
        frames.append(Frame(line, kind, title, message, tuple(actions), tuple(statuses.values()), depth, uid))
    def skip(items, reason):
        for child in walk(items):
            if child.kind == 'if':
                statuses[child.uid] = (child.line, 'NON VALUTATA')
    def execute(items, depth=0):
        for node in items:
            if node.kind == 'action':
                actions.append(node.value)
                frame(node.line, 'action', COMMANDS[node.value], 'Esegue questa azione una volta, poi prosegue.', depth)
            elif node.kind == 'pass':
                frame(node.line, 'pass', 'Nessuna azione', 'Questa istruzione è vuota; il programma prosegue.', depth)
            else:
                notes = []
                value = bool(evaluate(node.tree or parse_expression(node.value, language, node.line), data, language, notes))
                status = 'VERO' if value else 'FALSO'
                statuses[node.uid] = (node.line, status)
                skip(node.other if value else node.body, 'ramo escluso')
                def substitute(match):
                    name = match.group()
                    if name not in data:
                        return name
                    raw = data[name]
                    return str(raw).lower() if type(raw) is bool and language != 'Python' else str(raw)
                numeric = re.sub(r'\b[A-Za-z_][A-Za-z_0-9]*\b', substitute, node.value)
                message = numeric + ' → ' + status + '. ' + ('Entra nel ramo vero.' if value else 'Salta il ramo vero e cerca l’alternativa.')
                if value and node.other:
                    message += ' Le alternative di questa selezione non vengono valutate.'
                frame(node.line, 'condition', status, message + (' ' + ' '.join(notes) if notes else ''), depth, node.uid)
                if value:
                    execute(node.body, depth + 1)
                elif node.other:
                    if not (len(node.other) == 1 and node.other[0].chain):
                        frame(node.else_line, 'else', 'ALTRIMENTI', 'La condizione del suo if è falsa. Else non ha una nuova condizione.', depth)
                    execute(node.other, depth if node.other[0].chain else depth + 1)
    frame(0, 'start', 'Leggi i dati', 'Ogni caso è una nuova esecuzione: la selezione non è un ciclo.')
    execute(nodes)
    frame(0, 'finished', 'Fine del programma', 'Azioni eseguite: ' + describe(actions) + '.')
    return frames


def describe(actions):
    return ' → '.join(COMMANDS[x] for x in actions) if actions else 'nessuna azione'


def structure_ok(nodes, target):
    conditions = [n for n in walk(nodes) if n.kind == 'if']
    if not conditions:
        return False
    if target == 'independent':
        return len([n for n in nodes if n.kind == 'if']) >= 2
    if target == 'chain':
        return any(len(n.other) == 1 and n.other[0].kind == 'if' for n in conditions)
    if target == 'nested':
        return any(any(child.kind == 'if' for child in walk(n.body)) for n in conditions)
    if target == 'else':
        return any(n.other for n in conditions)
    return True
