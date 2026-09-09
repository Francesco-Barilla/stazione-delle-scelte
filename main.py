"""Stazione delle scelte: explanations, programming missions and misconceptions."""
import json
import os
from pathlib import Path
import sys

if '--smoke-test' in sys.argv:
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    os.environ['SDL_AUDIODRIVER'] = 'dummy'
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
import pygame

from engine import COMMANDS, LANGUAGES, CodeError, describe, format_expression, parse, run
from activities import Activities
from lessons import HOW_TO_PLAY, LANGUAGE_NOTES, MISCONCEPTIONS, PROCEDURE, QUIZZES, commands_text
from missions import BY_KEY, DIFFICULTIES, GROUPS, MISSIONS, validate
from scene import icon, stars, station
import storage
from ui import SIZE, THEMES, Editor, font, lines, mix, palette, panel, text, wrap

TITLE = 'Stazione delle scelte'


class App(Activities):
    def __init__(self, screen, state_path=None, saving=True):
        self.screen, self.canvas = screen, pygame.Surface(SIZE)
        self.state_path, self.saving = state_path, saving
        self.state, self.notice = storage.load(state_path)
        self.c = palette(self.state['theme'])
        self.page, self.return_page, self.mode, self.filter = 'home', 'home', 'learn', 'Tutte'
        self.mission = BY_KEY[self.state['mission']]
        self.editor, self.buttons = Editor(), []
        self.solution_editor = Editor()
        self.pointer, self.pressed, self.focus = (-1, -1), None, None
        self.modal, self.modal_scroll, self.modal_max = None, 0, 0
        self.modal_text, self.modal_title = '', ''
        self.choices, self.block_scroll, self.code_view = [], 0, False
        self.case_index, self.extra_case = 0, None
        self.frames, self.frame_index, self.playing, self.elapsed, self.motion = [], 0, False, 0, 1
        self.feedback, self.review, self.error_line, self.hint_level = '', None, 0, 0
        self.quiz_index, self.quiz_choice, self.quiz_attempted, self.quiz_correct = 0, None, False, False
        self.time, self.shake, self.alive = 0, 0, True
        self.fullscreen, self.window_size = False, screen.get_size()
        self.code_rect = pygame.Rect(742, 288, 658, 345)
        self.block_rect = self.code_rect.copy()
        self.init_activities()

    @property
    def language(self):
        return self.state['language']

    @property
    def difficulty(self):
        return self.state['difficulty']

    @property
    def easy(self):
        return self.mode == 'game' and self.difficulty == 'Facile'

    @property
    def quiz(self):
        return QUIZZES[self.quiz_index]

    @property
    def case(self):
        if self.page == 'quiz':
            return self.quiz.case
        if self.page in ('flight', 'briefing'):
            return self.activity_cases[self.activity_round]
        return self.extra_case or self.mission.cases[self.case_index]

    @property
    def frame(self):
        return self.frames[self.frame_index] if self.frames else None

    def key(self):
        return f'{self.mission.key}:{self.difficulty}:{self.language}'

    def save_draft(self):
        if self.page == 'lab' and self.mode == 'game':
            if self.easy:
                self.state['blocks'][self.mission.key] = list(self.choices)
            else:
                self.state['drafts'][self.key()] = self.editor.value

    def persist(self):
        self.save_draft()
        if self.saving:
            self.notice = storage.save(self.state, self.state_path)

    def invalidate(self, clear_feedback=True):
        self.frames, self.frame_index, self.playing = [], 0, False
        self.elapsed, self.motion, self.error_line = 0, 1, 0
        self.review = None
        if clear_feedback:
            self.feedback = ''

    def open_mission(self, key):
        self.persist()
        self.mission = BY_KEY[key]
        self.state['mission'] = key
        self.page, self.case_index, self.extra_case = 'lab', 0, None
        self.hint_level, self.block_scroll, self.code_view = 0, 0, False
        self.load_editor()
        self.persist()

    def load_editor(self):
        self.invalidate()
        self.editor.focus = False
        if self.mode == 'learn':
            self.editor.set(self.mission.solution(self.language))
        elif self.easy:
            self.choices = list(self.state['blocks'].get(self.mission.key, [-1] * len(self.mission.slots)))
            self.sync_blocks()
        else:
            self.editor.set(self.state['drafts'].get(self.key(), self.mission.starter(self.language, self.difficulty)))

    def sync_blocks(self):
        try:
            self.editor.set(self.mission.program(self.choices, self.language))
        except CodeError:
            self.editor.set(('# ' if self.language == 'Python' else '// ') + 'Completa i blocchi per vedere il codice equivalente.\n')
        self.invalidate()

    def set_language(self, language):
        if language == self.language:
            return
        self.persist()
        self.state['language'] = language
        destination = self.return_page if self.page == 'settings' else self.page
        if destination == 'lab':
            self.load_editor()
        elif destination == 'quiz':
            current_page = self.page
            self.open_quiz(self.quiz_index)
            self.page = current_page
        elif destination in ('flight', 'briefing'):
            current_page = self.page
            self.activity_code = self.mission.solution(language)
            self.page = destination
            self.activity_round, self.activity_complete = 0, False
            self.prepare_activity_case()
            self.page = current_page
        self.persist()

    def set_difficulty(self, difficulty):
        if difficulty == self.difficulty:
            return
        self.persist()
        self.state['difficulty'] = difficulty
        self.block_scroll = 0
        if self.page == 'lab':
            self.load_editor()
        elif self.page == 'flight':
            self.open_activity(self.mission.key)
        self.persist()

    def code(self):
        if self.page == 'quiz':
            return self.quiz.source(self.language)
        if self.page in ('flight', 'briefing'):
            return self.activity_code
        return self.mission.program(self.choices, self.language) if self.easy else self.editor.value

    def error(self, error):
        self.playing = False
        self.feedback, self.error_line, self.shake = str(error), error.line, 1
        self.follow_line(error.line)

    def start_trace(self, auto=True):
        try:
            self.frames = run(parse(self.code(), self.language), self.case.data, self.language)
            self.frame_index, self.elapsed, self.motion = 0, 0, 1
            self.playing, self.error_line = auto, 0
            if self.easy and self.page == 'lab':
                self.code_view = True
        except CodeError as error:
            self.error(error)

    def follow_line(self, line=None):
        line = line if line is not None else self.frame.line if self.frame else 0
        if line:
            visible = max(1, self.code_rect.height // (self.state['size'] + 8) - 1)
            if line - 1 < self.editor.scroll or line - 1 >= self.editor.scroll + visible:
                self.editor.scroll = max(0, line - 3)

    def advance(self):
        if self.frame_index + 1 < len(self.frames):
            self.frame_index += 1
            self.motion = 0 if self.frame.kind == 'action' else 1
            self.follow_line()
        else:
            self.playing = False

    def verify(self):
        self.persist()
        self.playing = False
        try:
            self.review = validate(self.mission, self.code(), self.language)
            self.feedback, self.error_line = self.review.message, 0
            if self.review.success:
                if self.key() not in self.state['completed']:
                    self.state['completed'].append(self.key())
                self.persist()
            else:
                self.shake = 1
                if self.review.case:
                    self.extra_case = self.review.case
                    self.start_trace(False)
        except CodeError as error:
            self.error(error)

    def open_quiz(self, index):
        self.persist()
        self.quiz_index = index
        self.mission = BY_KEY[self.quiz.mission]
        self.page = 'quiz'
        self.quiz_choice, self.quiz_attempted, self.quiz_correct = None, False, False
        self.editor.set(self.quiz.source(self.language))
        self.editor.focus = False
        self.invalidate()

    def verify_quiz(self):
        if self.quiz_choice is None:
            return
        self.quiz_attempted = True
        self.quiz_correct = self.quiz_choice == self.quiz.answer
        self.feedback = ('Previsione corretta. ' if self.quiz_correct else 'Questa previsione non corrisponde al codice. ') + self.quiz.explanation
        if self.quiz_correct:
            key = self.quiz.key + ':' + self.language
            if key not in self.state['quizzes']:
                self.state['quizzes'].append(key)
            self.persist()
        else:
            self.shake = 1

    def open_text(self, title, contents, kind='text'):
        self.playing = False
        self.modal, self.modal_title, self.modal_text = kind, title, contents
        self.modal_scroll, self.modal_max = 0, 0
        self.editor.focus = False

    def lesson(self, tab='Idea'):
        content = {'Idea': self.mission.objective + '\n\nL’IDEA\n' + self.mission.concept + '\n\nATTENZIONE\n' + self.mission.trap,
                   'Procedimento': PROCEDURE, 'Equivoci': self.mission.trap + '\n\n' + MISCONCEPTIONS,
                   'Linguaggi': LANGUAGE_NOTES[self.language], 'Comandi': commands_text(self.mission, self.language), 'Gioco': HOW_TO_PLAY}[tab]
        self.lesson_tab = tab
        self.open_text(tab + ' · ' + self.language, content, 'lesson')

    def logical(self, position):
        width, height = self.screen.get_size()
        scale = min(width / SIZE[0], height / SIZE[1])
        return ((position[0] - (width - SIZE[0] * scale) / 2) / scale,
                (position[1] - (height - SIZE[1] * scale) / 2) / scale)

    def button(self, key, label, rect, active=True, selected=False, primary=False, size=18):
        rect = pygame.Rect(rect)
        hovered = active and rect.collidepoint(self.pointer)
        color = self.c['mint'] if primary else self.c['accent'] if selected else self.c['border']
        fill = mix(self.c['card'], color, .13 if hovered or selected or primary else 0)
        panel(self.canvas, rect, fill, self.c['mint'] if hovered else color, 10)
        if hovered:
            pygame.draw.rect(self.canvas, self.c['mint'], rect, 2, border_radius=10)
        label_color = self.c['text'] if active else mix(self.c['card'], self.c['muted'], .6)
        if font(size).size(label)[0] <= rect.width - 18:
            text(self.canvas, label, rect.center, size, label_color, selected or primary, 'center')
        else:
            wrap(self.canvas, label, rect.inflate(-18, -10), size, label_color, selected or primary)
        self.buttons.append((key, rect, active))

    def header(self, subtitle='Un dato. Una condizione. Una scelta.'):
        self.canvas.blit(pygame.transform.smoothscale(icon(), (42, 42)), (36, 28))
        text(self.canvas, 'STAZIONE DELLE SCELTE', (92, 29), 24, self.c['text'], True)
        text(self.canvas, subtitle, (93, 59), 15, self.c['muted'])
        if self.page != 'home':
            if self.page != 'logic':
                self.button('logic', 'Banco logico', (795, 30, 171, 46), size=17)
            self.button('catalog', 'Sfide', (978, 30, 112, 46))
            self.button('settings', 'Impostazioni', (1100, 30, 171, 46))
            self.button('home', 'Home', (1281, 30, 119, 46))
        else:
            self.button('logic', 'Banco logico', (864, 30, 185, 46))
            self.button('help', 'Come si gioca', (1060, 30, 185, 46))
            self.button('settings', 'Impostazioni', (1255, 30, 145, 46), size=16)

    def selectors(self, quiz=False):
        for i, language in enumerate(LANGUAGES):
            self.button('lang:' + language, language, (742 + i * 166, 141, 158, 40), selected=self.language == language, size=17)
        if not quiz:
            for i, difficulty in enumerate(DIFFICULTIES):
                self.button('diff:' + difficulty, difficulty, (742 + i * 222, 192, 214, 39), active=self.mode == 'game', selected=self.difficulty == difficulty, size=17)

    def draw_home(self):
        self.header()
        text(self.canvas, 'Decidi il futuro della stazione.', (54, 128), 43, self.c['text'], True)
        wrap(self.canvas, 'Portelli, risorse e missioni: scopri come un programma sceglie cosa fare.\nImpara a leggere anche le condizioni che non vengono valutate.', pygame.Rect(56, 193, 1240, 85), 23, self.c['muted'])
        cards = [('learn', '01  IMPARA FACENDO', 'Prevedi. Osserva. Riprova.', 'Tre piccoli esperimenti: cambia un dato e scopri perché cambia la decisione.', self.c['mint']),
                 ('game', '02  GIOCA', 'Cinque droni ti aspettano.', f'{len(MISSIONS)} missioni · 3 difficoltà. Dai gli ordini, poi impara a programmare la stazione.', self.c['blue']),
                 ('quiz', '03  SCOVA L’EQUIVOCO', 'Metti alla prova un’idea.', 'Prevedi il risultato, segui la traccia e scopri perché una risposta può ingannare.', self.c['accent'])]
        for i, (mode, title, headline, description, color) in enumerate(cards):
            rect = pygame.Rect(54 + i * 450, 299, 431, 218)
            hover = rect.collidepoint(self.pointer)
            panel(self.canvas, rect, self.c['panel'], color if hover else self.c['border'], 19)
            pygame.draw.rect(self.canvas, color, (rect.x + 22, rect.y + 24, 5, 28), border_radius=2)
            text(self.canvas, title, (rect.x + 41, rect.y + 26), 19, color, True)
            text(self.canvas, headline, (rect.x + 23, rect.y + 76), 24, self.c['text'], True)
            wrap(self.canvas, description, pygame.Rect(rect.x + 23, rect.y + 115, rect.width - 46, 73), 19, self.c['muted'])
            self.buttons.append(('mode:' + mode, rect, True))
        station(self.canvas, pygame.Rect(55, 552, 840, 281), self.c, self.time)
        text(self.canvas, 'IL LABORATORIO', (948, 577), 17, self.c['accent'], True)
        wrap(self.canvas, 'if · if / else · if annidati\nelif / else if\nAND · OR · NOT · XOR\n0 / 1 · true / false · campi di testo\n\nPython · JavaScript · C · Java', pygame.Rect(948, 618, 435, 193), 21, self.c['text'])

    def draw_catalog(self):
        self.header('Impara' if self.mode == 'learn' else 'Gioca' if self.mode == 'game' else 'Scova l’equivoco · prevedi, osserva, comprendi')
        for i, group in enumerate(GROUPS):
            if self.mode != 'quiz':
                self.button('filter:' + group, group, (40 + i * 224, 103, 212, 40), selected=self.filter == group, size=17)
        text(self.canvas, self.language + (' · ' + self.difficulty if self.mode == 'game' else ''), (1398, 113), 18, self.c['muted'], anchor='topright')
        items = list(enumerate(QUIZZES)) if self.mode == 'quiz' else [(i, m) for i, m in enumerate(MISSIONS) if self.filter == 'Tutte' or m.group == self.filter]
        pages = max(1, (len(items) + 8) // 9)
        self.catalog_page = max(0, min(self.catalog_page, pages - 1))
        for index, (original, item) in enumerate(items[self.catalog_page * 9:(self.catalog_page + 1) * 9]):
            rect = pygame.Rect(40 + index % 3 * 463, 166 + index // 3 * 205, 446, 187)
            selected = (item.key + ':' + self.language in self.state['quizzes']) if self.mode == 'quiz' else (f'{item.key}:{self.difficulty}:{self.language}' in self.state['completed'])
            panel(self.canvas, rect, self.c['panel'], self.c['mint'] if rect.collidepoint(self.pointer) or selected else self.c['border'], 15)
            tag = 'EQUIVOCO ' + str(original + 1).zfill(2) if self.mode == 'quiz' else item.group.upper()
            text(self.canvas, tag, (rect.x + 20, rect.y + 16), 12, self.c['mint'] if selected else self.c['accent'], True)
            text(self.canvas, '✓' if selected else '→', (rect.right - 23, rect.y + 18), 21, self.c['mint'], anchor='topright')
            wrap(self.canvas, item.title, pygame.Rect(rect.x + 20, rect.y + 46, rect.width - 40, 54), 21, self.c['text'], True)
            label = 'Prevedi il comportamento del codice.' if self.mode == 'quiz' else item.subtitle
            wrap(self.canvas, label, pygame.Rect(rect.x + 20, rect.y + 106, rect.width - 40, 44), 16, self.c['muted'])
            self.buttons.append(('quiz:' + str(original) if self.mode == 'quiz' else 'mission:' + item.key, rect, True))
        text(self.canvas, f'{len(items)} sfide · pagina {self.catalog_page + 1} / {pages}', (720, 822), 19, self.c['muted'], anchor='center')
        self.button('catalog_page:-1', '← Precedenti', (40, 799, 225, 45), active=self.catalog_page > 0)
        self.button('catalog_page:1', 'Altre sfide →', (1175, 799, 225, 45), active=self.catalog_page + 1 < pages)

    def draw_data(self, top, width=660):
        fields = list(self.case.values)
        count = max(1, len(fields))
        for i, name in enumerate(fields):
            rect = pygame.Rect(40 + i * (width + 8) / count, top, (width + 8) / count - 8, 63)
            panel(self.canvas, rect, self.c['panel'], self.c['border'], 10)
            value = self.case.values[name]
            extra = ''
            if isinstance(value, str):
                label = '"' + value + '"' if value != ' ' else '" " · uno spazio'
                extra = name.replace('testo_', 'campo_') + ': ' + ('1 = vero' if value else '0 = falso')
            elif type(value) is bool or name.startswith('segnale_'):
                label = str(int(value)) + ' = ' + ('True' if value else 'False') if self.language == 'Python' else str(int(value)) + ' = ' + ('true' if value else 'false')
            else:
                label = str(value) + ('%' if name == 'batteria' else ' kg' if name == 'peso' else ' °C' if name == 'temperatura' else '')
            text(self.canvas, name, (rect.x + 13, rect.y + 5), 13, self.c['muted'])
            text(self.canvas, label, (rect.x + 13, rect.y + 23), 19, self.c['mint'] if value else self.c['accent'], True)
            if extra:
                text(self.canvas, extra, (rect.x + 13, rect.y + 46), 12, self.c['muted'])

    def draw_scene(self, rect):
        frame = self.frame
        previous = self.frames[self.frame_index - 1].actions if self.frames and self.frame_index else ()
        station(self.canvas, pygame.Rect(rect), self.c, self.time, frame.actions if frame else (), previous, self.motion, self.shake)

    def draw_statuses(self, top):
        rect = pygame.Rect(742, top, 658, 43)
        panel(self.canvas, rect, self.c['panel'], self.c['border'], 8)
        states = self.frame.statuses if self.frame else ()
        if not states:
            text(self.canvas, 'Stati dei controlli dopo ogni passo', (756, top + 12), 15, self.c['muted'])
            return
        x = 755
        for line, status in states:
            label = f'R{line} · {status}'
            width = font(14, True).size(label)[0] + 22
            if x + width > rect.right - 15:
                text(self.canvas, '…', (rect.right - 21, top + 13), 17, self.c['muted'])
                break
            color = self.c['mint'] if status == 'VERO' else self.c['danger'] if status == 'FALSO' else self.c['muted']
            panel(self.canvas, pygame.Rect(x, top + 7, width - 6, 28), mix(self.c['panel'], color, .12), radius=5)
            text(self.canvas, label, (x + 7, top + 13), 14, color, True)
            x += width
        self.buttons.append(('trace_details', rect, True))

    def draw_blocks(self):
        rect = self.block_rect
        panel(self.canvas, rect, self.c['bg'], self.c['border'], 10)
        total = len(self.mission.slots) * 72
        self.block_scroll = max(0, min(self.block_scroll, max(0, total - rect.height + 10)))
        clip = self.canvas.get_clip()
        self.canvas.set_clip(rect.inflate(-4, -4).clip(clip))
        for i, slot in enumerate(self.mission.slots):
            row = pygame.Rect(rect.x + 12 + slot.depth * 23, rect.y + 9 + i * 72 - self.block_scroll, rect.width - 33 - slot.depth * 23, 63)
            color = self.c['blue'] if slot.kind == 'condition' else self.c['mint']
            panel(self.canvas, row, self.c['card'], color if row.collidepoint(self.pointer) else self.c['border'], 8)
            pygame.draw.rect(self.canvas, color, (row.x, row.y + 8, 3, row.height - 16), border_radius=1)
            text(self.canvas, slot.label, (row.x + 14, row.y + 7), 12, color, True)
            selected = self.choices[i]
            value = 'Scegli una condizione…' if slot.kind == 'condition' else 'Scegli un’azione…'
            if selected >= 0:
                value = format_expression(slot.options[selected], self.language) if slot.kind == 'condition' else COMMANDS[slot.options[selected]] + ' · ' + slot.options[selected] + '()'
            text(self.canvas, value, (row.x + 14, row.y + 31), 17, self.c['text'])
            pygame.draw.polygon(self.canvas, self.c['muted'], [(row.right - 26, row.y + 35), (row.right - 16, row.y + 35), (row.right - 21, row.y + 41)])
            hit = row.clip(rect.inflate(-4, -4))
            if hit.height:
                self.buttons.append(('slot:' + str(i), hit, True))
        self.canvas.set_clip(clip)
        if total > rect.height:
            track = rect.height - 12
            height = track * rect.height / total
            y = rect.y + 6 + (track - height) * self.block_scroll / (total - rect.height + 10)
            panel(self.canvas, pygame.Rect(rect.right - 8, y, 4, height), self.c['muted'], radius=2)

    def playback(self, top, quiz=False):
        enabled = not quiz or self.quiz_attempted
        self.button('run', 'Pausa' if self.playing else 'Esegui', (742, top, 157, 45), active=enabled, primary=True)
        self.button('step', 'Un passo', (909, top, 157, 45), active=enabled)
        self.button('back', 'Indietro', (1076, top, 157, 45), active=bool(self.frames and self.frame_index > 0))
        self.button('restart', 'Riparti', (1243, top, 157, 45), active=enabled)

    def draw_lab(self):
        self.header('Impara · osserva il programma' if self.mode == 'learn' else 'Gioca · costruisci una regola valida per tutti i casi')
        text(self.canvas, self.mission.title, (40, 107), 28, self.c['text'], True)
        self.selectors()
        panel(self.canvas, pygame.Rect(40, 151, 660, 98), self.c['panel'], self.c['border'], 12)
        wrap(self.canvas, self.mission.objective, pygame.Rect(57, 164, 626, 74), 18, self.c['text'])
        self.draw_scene((40, 261, 660, 240))
        self.button('case:-1', '‹', (40, 511, 49, 39))
        text(self.canvas, (self.extra_case.label if self.extra_case else f'{self.case_index + 1}/{len(self.mission.cases)} · {self.case.label}'), (370, 522), 18, self.c['text'], anchor='midtop')
        self.button('case:1', '›', (651, 511, 49, 39))
        self.draw_data(562)
        frame = self.frame
        panel(self.canvas, pygame.Rect(40, 638, 660, 147), self.c['panel'], self.c['border'], 12)
        text(self.canvas, f'PASSO {self.frame_index + 1}/{len(self.frames)}' if frame else 'OSSERVA IL FLUSSO', (56, 651), 13, self.c['accent'], True)
        self.button('trace_details', 'Dettagli', (591, 645, 96, 31), active=bool(frame), size=14)
        text(self.canvas, frame.title if frame else 'Leggi i dati, poi esegui.', (56, 676), 22, self.c['text'], True)
        message = frame.message if frame else 'La riga attiva e gli stati delle condizioni mostrano il percorso della decisione.'
        wrap(self.canvas, message, pygame.Rect(56, 709, 628, 64), 17, self.c['muted'])
        self.button('guided', 'Impara facendo', (40, 798, 208, 46))
        self.button('lesson:Equivoci', 'Equivoci', (258, 798, 207, 46))
        self.button('hint', 'Suggerimento', (475, 798, 225, 46))
        self.button('lesson:Comandi', 'Dati e comandi', (742, 243, 181, 36), size=16)
        if self.easy:
            self.button('view', 'Blocchi' if self.code_view else 'Vedi codice', (933, 243, 171, 36), size=16)
            self.button('block:-1', '↑', (1114, 243, 48, 36), active=not self.code_view)
            self.button('block:1', '↓', (1172, 243, 48, 36), active=not self.code_view)
        self.button('solution', 'Soluzione', (1230, 243, 170, 36), size=16)
        if self.easy and not self.code_view:
            self.draw_blocks()
        else:
            self.editor.draw(self.canvas, self.code_rect, self.c, active=frame.line if frame else 0, error=self.error_line,
                             readonly=self.mode == 'learn' or self.easy, tick=self.time, size=self.state['size'])
            self.draw_statuses(590)
        self.playback(644)
        if self.mode == 'game':
            passed = self.review and self.review.success
            self.button('test_flight' if passed else 'verify', 'Collauda la regola con cinque droni' if passed else 'Verifica missione · tutti i casi', (742, 701, 658, 47), primary=True)
        else:
            self.button('try', 'Ora prova tu · stessi dati, nuova sfida', (742, 701, 658, 47), primary=True)
        status = self.feedback or 'Scegli un caso e osserva i controlli. Apri le schede per leggere le spiegazioni complete.'
        panel(self.canvas, pygame.Rect(742, 760, 658, 85), self.c['panel'], self.c['mint'] if self.review and self.review.success else self.c['border'], 12)
        wrap(self.canvas, status, pygame.Rect(756, 771, 561, 60), 16, self.c['text'])
        self.button('feedback', 'Leggi', (1321, 781, 65, 41), active=bool(self.feedback), size=15)

    def draw_quiz(self):
        self.header('Scova l’equivoco · prima prevedi, poi osserva')
        text(self.canvas, f'{self.quiz_index + 1:02} · {self.quiz.title}', (40, 107), 28, self.c['text'], True)
        self.selectors(quiz=True)
        self.draw_scene((40, 160, 660, 259))
        text(self.canvas, self.quiz.case.label, (40, 436), 18, self.c['muted'])
        self.draw_data(469)
        wrap(self.canvas, self.quiz.question, pygame.Rect(40, 552, 650, 63), 23, self.c['text'], True)
        for i, choice in enumerate(self.quiz.choices):
            self.button('answer:' + str(i), choice, (40, 620 + i * 58, 660, 49), selected=self.quiz_choice == i, size=18)
        self.button('check_answer', 'Verifica previsione', (40, 804, 315, 46), active=self.quiz_choice is not None, primary=True)
        self.button('quiz_next', 'Prossimo equivoco →', (367, 804, 333, 46))
        self.code_rect = pygame.Rect(742, 194, 658, 354)
        self.editor.draw(self.canvas, self.code_rect, self.c, active=self.frame.line if self.frame else 0, readonly=True, tick=self.time, size=self.state['size'])
        self.draw_statuses(557)
        self.playback(613, quiz=True)
        text(self.canvas, 'La traccia si attiva dopo la tua prima previsione.', (743, 672), 16, self.c['muted'])
        panel(self.canvas, pygame.Rect(742, 707, 658, 142), self.c['panel'], self.c['mint'] if self.quiz_correct else self.c['border'], 12)
        wrap(self.canvas, self.feedback or 'Non cercare la soluzione ideale: prevedi ciò che esegue esattamente il codice mostrato.', pygame.Rect(758, 722, 622, 82), 18, self.c['text'])
        self.button('feedback', 'Leggi il perché', (1146, 804, 238, 34), active=self.quiz_attempted, size=16)

    def draw_settings(self):
        self.header('Preferenze della tua stazione')
        panel(self.canvas, pygame.Rect(180, 144, 1080, 639), self.c['panel'], self.c['border'], 20)
        for row, (label, prefix, options, current) in enumerate((
            ('Aspetto', 'theme:', tuple(THEMES), self.state['theme']),
            ('Testo del codice e delle spiegazioni', 'size:', ('17', '19', '21'), str(self.state['size'])),
            ('Velocità della traccia', 'speed:', ('0.5', '1', '2', '3'), str(self.state['speed'])),
            ('Linguaggio', 'lang:', LANGUAGES, self.language),
        )):
            top = 173 + row * 115
            text(self.canvas, label, (209, top), 21, self.c['text'], True)
            for i, option in enumerate(options):
                self.button(prefix + option, option + ('×' if prefix == 'speed:' else ''), (210 + i * 252, top + 38, 234, 44), selected=option == current)
        wrap(self.canvas, 'Le bozze e i progressi restano sul computer. Il cambio di tema o dimensione non cancella il tentativo. F11: schermo intero.', pygame.Rect(211, 656, 994, 64), 19, self.c['muted'])
        self.button('return', 'Torna al laboratorio', (870, 723, 350, 45), primary=True)

    def draw_modal(self):
        veil = pygame.Surface(SIZE, pygame.SRCALPHA)
        veil.fill((0, 0, 0, 175))
        self.canvas.blit(veil, (0, 0))
        self.buttons = []
        rect = pygame.Rect(174, 79, 1092, 748)
        panel(self.canvas, rect, self.c['panel'], self.c['border'], 20)
        text(self.canvas, self.modal_title, (204, 104), 27, self.c['text'], True)
        self.button('close', 'Chiudi', (1126, 99, 112, 42))
        top = 161
        if self.modal == 'lesson':
            for i, tab in enumerate(('Idea', 'Procedimento', 'Equivoci', 'Linguaggi', 'Comandi', 'Gioco')):
                self.button('lesson:' + tab, tab, (204 + i * 173, 159, 162, 39), selected=self.lesson_tab == tab, size=16)
            top = 217
        if self.modal == 'slot':
            slot = self.mission.slots[self.slot_index]
            wrap(self.canvas, 'Scegli il contenuto del blocco. La struttura della missione resta visibile nel laboratorio.', pygame.Rect(205, 172, 984, 70), 21, self.c['muted'])
            for i, option in enumerate(slot.options):
                label = format_expression(option, self.language) if slot.kind == 'condition' else COMMANDS[option] + ' · ' + option + '()'
                self.button('choose:' + str(i), label, (220, 280 + i * 103, 1000, 80), selected=self.choices[self.slot_index] == i, size=23)
            return
        if self.modal == 'solution':
            code_rect = pygame.Rect(206, 167, 994, 541)
            size = self.state['size']
            line_height = size + 8
            self.modal_max = max(0, len(self.solution_editor.value.splitlines()) - (code_rect.height - 16) // line_height + 1) * line_height
            self.modal_scroll = max(0, min(self.modal_scroll, self.modal_max))
            self.solution_editor.scroll = self.modal_scroll // line_height
            self.solution_editor.draw(self.canvas, code_rect, self.c, readonly=True, size=size)
            wrap(self.canvas, 'Questa è una soluzione possibile. Consultarla non modifica il tuo tentativo e non completa la missione.', pygame.Rect(207, 727, 983, 56), 20, self.c['muted'])
            self.button('scroll:-1', '↑', (1211, 180, 33, 42), active=self.modal_scroll > 0)
            self.button('scroll:1', '↓', (1211, 656, 33, 42), active=self.modal_scroll < self.modal_max)
            text(self.canvas, 'Rotella · PagSu/PagGiù · Home/End', (207, 793), 14, self.c['muted'])
            return
        size = self.state['size'] + 2
        step = font(size).get_linesize() + 6
        content_rect = pygame.Rect(206, top, 995, 767 - top)
        content_lines = lines(self.modal_text, content_rect.width, size)
        self.modal_max = max(0, len(content_lines) * step - content_rect.height)
        self.modal_scroll = max(0, min(self.modal_scroll, self.modal_max))
        clip = self.canvas.get_clip()
        self.canvas.set_clip(content_rect.clip(clip))
        for i, line in enumerate(content_lines):
            y = top + i * step - self.modal_scroll
            if y + step >= top and y < content_rect.bottom:
                text(self.canvas, line, (content_rect.x, y), size, self.c['text'])
        self.canvas.set_clip(clip)
        self.button('scroll:-1', '↑', (1211, 220, 33, 42), active=self.modal_scroll > 0)
        self.button('scroll:1', '↓', (1211, 714, 33, 42), active=self.modal_scroll < self.modal_max)
        text(self.canvas, 'Rotella · PagSu/PagGiù · Home/End', (207, 793), 14, self.c['muted'])
        text(self.canvas, f'{round(self.modal_scroll / self.modal_max * 100) if self.modal_max else 100}%', (1230, 793), 14, self.c['muted'], anchor='topright')

    def draw(self):
        self.buttons = []
        stars(self.canvas, self.c, self.time)
        if self.page == 'home':
            self.draw_home()
        elif self.page == 'catalog':
            self.draw_catalog()
        elif self.page == 'settings':
            self.draw_settings()
        elif self.page == 'quiz':
            self.draw_quiz()
        elif self.page in ('flight', 'briefing'):
            self.draw_activity()
        elif self.page == 'logic':
            self.draw_logic()
        else:
            self.code_rect = pygame.Rect(742, 288, 658, 293)
            self.draw_lab()
        text(self.canvas, 'Realizzato dal Prof. Barillà Francesco', (40, 880), 14, self.c['muted'], anchor='midleft')
        text(self.canvas, self.notice or 'OFFLINE · LE SCELTE SI IMPARANO PROVANDO', (1400, 880), 13, self.c['muted'], anchor='midright')
        if self.modal:
            self.draw_modal()
        cursor = pygame.SYSTEM_CURSOR_HAND if any(active and rect.collidepoint(self.pointer) for _, rect, active in self.buttons) else pygame.SYSTEM_CURSOR_IBEAM if self.page == 'lab' and self.mode == 'game' and not self.easy and self.code_rect.collidepoint(self.pointer) and not self.modal else pygame.SYSTEM_CURSOR_ARROW
        try:
            pygame.mouse.set_cursor(cursor)
        except pygame.error:
            pass
        width, height = self.screen.get_size()
        scale = min(width / SIZE[0], height / SIZE[1])
        size = round(SIZE[0] * scale), round(SIZE[1] * scale)
        self.screen.fill('#000000')
        self.screen.blit(pygame.transform.smoothscale(self.canvas, size), ((width - size[0]) // 2, (height - size[1]) // 2))

    def action(self, key):
        if self.activity_action(key):
            return
        if key == 'close':
            self.modal = None
        elif key.startswith('lesson:'):
            self.lesson(key.split(':', 1)[1])
        elif key == 'help':
            self.open_text('Come si gioca', HOW_TO_PLAY)
        elif key == 'hint':
            self.hint_level = min(3, self.hint_level + 1)
            self.open_text(f'Suggerimento {self.hint_level}/3', '\n\n'.join(self.mission.hints[:self.hint_level]))
        elif key == 'solution':
            self.solution_editor.set(self.activity_code if self.page in ('flight', 'briefing') else self.mission.solution(self.language))
            self.open_text('Una soluzione possibile · ' + self.language, '', 'solution')
        elif key == 'feedback':
            self.open_text('Il perché del risultato', self.feedback)
        elif key == 'trace_details' and self.frame:
            state_text = '\n'.join(f'Riga {line}: {status}' for line, status in self.frame.statuses)
            self.open_text('Leggi il passo della decisione', self.frame.title + '\n\n' + self.frame.message + '\n\n' + state_text + '\n\nAzioni finora: ' + describe(self.frame.actions))
        elif key.startswith('scroll:'):
            self.modal_scroll += int(key.split(':')[1]) * 250
        elif key.startswith('slot:'):
            self.slot_index = int(key.split(':')[1])
            self.open_text(self.mission.slots[self.slot_index].label, '', 'slot')
        elif key.startswith('choose:'):
            self.choices[self.slot_index] = int(key.split(':')[1])
            self.modal = None
            self.sync_blocks()
            self.persist()
        elif key == 'view':
            self.code_view = not self.code_view
        elif key.startswith('block:'):
            self.block_scroll += int(key.split(':')[1]) * 144
        elif key.startswith('mode:'):
            self.persist()
            self.mode, self.page, self.filter = key.split(':')[1], 'catalog', 'Tutte'
            self.playing = False
            self.catalog_page = 0
        elif key.startswith('filter:'):
            self.filter = key.split(':')[1]
            self.catalog_page = 0
        elif key.startswith('catalog_page:'):
            self.catalog_page += int(key.split(':')[1])
        elif key.startswith('mission:'):
            self.open_activity(key.split(':')[1])
        elif key.startswith('quiz:'):
            self.open_quiz(int(key.split(':')[1]))
        elif key.startswith('lang:'):
            self.set_language(key.split(':')[1])
        elif key.startswith('diff:'):
            self.set_difficulty(key.split(':')[1])
        elif key.startswith('theme:'):
            self.state['theme'] = key.split(':')[1]
            self.c = palette(self.state['theme'])
            self.persist()
        elif key.startswith('size:'):
            self.state['size'] = int(key.split(':')[1])
            self.persist()
        elif key.startswith('speed:'):
            self.state['speed'] = float(key.split(':')[1])
            self.persist()
        elif key in ('home', 'catalog', 'settings', 'return'):
            self.persist()
            self.playing = False
            if key == 'settings':
                if self.page != 'settings':
                    self.return_page = self.page
                self.page = 'settings'
            elif key == 'return':
                self.page = self.return_page
            else:
                self.page = key
        elif key.startswith('case:'):
            self.case_index = (self.case_index + int(key.split(':')[1])) % len(self.mission.cases)
            self.extra_case = None
            self.invalidate()
        elif key == 'try':
            current = self.case_index
            self.persist()
            self.page = 'catalog'
            self.mode = 'game'
            self.open_mission(self.mission.key)
            self.case_index = current
        elif key == 'run':
            if self.playing:
                self.playing = False
            elif self.frames and self.frame_index < len(self.frames) - 1:
                self.playing = True
            else:
                self.start_trace()
        elif key == 'step':
            self.playing = False
            if not self.frames:
                self.start_trace(False)
            self.advance()
            self.motion = 1
        elif key == 'back':
            self.playing, self.motion = False, 1
            self.frame_index = max(0, self.frame_index - 1)
            self.follow_line()
        elif key == 'restart':
            self.invalidate(clear_feedback=False)
        elif key == 'verify':
            self.verify()
        elif key.startswith('answer:'):
            self.quiz_choice = int(key.split(':')[1])
        elif key == 'check_answer':
            self.verify_quiz()
        elif key == 'quiz_next':
            self.open_quiz((self.quiz_index + 1) % len(QUIZZES))

    def event(self, event):
        if event.type == pygame.QUIT:
            self.persist()
            self.alive = False
            return
        if event.type == pygame.VIDEORESIZE and not self.fullscreen:
            self.screen = pygame.display.set_mode((max(960, event.w), max(600, event.h)), pygame.RESIZABLE)
        if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            self.pointer = self.logical(event.pos)
        if self.logic_event(event):
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.pressed = next((key for key, rect, active in reversed(self.buttons) if active and rect.collidepoint(self.pointer)), None)
            if not self.modal and self.page == 'lab' and self.mode == 'game' and not self.easy:
                if self.code_rect.collidepoint(self.pointer):
                    self.editor.click(self.pointer, bool(pygame.key.get_mods() & pygame.KMOD_SHIFT))
                else:
                    self.editor.focus = False
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            target = next((key for key, rect, active in reversed(self.buttons) if active and rect.collidepoint(self.pointer)), None)
            if target and target == self.pressed:
                self.action(target)
            self.pressed = None
        if event.type == pygame.MOUSEWHEEL:
            if self.modal:
                self.modal_scroll -= event.y * 82
            elif self.page == 'lab' and self.easy and not self.code_view and self.block_rect.collidepoint(self.pointer):
                self.block_scroll -= event.y * 64
            elif self.page in ('lab', 'quiz') and self.code_rect.collidepoint(self.pointer):
                if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    self.editor.xscroll = max(0, self.editor.xscroll - event.y * 5)
                else:
                    self.editor.scroll = max(0, self.editor.scroll - event.y * 3)
        editable = not self.modal and self.page == 'lab' and self.mode == 'game' and not self.easy and self.editor.focus
        if event.type == pygame.TEXTINPUT and editable:
            if self.editor.replace(event.text):
                self.invalidate()
                self.persist()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                if not self.fullscreen:
                    self.window_size = self.screen.get_size()
                    self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                else:
                    self.screen = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
                self.fullscreen = not self.fullscreen
            elif event.key == pygame.K_ESCAPE:
                self.action('close' if self.modal else 'return' if self.page == 'settings' else 'home')
            elif self.modal and event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_PAGEUP, pygame.K_PAGEDOWN, pygame.K_HOME, pygame.K_END):
                self.modal_scroll += {pygame.K_UP: -65, pygame.K_DOWN: 65, pygame.K_PAGEUP: -410, pygame.K_PAGEDOWN: 410, pygame.K_HOME: -100000, pygame.K_END: 100000}[event.key]
            elif editable:
                if self.editor.key(event):
                    self.invalidate()
                    self.persist()
            elif not self.modal and self.page in ('flight', 'briefing') and pygame.K_a <= event.key <= pygame.K_d:
                self.choose_order(event.key - pygame.K_a)
            elif event.key == pygame.K_TAB:
                enabled = [key for key, _, active in self.buttons if active]
                if enabled:
                    index = enabled.index(self.focus) if self.focus in enabled else -1
                    self.focus = enabled[(index + (-1 if event.mod & pygame.KMOD_SHIFT else 1)) % len(enabled)]
                    rect = next(rect for key, rect, _ in self.buttons if key == self.focus)
                    self.pointer = rect.center
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE) and self.focus:
                if any(key == self.focus and active for key, _, active in self.buttons):
                    self.action(self.focus)

    def update(self, dt):
        self.time += dt
        self.shake = max(0, self.shake - dt * 2)
        self.update_activities(dt)
        if not self.modal and self.page in ('lab', 'quiz') and self.playing:
            self.motion = min(1, self.motion + dt * 3 * self.state['speed'])
            self.elapsed += dt
            if self.elapsed >= 1.1 / self.state['speed']:
                self.elapsed = 0
                self.advance()


def smoke(report, screenshot_dir=None):
    app = App(pygame.display.set_mode((1280, 800)), saving=False)
    shots = Path(screenshot_dir) if screenshot_dir else None
    if shots:
        shots.mkdir(parents=True, exist_ok=True)
    def capture(name):
        app.draw()
        if shots:
            pygame.image.save(app.canvas, str(shots / (name + '.png')))
    capture('01-home')
    checks = 0
    for theme in THEMES:
        app.state['theme'], app.c = theme, palette(theme)
        for language in LANGUAGES:
            app.state['language'] = language
            app.mode = 'learn'
            for mission in MISSIONS:
                app.open_mission(mission.key)
                app.start_trace(False)
                app.frame_index = min(2, len(app.frames) - 1)
                app.draw()
                assert app.frames[-1].actions == mission.rule(app.case.data)
                checks += 1
    app.state['theme'], app.c = 'Notte', palette('Notte')
    app.state['language'] = 'Python'
    app.page, app.mode = 'catalog', 'game'
    capture('02-missioni')
    app.mode = 'learn'
    app.open_mission('annidato')
    app.start_trace(False)
    app.frame_index = 1
    capture('03-impara')
    app.mode = 'game'
    app.open_mission('turno')
    capture('04-blocchi')
    app.choices = app.mission.correct_choices()
    app.sync_blocks()
    app.verify()
    capture('05-verifica')
    app.lesson('Equivoci')
    capture('06-equivoci')
    app.modal_scroll = app.modal_max
    app.draw()
    app.modal = None
    app.open_quiz(4)
    app.quiz_choice = app.quiz.answer
    app.verify_quiz()
    app.start_trace(False)
    app.frame_index = 1
    capture('07-previsione')
    app.action('settings')
    capture('08-impostazioni')
    app.action('return')
    app.mode = 'learn'
    app.open_mission('turno')
    app.set_language('C')
    app.action('solution')
    capture('09-soluzione')
    app.modal = None
    app.start_trace(False)
    app.frame_index = 1
    app.state['theme'], app.c = 'Giorno', palette('Giorno')
    capture('10-codice-c')
    app.state['theme'], app.c = 'Notte', palette('Notte')
    app.set_language('Python')
    app.mode = 'learn'
    app.open_activity('annidato')
    capture('11-impara-facendo')
    app.mode = 'game'
    app.set_difficulty('Facile')
    app.open_activity('campi_xor')
    app.activity_round = 3
    app.prepare_activity_case()
    capture('12-turno-dei-droni')
    app.choose_order(app.activity_options.index(app.mission.rule(app.case.data)))
    app.update(1)
    capture('13-portello-in-azione')
    app.action('logic')
    app.action('operator:XOR')
    app.action('representation:Campi')
    app.logic_fields[0].set('0')
    app.logic_fields[1].set('MARTE')
    capture('14-banco-logico')
    app.action('representation:0/1')
    app.action('operator:AND')
    capture('15-binari')
    app.action('representation:Booleani')
    app.action('operator:NOT')
    capture('16-not')
    app.action('mode:quiz')
    app.catalog_page = 2
    capture('17-nuovi-equivoci')
    Path(report).parent.mkdir(parents=True, exist_ok=True)
    Path(report).write_text(json.dumps(dict(ok=True, render_checks=checks, activity_views=7, missions=len(MISSIONS), quizzes=len(QUIZZES), languages=list(LANGUAGES))), encoding='utf-8')


def main():
    pygame.init()
    pygame.display.set_caption(TITLE)
    pygame.display.set_icon(icon())
    pygame.key.set_repeat(450, 35)
    if '--smoke-test' in sys.argv:
        index = sys.argv.index('--smoke-test')
        screenshots = sys.argv[sys.argv.index('--screenshots') + 1] if '--screenshots' in sys.argv else None
        smoke(sys.argv[index + 1], screenshots)
    else:
        app = App(pygame.display.set_mode((1280, 800), pygame.RESIZABLE))
        clock = pygame.time.Clock()
        app.draw()
        while app.alive:
            dt = min(.1, clock.tick(60) / 1000)
            for event in pygame.event.get():
                app.event(event)
            app.update(dt)
            app.draw()
            pygame.display.flip()
    pygame.quit()


if __name__ == '__main__':
    main()
