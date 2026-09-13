"""Interactive lessons, five-drone rounds and a hands-on Boolean bench."""
import random
import pygame
from engine import LANGUAGES, describe, parse, run
from logic import OPERATORS, REPRESENTATIONS, EXPLANATIONS, NOTES, compute, normalize, present, sample_source, truth_table
from missions import Case
from ui import Editor, font, mix, panel, text, wrap

# Each sequence includes a contrast and the mission's important edge case.
GUIDED_CASES = {
    'ricarica': (1, 2, 3), 'portello': (0, 1, 0), 'soglia': (0, 1, 2),
    'indipendenti': (0, 1, 2), 'catena': (0, 1, 3), 'priorita': (0, 2, 3),
    'and': (0, 1, 3), 'or': (0, 2, 3), 'intervallo': (0, 1, 3),
    'annidato': (0, 1, 2), 'soccorso': (0, 1, 3), 'turno': (0, 1, 2),
    'not': (0, 1, 0), 'bit_and': (1, 3, 0), 'bit_or': (1, 3, 0),
    'xor': (1, 3, 0), 'bit_not': (0, 1, 0), 'campo': (0, 1, 2),
    'campi_and': (1, 3, 4), 'campi_xor': (1, 3, 4),
}


class Activities:
    def init_activities(self):
        self.catalog_page = 0
        self.activity_cases, self.activity_options = [], []
        self.activity_round = 0
        self.activity_correct, self.activity_complete = False, False
        self.activity_selected, self.activity_progress = None, 0
        self.activity_attempt = None
        self.activity_code, self.activity_feedback, self.activity_details = '', '', ''
        self.activity_mistakes = 0
        self.logic_return = 'home'
        self.logic_operator, self.logic_representation = 'AND', 'Booleani'
        self.logic_bits = [False, True]
        self.logic_fields = [Editor(''), Editor('ORIONE')]
        self.logic_editor = Editor()
        self.logic_language = self.language
        self.logic_origin_language = self.language

    def open_activity(self, key):
        self.open_mission(key)
        if self.mode == 'learn':
            self.begin_activity(lesson=True)
        elif self.easy:
            self.begin_activity()

    def begin_activity(self, lesson=False, code=None):
        self.persist()
        self.playing = False
        self.activity_code = code or self.mission.solution(self.language)
        available = list(self.mission.cases)
        if lesson:
            self.activity_cases = [available[index] for index in GUIDED_CASES[self.mission.key]]
        else:
            self.activity_cases = [available[i % len(available)] for i in range(4)]
            self.activity_cases.append(Case('Caso a sorpresa', random.choice(list(self.mission.all_cases())).values))
        self.activity_round, self.activity_mistakes = 0, 0
        self.page = 'briefing' if lesson else 'flight'
        self.activity_complete = False
        self.prepare_activity_case()

    def prepare_activity_case(self):
        self.invalidate()
        self.activity_correct, self.activity_selected, self.activity_progress = False, None, 0
        self.activity_attempt = None
        options = set(self.mission.rule(case.data) for case in self.mission.all_cases())
        self.activity_options = sorted(options)
        random.Random(self.mission.key + str(self.activity_round)).shuffle(self.activity_options)
        self.activity_feedback = ('Leggi la regola in alto, poi fai una previsione. Puoi riprovare senza perdere punti.' if self.page == 'briefing' else 'Leggi i sensori e assegna al drone l’ordine corretto.')
        if self.activity_round > 0:
            previous = self.activity_cases[self.activity_round - 1].values
            changed = [name for name, value in self.case.values.items() if value != previous.get(name)]
            self.activity_feedback = 'È cambiato: ' + ', '.join(changed) + '. Cambierà anche l’ordine?'
        if self.page == 'flight' and self.activity_round == 4:
            self.activity_feedback = 'Ultimo drone: un caso a sorpresa. Usa la regola, anche se questi dati sono nuovi.'
        self.activity_details = self.mission.concept

    def choose_order(self, index):
        if self.activity_correct or self.activity_complete or not 0 <= index < len(self.activity_options):
            return
        expected = self.mission.rule(self.case.data)
        chosen = self.activity_options[index]
        self.activity_attempt = index
        if chosen != expected:
            self.activity_mistakes += 1
            self.shake = 1
            self.activity_feedback = 'Il drone resta al sicuro. Ricontrolla la regola: ' + self.mission.hints[min(self.activity_mistakes - 1, 2)]
            self.activity_details = f'Hai proposto: {describe(chosen)}.\n\n{self.mission.trap}\n\nRileggi i dati: ' + self.describe_case()
            return
        self.activity_correct, self.activity_selected = True, index
        self.frames = run(parse(self.activity_code, self.language), self.case.data, self.language)
        self.frame_index, self.elapsed, self.playing = 0, 0, True
        self.activity_feedback = 'Ordine corretto: ' + describe(expected) + '. Ora guarda il portello e segui la decisione.'
        decisions = [frame.message for frame in self.frames if frame.kind == 'condition']
        states = '\n'.join(f'Riga {line}: {status}' for line, status in self.frames[-1].statuses)
        self.activity_details = self.mission.concept + '\n\nIN QUESTO CASO\n' + '\n\n'.join(decisions) + '\n\nCONTROLLI RAGGIUNTI E SALTATI\n' + states + '\n\n' + self.mission.trap

    def describe_case(self):
        def label(value):
            return repr(value) if isinstance(value, str) else str(value)
        return ', '.join(name + '=' + label(value) for name, value in self.case.values.items())

    def next_drone(self):
        if not self.activity_correct or self.activity_progress < 1 or self.playing:
            return
        if self.activity_round + 1 < len(self.activity_cases):
            self.activity_round += 1
            self.prepare_activity_case()
        else:
            self.activity_complete = True
            self.activity_feedback = self.mission.concept if self.page == 'briefing' else 'Tutti i cinque droni hanno ricevuto l’ordine corretto. Prova ora a scrivere una regola che li gestisca da sola nel Laboratorio del codice.'
            if self.page == 'flight' and self.difficulty == 'Facile':
                if self.key() not in self.state['completed']:
                    self.state['completed'].append(self.key())
                self.persist()

    def update_activities(self, dt):
        if self.page in ('flight', 'briefing') and not self.modal and self.activity_correct and not self.activity_complete:
            if self.playing:
                self.activity_progress = min(1, self.activity_progress + dt * .6 * self.state['speed'])
                self.elapsed += dt
                if self.elapsed >= .65 / self.state['speed']:
                    self.elapsed = 0
                    if self.frame_index + 1 < len(self.frames):
                        self.frame_index += 1
                    elif self.activity_progress >= 1:
                        self.playing = False

    def logic_values(self):
        if self.logic_representation == 'Campi':
            return tuple(normalize(editor.value, 'Campi') for editor in self.logic_fields)
        if self.logic_representation == '0/1':
            return tuple(normalize(int(value), '0/1') for value in self.logic_bits)
        return tuple(self.logic_bits)

    def draw_logic(self):
        self.header('Banco logico · cambia un ingresso e osserva che cosa cambia')
        text(self.canvas, 'Cambia gli ingressi: il risultato si aggiorna da solo.', (40, 105), 30, self.c['text'], True)
        for index, representation in enumerate(REPRESENTATIONS):
            self.button('representation:' + representation, representation, (40 + index * 220, 155, 210, 43), selected=self.logic_representation == representation)
        for index, operator in enumerate(OPERATORS):
            self.button('operator:' + operator, operator, (742 + index * 166, 155, 158, 43), selected=self.logic_operator == operator)
        values = self.logic_values()
        result = compute(self.logic_operator, *values)
        for index in range(2):
            left = 40 + index * 340
            enabled = not (self.logic_operator == 'NOT' and index == 1)
            panel(self.canvas, pygame.Rect(left, 221, 320, 247), self.c['panel'], self.c['border'], 16)
            text(self.canvas, 'INGRESSO ' + ('A' if index == 0 else 'B'), (left + 18, 240), 17, self.c['accent'] if enabled else self.c['muted'], True)
            text(self.canvas, 'Clicca nel campo e scrivi' if self.logic_representation == 'Campi' else 'Clicca sul valore per cambiarlo', (left + 18, 266), 13, self.c['muted'])
            if self.logic_representation == 'Campi':
                self.logic_fields[index].draw(self.canvas, pygame.Rect(left + 17, 280, 285, 52), self.c, readonly=not enabled, tick=self.time, size=18, line_numbers=False)
                length = len(self.logic_fields[index].value)
                text(self.canvas, str(length) + (' carattere' if length == 1 else ' caratteri'), (left + 160, 400), 14, self.c['muted'], anchor='center')
                for j, (label, value) in enumerate((('Vuoto', ''), ('"0"', '0'), ('Spazio', ' '))):
                    self.button(f'field:{index}:{j}', label, (left + 17 + j * 96, 348, 89, 36), active=enabled, size=16)
            else:
                label = str(int(values[index])) if self.logic_representation == '0/1' else str(values[index]) if self.logic_language == 'Python' else str(values[index]).lower()
                self.button('bit:' + str(index), label, (left + 30, 285, 260, 91), active=enabled, selected=values[index], size=35)
            note = f'{int(values[index])} = ' + ('vero' if values[index] else 'falso') if enabled else 'NOT usa soltanto A'
            text(self.canvas, note, (left + 160, 422), 22, self.c['mint'] if values[index] and enabled else self.c['muted'], True, 'center')
        panel(self.canvas, pygame.Rect(742, 221, 658, 142), self.c['panel'], self.c['mint'] if result else self.c['accent'], 16)
        text(self.canvas, 'RISULTATO', (765, 242), 15, self.c['muted'], True)
        text(self.canvas, f'{int(result)} = ' + ('true · vero' if result else 'false · falso'), (1071, 304), 38, self.c['mint'] if result else self.c['accent'], True, 'center')
        panel(self.canvas, pygame.Rect(742, 380, 658, 271), self.c['panel'], self.c['border'], 16)
        text(self.canvas, 'TABELLA DI VERITÀ · la riga accesa è il tuo caso', (763, 399), 17, self.c['text'], True)
        for x, label in ((812, 'A'), (992, 'B'), (1220, self.logic_operator)):
            text(self.canvas, label, (x, 437), 17, self.c['muted'], True, 'center')
        for index, (a, b, answer) in enumerate(truth_table(self.logic_operator)):
            active = a == values[0] and (self.logic_operator == 'NOT' or b == values[1])
            y = 464 + index * 43
            if active:
                panel(self.canvas, pygame.Rect(761, y - 13, 619, 38), mix(self.c['panel'], self.c['mint'], .15), self.c['mint'], 6)
            for x, label in ((812, str(int(a))), (992, '—' if self.logic_operator == 'NOT' else str(int(b))), (1220, str(int(answer)))):
                text(self.canvas, label, (x, y + 6), 23, self.c['mint'] if active else self.c['text'], True, 'center')
        for index, language in enumerate(LANGUAGES):
            self.button('logic_lang:' + language, language, (40 + index * 167, 483, 157, 37), selected=language == self.logic_language, size=16)
        code = sample_source(self.logic_operator, self.logic_representation, self.logic_language)
        if self.logic_editor.value != code:
            self.logic_editor.set(code)
        self.logic_editor.draw(self.canvas, pygame.Rect(40, 532, 660, 241), self.c, readonly=True, size=18)
        wrap(self.canvas, EXPLANATIONS[self.logic_operator], pygame.Rect(750, 674, 642, 111), 19, self.c['text'])
        self.button('logic_help', 'Il perché · prova anche "0" e uno spazio', (40, 799, 660, 46), size=18)
        self.button('logic_back', 'Torna alla missione' if self.logic_return in ('lab', 'flight', 'briefing', 'quiz') else 'Torna indietro', (1065, 799, 335, 46), primary=True)

    def activity_action(self, key):
        if key.startswith('order:'):
            self.choose_order(int(key.split(':')[1]))
        elif key == 'next_drone':
            self.next_drone()
        elif key == 'activity_why':
            self.open_text('Un dato alla volta', self.activity_details)
        elif key == 'activity_again':
            self.begin_activity(code=self.activity_code)
        elif key == 'activity_resume':
            self.playing = True
        elif key == 'guided':
            self.persist()
            self.mode = 'learn'
            self.begin_activity(lesson=True)
        elif key == 'activity_play':
            self.mode = 'game'
            self.state['difficulty'] = 'Facile'
            self.begin_activity()
        elif key == 'activity_code':
            self.persist()
            self.mode = 'game'
            self.open_mission(self.mission.key)
        elif key == 'test_flight':
            self.begin_activity(code=self.code())
        elif key == 'logic':
            self.persist()
            self.playing = False
            if self.page != 'logic':
                self.logic_return = self.page
                self.logic_language = self.language
                self.logic_origin_language = self.language
            self.page = 'logic'
        elif key == 'logic_back':
            self.page = self.logic_return
            if self.page == 'lab' and self.logic_origin_language != self.language:
                self.load_editor()
            elif self.page in ('flight', 'briefing') and self.logic_origin_language != self.language:
                self.begin_activity(lesson=self.page == 'briefing')
        elif key.startswith('logic_lang:'):
            self.logic_language = key.split(':')[1]
        elif key == 'logic_help':
            self.open_text('Prova, osserva, distingui', NOTES)
        elif key.startswith('operator:'):
            self.logic_operator = key.split(':')[1]
            if self.logic_operator == 'NOT':
                self.logic_fields[1].focus = False
        elif key.startswith('representation:'):
            self.logic_representation = key.split(':')[1]
            for editor in self.logic_fields:
                editor.focus = False
        elif key.startswith('bit:'):
            index = int(key.split(':')[1])
            self.logic_bits[index] = not self.logic_bits[index]
        elif key.startswith('field:'):
            _, index, choice = key.split(':')
            self.logic_fields[int(index)].set(('', '0', ' ')[int(choice)])
        else:
            return False
        return True

    def logic_event(self, event):
        if self.page != 'logic' or self.modal or self.logic_representation != 'Campi':
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for index, editor in enumerate(self.logic_fields):
                editor.focus = editor.rect.collidepoint(self.pointer) and (index == 0 or self.logic_operator != 'NOT')
                if editor.focus:
                    editor.click(self.pointer)
        editor = next((editor for editor in self.logic_fields if editor.focus), None)
        if editor is None:
            return False
        if event.type == pygame.TEXTINPUT:
            value = event.text.replace('\n', '').replace('\r', '')
            if len(editor.value) + len(value) - abs(editor.caret - editor.anchor) <= 40:
                editor.replace(value)
            return True
        if event.type == pygame.KEYDOWN and event.key not in (pygame.K_ESCAPE, pygame.K_F11):
            if event.key not in (pygame.K_RETURN, pygame.K_TAB):
                editor.key(event)
                cleaned = editor.value.replace('\n', '').replace('\r', '')[:40]
                if cleaned != editor.value:
                    editor.set(cleaned)
            return True
        return False
