"""Learner-first game panels and an observation view separate from writing."""
import pygame
from engine import LANGUAGES, describe
from guidance import RULES, first_gap, inline_example, objective_for, writing_task
from missions import DIFFICULTIES
from scene import flight_scene
from ui import font, mix, panel, text, wrap


def action_summary(actions):
    return describe(actions[:2]) + (f' … (+{len(actions) - 2} azioni)' if len(actions) > 2 else '')


class GuidedUI:
    def fitted(self, label, rect, size=22, color=None, mono=False):
        rect = pygame.Rect(rect)
        while size > 16 and font(size, True, mono).size(str(label))[0] > rect.width:
            size -= 1
        clip = self.canvas.get_clip()
        self.canvas.set_clip(rect.clip(clip))
        text(self.canvas, label, rect.midleft, size, color or self.c['text'], True, 'midleft', mono)
        self.canvas.set_clip(clip)

    def task_header(self):
        self.header('Impara: scegli una risposta e osserva' if self.mode == 'learn' else 'Gioca: scegli, completa oppure programma')
        text(self.canvas, self.mission.title, (40, 104), 29, self.c['text'], True)
        wrap(self.canvas, objective_for(self.mission, self.language), pygame.Rect(42, 148, 1354, 53), 19, self.c['text'])
        for i, language in enumerate(LANGUAGES):
            self.button('lang:' + language, language, (40 + i * 128, 210, 119, 35), selected=self.language == language, size=16)
        if self.mode == 'game':
            for i, (difficulty, verb) in enumerate(zip(DIFFICULTIES, ('scegli', 'completa', 'scrivi'))):
                self.button('diff:' + difficulty, difficulty + ' · ' + verb, (755 + i * 217, 210, 211, 35), selected=self.difficulty == difficulty, size=16)
        else:
            text(self.canvas, 'Leggi i dati → scegli una risposta → osserva il perché', (748, 220), 17, self.c['muted'])

    def draw_game_lab(self):
        self.task_header()
        s, c = self.canvas, self.c
        panel(s, pygame.Rect(40, 260, 850, 591), c['panel'], radius=16)
        panel(s, pygame.Rect(910, 260, 490, 591), c['panel'], radius=16)
        label = '1  SCEGLI NEI BLOCCHI' if self.easy else '1  COMPLETA IL CODICE' if self.difficulty == 'Medio' else '1  SCRIVI LA REGOLA'
        text(s, label, (57, 282), 18, c['mint'], True)
        if self.easy:
            missing = sum(item < 0 for item in self.choices)
            self.button('next_slot', 'Prossimo blocco vuoto', (621, 274, 249, 38), active=bool(missing), primary=bool(missing), size=16)
            wrap(s, 'Fai clic su ogni blocco e scegli una condizione o un’azione.\nPoi premi Controlla i blocchi: la regola deve funzionare con tutti i dati.', pygame.Rect(57, 325, 812, 65), 19, c['text'])
            text(s, f'{len(self.choices) - missing}/{len(self.choices)} blocchi compilati · scorri per raggiungere quelli in basso', (58, 394), 15, c['muted'])
            self.block_rect = pygame.Rect(56, 425, 815, 309)
            if not self.code_view:
                self.draw_blocks()
            else:
                self.code_rect = self.block_rect.copy()
                self.editor.draw(s, self.code_rect, c, readonly=True, size=self.state['size'] + 2)
            self.button('view', 'Torna ai blocchi' if self.code_view else 'Vedi il codice dei blocchi', (56, 749, 399, 35), size=16)
            self.button('block:-1', 'Scorri ↑', (467, 749, 196, 35), active=not self.code_view and self.block_scroll > 0, size=16)
            self.button('block:1', 'Scorri ↓', (675, 749, 196, 35), active=not self.code_view and len(self.choices) * 72 > self.block_rect.height, size=16)
        else:
            gap = first_gap(self.editor.value, self.language)
            self.button('focus_code', 'Completa i ???' if gap else 'Scrivi qui', (639, 274, 231, 38), primary=True, size=18)
            title, task = writing_task(self.mission, self.editor.value, self.language)
            wrap(s, title + '\n' + task, pygame.Rect(57, 325, 812, 66), 18, c['text'])
            status = 'Stai scrivendo · Invio va a capo · Tab rientra · Ctrl+Invio controlla' if self.editor.focus else (
                f'Da completare: riga {gap.line} · premi Completa i ???' if gap else 'Zona di scrittura · ' + self.language)
            text(s, status, (58, 396), 15, c['accent'] if gap or self.editor.focus else c['muted'])
            self.code_rect = pygame.Rect(56, 424, 815, 262)
            self.editor.draw(s, self.code_rect, c, error=self.error_line, tick=self.time, size=self.state['size'] + 2)
            if not self.editor.value.strip() and not self.editor.focus:
                text(s, 'Scrivi qui la tua regola', (79, 460), 27, c['muted'], True)
                wrap(s, 'Premi Scrivi qui e usa la tastiera.\nUsa i nomi dei sensori forniti dal gioco.', pygame.Rect(80, 508, 740, 72), 21, c['muted'])
            caption, sample = inline_example(self.mission, self.editor.value, self.language)
            text(s, caption, (58, 701), 15, c['blue'], True)
            for i, line in enumerate(sample):
                self.fitted(line, (58, 728 + i * 27, 810, 27), 21, mono=True)
        self.button('writing_help', 'Consegna e comandi' if self.easy else 'Cosa devo scrivere?', (56, 799, 237, 37), size=17)
        self.button('trace_view', 'Guarda l’esecuzione', (305, 799, 325, 37), size=17)
        self.button('solution', 'Mostra una soluzione', (642, 799, 229, 37), size=16)
        self.draw_rule_result()

    def draw_rule_result(self):
        s, c = self.canvas, self.c
        text(s, '2  CONTROLLA IL RISULTATO', (931, 282), 18, c['mint'], True)
        success = self.review is not None and self.review.success
        if self.review or self.feedback:
            self.fitted('Missione completata' if success else 'Da correggere: riprova', (932, 324, 450, 36), 26, c['mint'] if success else c['danger'])
            if self.review and self.review.case:
                message = f'{self.review.passed}/{self.review.total} casi riusciti. La regola sbaglia con i dati qui sotto. Confronta gli ordini e correggi il codice.'
            else:
                message = self.feedback
            wrap(s, message, pygame.Rect(933, 369, 447, 107), 18, c['text'])
            self.button('feedback', 'Leggi il perché', (1205, 479, 175, 30), size=15)
        else:
            self.fitted('Che cosa deve decidere?', (932, 324, 450, 36), 25)
            wrap(s, '\n'.join(f'{i+1}. {rule}' for i, rule in enumerate(RULES[self.mission.key])), pygame.Rect(933, 367, 447, 133), 18, c['text'])
        self.button('case:-1', '‹', (932, 518, 34, 30), size=23)
        case_label = 'Caso da correggere' if self.extra_case else f'Dati del gioco · {self.case_index + 1}/{len(self.mission.cases)}'
        text(s, case_label, (980, 522), 17, c['text'], True)
        self.button('case:1', '›', (1346, 518, 34, 30), size=23)
        self.draw_data(558, 448, 932)
        expected = self.mission.rule(self.case.data)
        text(s, 'ORDINI RICHIESTI, IN ORDINE', (933, 635), 14, c['blue'], True)
        wrap(s, action_summary(expected), pygame.Rect(933, 657, 447, 50), 19, c['text'], True)
        if self.review or self.error_line:
            actual = self.frames[-1].actions if self.frames else ()
            text(s, 'IL TUO CODICE HA PRODOTTO', (933, 711), 14, c['mint'] if success else c['danger'], True)
            wrap(s, action_summary(actual) if not self.error_line else 'Codice da completare o correggere', pygame.Rect(933, 733, 447, 39), 17, c['text'], True)
        else:
            text(s, 'Il controllo prova tutti i dati della missione.', (933, 743), 16, c['muted'])
        label = 'Prova la regola con 5 droni' if success else 'Controlla i blocchi' if self.easy else 'Controlla il mio codice'
        self.button('test_flight' if success else 'verify', label, (932, 785, 448, 49), primary=True, size=21)

    def draw_game_trace(self):
        s, c = self.canvas, self.c
        text(s, 'Osserva i passi. Per verificare la missione torna al gioco e premi Controlla.', (204, 166), 19, c['muted'])
        self.trace_editor.draw(s, pygame.Rect(205, 214, 599, 282), c, readonly=True,
                               active=self.frame.line if self.frame else 0, error=self.error_line, size=self.state['size'] + 2)
        text(s, 'Rotella: su/giù · Shift + rotella: destra/sinistra', (207, 192), 14, c['muted'])
        self.draw_scene((822, 214, 410, 282))
        frame = self.frame
        title = f'Passo {self.frame_index + 1}/{len(self.frames)} · {frame.title}' if frame else 'Prima correggi il codice'
        self.fitted(title, (207, 518, 1005, 36), 26)
        wrap(s, frame.message if frame else self.feedback, pygame.Rect(207, 568, 1004, 82), 22, c['text'])
        if frame:
            states = ' · '.join(f'Riga {line}: {status}' for line, status in frame.statuses)
            wrap(s, states, pygame.Rect(207, 656, 1004, 55), 17, c['muted'])
        for i, (key, label, active) in enumerate((('run', 'Pausa' if self.playing else 'Esegui i passi', bool(frame)),
                ('step', 'Passo successivo', bool(frame) and self.frame_index + 1 < len(self.frames)),
                ('back', 'Passo precedente', bool(frame) and self.frame_index > 0))):
            self.button(key, label, (207 + i * 340, 740, 325, 47), active=active, primary=key == 'step', size=20)

    def draw_activity(self):
        guided = self.page == 'briefing'
        self.task_header()
        s, c = self.canvas, self.c
        panel(s, pygame.Rect(40, 260, 850, 591), c['panel'], radius=16)
        panel(s, pygame.Rect(910, 260, 490, 591), c['panel'], radius=16)
        text(s, '1  LEGGI I DATI DEL DRONE', (57, 282), 18, c['mint'], True)
        counter = f'Esperimento {self.activity_round + 1}/3' if guided else f'Drone {self.activity_round + 1}/5'
        text(s, counter, (869, 286), 17, c['accent'], True, 'topright')
        self.draw_data(328, 812, 57)
        text(s, 'Questi sono i dati da usare. Scegli una risposta a destra →', (59, 401), 18, c['text'])
        flight_scene(s, pygame.Rect(57, 439, 814, 220), c, self.time, self.activity_options,
                     self.activity_selected, self.activity_progress, self.shake, self.activity_round + 1)
        frame = self.frame
        title = 'COSA FA IL COMPUTER' if frame else 'COME RAGIONARE'
        text(s, title, (58, 680), 16, c['blue'], True)
        message = frame.message if frame else 'Leggi la regola in alto e applicala a questi dati. Una risposta può contenere più ordini: verranno eseguiti da sinistra a destra.'
        if self.activity_complete:
            message = self.mission.concept
        wrap(s, message, pygame.Rect(58, 709, 813, 58 if frame and not self.activity_complete else 76), 19, c['text'])
        if frame and not self.activity_complete:
            states = ' · '.join(f'Riga {line}: {status}' for line, status in frame.statuses)
            self.fitted(states, (58, 773, 812, 21), 14, c['muted'])
        self.button('activity_why', 'Spiegami il perché', (56, 799, 249, 37), size=17)
        self.button('solution', 'Guarda il codice', (317, 799, 253, 37), size=17)
        self.button('activity_code', 'Laboratorio del codice', (582, 799, 289, 37), size=17)
        text(s, '2  SCEGLI UNA RISPOSTA', (932, 282), 18, c['mint'], True)
        wrap(s, 'Quali ordini eseguirà la stazione?', pygame.Rect(933, 325, 447, 64), 26, c['text'], True)
        for i, outcome in enumerate(self.activity_options):
            label = chr(65+i) + ' · ' + (describe(outcome) if outcome else 'Nessuna azione: resta fermo')
            selected = self.activity_attempt == i
            self.button('order:' + str(i), label, (932, 407 + i * 62, 448, 53), active=not self.activity_correct and not self.activity_complete,
                        selected=selected, size=18)
            if selected:
                pygame.draw.rect(s, c['mint'] if self.activity_correct else c['danger'], pygame.Rect(932, 407 + i * 62, 448, 53), 3, border_radius=10)
        if self.activity_complete:
            heading = 'Esperimenti completati' if guided else 'Turno completato'
            message = 'Hai applicato la regola a tutti i casi del turno. Ora puoi provarla nel codice.'
        elif self.activity_correct:
            heading = 'Corretto'
            message = 'La scelta è corretta, anche se il drone resta fermo.' if not self.mission.rule(self.case.data) or all(x in ('attendi', 'nega') for x in self.mission.rule(self.case.data)) else 'La scelta è corretta. Osserva la decisione del computer, poi continua.'
        elif self.activity_attempt is not None:
            heading = 'Da rivedere: riprova'
            message = self.mission.hints[min(self.activity_mistakes - 1, 2)]
        else:
            heading = 'Fai clic su una risposta'
            message = 'Puoi usare anche i tasti A–D. Se sbagli, ricevi un indizio e puoi scegliere di nuovo.'
        color = c['mint'] if self.activity_correct or self.activity_complete else c['danger'] if self.activity_attempt is not None else c['text']
        text(s, heading, (933, 668), 23, color, True)
        wrap(s, message, pygame.Rect(933, 706, 447, 69), 18, c['text'])
        if self.activity_complete:
            self.button('activity_play' if guided else 'activity_again', 'Ora pilota tu' if guided else 'Rigioca il turno', (932, 785, 448, 49), primary=True, size=21)
        else:
            ready = self.activity_correct and self.activity_progress >= 1 and not self.playing
            paused = self.activity_correct and not self.playing and (self.activity_progress < 1 or self.frame_index < len(self.frames) - 1)
            label = 'Prossimo esperimento' if guided else 'Prossimo drone'
            if self.activity_round == len(self.activity_cases) - 1:
                label = 'Concludi gli esperimenti' if guided else 'Completa il turno'
            if not self.activity_correct:
                label = 'Prima scegli una risposta'
            elif self.playing:
                label = 'Osserva la decisione…'
            self.button('activity_resume' if paused else 'next_drone', 'Riprendi la decisione' if paused else label, (932, 785, 448, 49), active=ready or paused, primary=True, size=20)
