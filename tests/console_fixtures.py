"""Language-neutral output slots for existing control-flow test fixtures.

@apri means insert the native print statement without changing punctuation,
conditions, nesting or source-line numbers. This is test data, not app syntax.
"""
import re
from engine import parse as parse_program
from missions import validate as validate_program
from native_io import output_statement


def console_source(source, language):
    return re.sub(r'@(\w+)', lambda m: output_statement(m[1], language).rstrip(';'), source)


def parse(source, language):
    return parse_program(console_source(source, language), language)


def validate(mission, source, language):
    return validate_program(mission, console_source(source, language), language)
