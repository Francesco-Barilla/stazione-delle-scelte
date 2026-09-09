"""Truth semantics and complete learner journeys, including interruptions."""
import os
from pathlib import Path
import tempfile
import unittest

os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame

from engine import CodeError, LANGUAGES, generate, parse, run
from logic import OPERATORS, REPRESENTATIONS, compute, normalize, truth_table
from main import App
from missions import BY_KEY, Case, DEFAULT_DATA, MISSIONS
from ui import THEMES, font, palette


class LogicTests(unittest.TestCase):
    def test_truth_tables_and_representations_agree_with_independent_oracle(self):
        expected = {'AND': [False, False, False, True], 'OR': [False, True, True, True],
                    'XOR': [False, True, True, False], 'NOT': [True, False]}
        for operator, outputs in expected.items():
            self.assertEqual([row[2] for row in truth_table(operator)], outputs)
        for representation, examples in [('Booleani', [False, True]), ('0/1', [0, 1]), ('Campi', ['', '0'])]:
            for operator in ('AND', 'OR', 'XOR'):
                results = [compute(operator, normalize(a, representation), normalize(b, representation)) for a in examples for b in examples]
                self.assertEqual(results, expected[operator])
        for value in ('0', 'false', ' ', '\t', '🌙'):
            self.assertTrue(normalize(value, 'Campi'))
            self.assertTrue(Case('Presenza', {'testo_a': value}).data['campo_a'])
        self.assertFalse(Case('Vuoto', {'testo_a': ''}).data['campo_a'])
        for value in (-1, 2, '0', True, None):
            with self.assertRaises(ValueError):
                normalize(value, '0/1')

    def test_xor_evaluates_both_and_preserves_native_types_and_precedence(self):
        source = 'if badge ^ autorizzato:\n    apri()\nelse:\n    attendi()\n'
        for language in LANGUAGES:
            for a in (False, True):
                for b in (False, True):
                    frames = run(parse(generate(parse(source, 'Python'), language), language), DEFAULT_DATA | {'badge': a, 'autorizzato': b}, language)
                    self.assertEqual(frames[-1].actions, ('apri',) if a != b else ('attendi',))
                    self.assertFalse(any('Cortocircuito' in f.message for f in frames))
            code = 'if 2 ^ 1 == 2:\n    apri()\n' if language == 'Python' else 'if (2 ^ 1 == 2) { apri(); }'
            if language == 'Java':
                with self.assertRaises(CodeError):
                    parse(code, language)  # Java parses 2 ^ false, which mixes types.
            else:
                self.assertEqual(run(parse(code, language), DEFAULT_DATA, language)[-1].actions, () if language == 'Python' else ('apri',))
        for code in ('if (segnale_a ^ segnale_b) { parti(); }', 'if (badge ^ 1) { apri(); }'):
            with self.assertRaises(CodeError):
                parse(code, 'Java')
        code = 'if ((segnale_a ^ segnale_b) == 1) { parti(); }'
        self.assertEqual(run(parse(code, 'Java'), DEFAULT_DATA | {'segnale_a': 1}, 'Java')[-1].actions, ('parti',))


class ActivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((1440, 900))

    @classmethod
    def tearDownClass(cls):
        font.cache_clear()
        pygame.quit()

    def setUp(self):
        self.app = App(self.screen, saving=False, state_path=Path(tempfile.gettempdir()) / 'nonexistent-selection-activity-test.json')

    def finish_animation(self):
        for _ in range(160):
            self.app.update(.1)
            if not self.app.playing:
                return
        self.fail('Animation did not finish')

    def test_all_missions_can_complete_a_five_drone_round_in_every_language(self):
        app = self.app
        app.mode = 'game'
        for language in LANGUAGES:
            app.set_language(language)
            for mission in MISSIONS:
                app.open_activity(mission.key)
                self.assertEqual(app.page, 'flight')
                key = app.key()
                for index in range(5):
                    expected = mission.rule(app.case.data)
                    correct = app.activity_options.index(expected)
                    wrong = (correct + 1) % len(app.activity_options)
                    app.choose_order(wrong)
                    self.assertFalse(app.activity_correct)
                    self.assertEqual(app.activity_progress, 0)
                    app.choose_order(correct)
                    self.assertEqual(app.frames[-1].actions, expected)
                    app.draw()
                    app.next_drone()  # Cannot skip observation while flying.
                    self.assertEqual(app.activity_round, index)
                    self.finish_animation()
                    self.assertNotIn(key, app.state['completed'])
                    app.next_drone()
                self.assertTrue(app.activity_complete)
                self.assertIn(key, app.state['completed'])

    def test_lessons_have_three_predictions_and_do_not_award_game_completion(self):
        app = self.app
        app.open_activity('annidato')
        self.assertEqual(app.page, 'briefing')
        for index in range(3):
            app.choose_order(app.activity_options.index(app.mission.rule(app.case.data)))
            if index == 0:
                self.assertIn('NON VALUTATA', app.activity_details)
            self.finish_animation()
            app.next_drone()
        self.assertTrue(app.activity_complete)
        self.assertFalse(app.state['completed'])
        app.action('activity_play')
        self.assertEqual((app.page, app.mode, app.activity_round), ('flight', 'game', 0))

    def test_pause_modal_bench_settings_and_resume_keep_the_current_drone(self):
        app = self.app
        app.mode = 'game'
        app.open_activity('turno')
        app.choose_order(app.activity_options.index(app.mission.rule(app.case.data)))
        app.update(.2)
        progress, frames = app.activity_progress, app.frames
        for open_key, close_key in [('activity_why', 'close'), ('logic', 'logic_back'), ('settings', 'return')]:
            app.action(open_key)
            app.update(10)
            app.action(close_key)
            self.assertEqual(app.activity_progress, progress)
            self.assertIs(app.frames, frames)
            app.draw()
            self.assertTrue(next(active for key, _, active in app.buttons if key == 'activity_resume'))
        app.action('activity_resume')
        self.finish_animation()
        app.next_drone()
        self.assertEqual(app.activity_round, 1)

    def test_bench_language_does_not_change_or_overwrite_a_mission_draft(self):
        app = self.app
        app.mode = 'game'
        app.set_difficulty('Difficile')
        app.open_mission('campo')
        app.editor.set('# un tentativo da conservare')
        app.action('logic')
        app.action('logic_lang:Java')
        app.action('representation:Campi')
        app.action('operator:XOR')
        app.draw()
        app.logic_fields[0].focus = True
        app.event(pygame.event.Event(pygame.TEXTINPUT, text='0'))
        self.assertEqual(app.logic_values(), (True, True))
        app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_BACKSPACE, mod=0))
        self.assertEqual(app.logic_values(), (False, True))
        app.action('logic_back')
        self.assertEqual(app.language, 'Python')
        self.assertEqual(app.editor.value, '# un tentativo da conservare')

    def test_changing_language_restarts_flight_and_difficulty_opens_editor(self):
        app = self.app
        app.mode = 'game'
        app.open_activity('campi_xor')
        app.choose_order(app.activity_options.index(app.mission.rule(app.case.data)))
        self.finish_animation()
        app.next_drone()
        app.set_language('Java')
        self.assertEqual(app.activity_round, 0)
        self.assertFalse(app.activity_correct)
        self.assertIn('if (', app.activity_code)
        app.set_difficulty('Medio')
        self.assertEqual(app.page, 'lab')
        self.assertIn('???', app.editor.value)

    def test_catalog_pagination_and_new_views_fit_in_every_theme(self):
        app = self.app
        canvas = pygame.Rect(0, 0, 1440, 900)
        for theme in THEMES:
            app.c = palette(theme)
            for mode in ('learn', 'game', 'quiz'):
                app.action('mode:' + mode)
                seen = set()
                for page in range(3):
                    app.catalog_page = page
                    app.draw()
                    for key, rect, _ in app.buttons:
                        self.assertTrue(canvas.contains(rect))
                        if key.startswith(('mission:', 'quiz:')):
                            seen.add(key)
                self.assertEqual(len(seen), 20)
            app.mode = 'game'
            app.open_activity('indipendenti')
            app.draw()
            app.action('logic')
            for representation in REPRESENTATIONS:
                app.logic_representation = representation
                for operator in OPERATORS:
                    app.logic_operator = operator
                    for language in LANGUAGES:
                        app.logic_language = language
                        app.draw()
                        self.assertTrue(all(canvas.contains(rect) for _, rect, _ in app.buttons))


if __name__ == '__main__':
    unittest.main()
