"""Standard console statements used by the visual station and robot."""
import ast
import json
import re

PRINTERS = {'Python': 'print', 'JavaScript': 'console.log', 'C': 'printf', 'Java': 'System.out.println'}
STRING_TOKEN = r'"(?:\\.|[^"\\])*"|\x27(?:\\.|[^\x27\\])*\x27'


def output_statement(message, language):
    literal = json.dumps(message, ensure_ascii=False)
    if language == 'C':
        return 'printf("%s\\n", ' + literal + ');'
    return PRINTERS[language] + '(' + literal + ')' + ('' if language == 'Python' else ';')


def output_message(source, language, example_message='avanza'):
    """Validate the supported standard print signature and return its line."""
    source = re.sub(r'\s*\.\s*', '.', source.strip()).rstrip(';').strip()
    call = re.fullmatch(r'([\w.]+)\s*\((.*)\)', source, re.S)
    example = output_statement(example_message, language)
    if not call or call[1] != PRINTERS[language]:
        raise ValueError('Usa la funzione standard del linguaggio, per esempio ' + example + ' Le vecchie funzioni del gioco non sono più usate.')
    try:
        argument = call[2].strip()
        if language in ('JavaScript', 'Java') and (not re.fullmatch(STRING_TOKEN, argument) or '\\' in argument):
            raise ValueError()
        args = ast.parse('f(' + call[2] + ')', mode='eval').body
        if args.keywords or any(not isinstance(a, ast.Constant) or not isinstance(a.value, str) for a in args.args):
            raise ValueError()
        values = [a.value for a in args.args]
        if language in ('C', 'Java') and any(not ast.get_source_segment('f(' + call[2] + ')', a).startswith('"') for a in args.args):
            raise ValueError()
        if language == 'C':
            if len(values) == 2 and values[0] == '%s\n':
                message = values[1]
            elif len(values) == 1 and values[0].endswith('\n') and '%' not in values[0]:
                message = values[0][:-1]
            else:
                raise ValueError()
        elif len(values) == 1:
            message = values[0]
        else:
            raise ValueError()
        if '\n' in message or '\r' in message:
            raise ValueError()
        return message
    except (SyntaxError, ValueError, TypeError):
        raise ValueError('Scrivi un messaggio per istruzione. Esempio: ' + example + (' %s richiede un testo; \\n va a capo.' if language == 'C' else ' Il testo va tra virgolette.')) from None


def output_explanation(language):
    note = (' In C %s è il segnaposto per il testo, l’argomento dopo la virgola lo riempie e \\n va a capo.' if language == 'C' else '')
    return ('Il programma scrive messaggi nel terminale con ' + PRINTERS[language] + '. Il gioco anima quei messaggi: la funzione standard stampa testo, non muove da sola un robot e non aziona portelli.' + note)
