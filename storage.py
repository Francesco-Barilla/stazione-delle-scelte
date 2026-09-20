"""Validated local progress, separate from the sorting and loop laboratories."""
import json
import classroom
import os
from pathlib import Path
import sys
from engine import LANGUAGES, MAX_CODE
from missions import BY_KEY, DIFFICULTIES


def data_path():
    root = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent
    return root / 'progressi_selezione.json'


def defaults():
    return dict(classroom=classroom.empty(), language='Python', difficulty='Facile', theme='Notte', size=19,
                speed=1, mission='ricarica', completed=[], quizzes=[], drafts={}, blocks={})


def load(path=None):
    state = defaults()
    try:
        incoming = json.loads(Path(path or data_path()).read_text(encoding='utf-8'))
        if not isinstance(incoming, dict):
            raise ValueError()
        for name, values in (('language', LANGUAGES), ('difficulty', DIFFICULTIES),
                             ('theme', ('Notte', 'Giorno', 'Contrasto')), ('size', (17, 19, 21)), ('speed', (.5, 1, 2, 3)), ('mission', BY_KEY)):
            if incoming.get(name) in values and not (name in ('size', 'speed') and type(incoming.get(name)) is bool):
                state[name] = incoming[name]
        for name in ('completed', 'quizzes'):
            if isinstance(incoming.get(name), list):
                state[name] = list(dict.fromkeys(v for v in incoming[name][:1000] if isinstance(v, str)))
        if isinstance(incoming.get('drafts'), dict):
            state['drafts'] = {k: v for k, v in list(incoming['drafts'].items())[:300] if isinstance(k, str) and isinstance(v, str) and len(v) <= MAX_CODE}
        if isinstance(incoming.get('blocks'), dict):
            for key, choices in list(incoming['blocks'].items())[:100]:
                if key in BY_KEY and isinstance(choices, list) and len(choices) == len(BY_KEY[key].slots) and all(type(v) is int and -1 <= v < len(slot.options) for v, slot in zip(choices, BY_KEY[key].slots)):
                    state['blocks'][key] = choices
        state['classroom'] = classroom.clean(incoming.get('classroom'))
        return state, ''
    except FileNotFoundError:
        return state, ''
    except (OSError, ValueError, TypeError):
        return state, 'Il salvataggio non è leggibile. Puoi continuare con una nuova sessione.'


def save(state, path=None):
    path = Path(path or data_path())
    temporary = path.with_suffix('.tmp')
    try:
        temporary.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding='utf-8')
        os.replace(temporary, path)
        return ''
    except OSError:
        return 'Non riesco a salvare qui. Estrai il programma in una cartella personale scrivibile; questa sessione resta in memoria.'
