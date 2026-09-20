"""Copyable programs with standard input; the game editor supplies these data."""
import re
from engine import FIELDS


def input_fields(code):
    # Ignore strings and comments: only variables actually used in conditions.
    source = re.sub(r'"(?:\\.|[^"\\])*"|\x27(?:\\.|[^\x27\\])*\x27|//[^\n]*|#[^\n]*', '', code)
    return [name for name in FIELDS if re.search(r'\b' + name + r'\b', source)]


def input_block(code, language):
    rows = []
    for name in input_fields(code):
        boolean = FIELDS[name] is bool
        note = name + (': inserisci 0 (falso) o 1 (vero)' if boolean else ': inserisci un numero intero')
        rows.append(('# ' if language == 'Python' else '// ') + note)
        if language == 'Python':
            rows.append(name + ' = int(input())' + (' != 0' if boolean else ''))
        elif language == 'JavaScript':
            rows.append('const ' + name + ' = Number(prompt())' + (' !== 0' if boolean else '') + ';')
        elif language == 'Java':
            rows.append(('boolean ' if boolean else 'int ') + name + ' = Integer.parseInt(input.nextLine())' + (' != 0' if boolean else '') + ';')
        else:
            target = 'valore_' + name if boolean else name
            rows += ['int ' + target + ' = 0;', 'scanf("%d", &' + target + ');']
            if boolean:
                rows.append('bool ' + name + ' = ' + target + ' != 0;')
    return '\n'.join(rows)


def wrap_program(body, language):
    if language == 'C':
        return '#include <stdio.h>\n#include <stdbool.h>\n\nint main(void) {\n' + '\n'.join('    '+line for line in body.splitlines()) + '\n    return 0;\n}\n'
    if language == 'Java':
        return 'import java.util.Scanner;\n\npublic class Main {\n    public static void main(String[] args) {\n        Scanner input = new Scanner(System.in);\n' + '\n'.join('        '+line for line in body.splitlines()) + '\n    }\n}\n'
    return ('// JavaScript nel browser: prompt legge un dato alla volta.\n' if language == 'JavaScript' else '') + body + '\n'


def context_code(code, language):
    return wrap_program(input_block(code, language) + '\n\n' + code, language)
