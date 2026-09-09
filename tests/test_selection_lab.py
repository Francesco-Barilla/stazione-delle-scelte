import copy
import json
import os
from pathlib import Path
import tempfile
import unittest

os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import pygame
from engine import CodeError, LANGUAGES, MAX_CODE, evaluate, generate, parse, parse_expression, run
from lessons import QUIZZES
from missions import BY_KEY, Case, DEFAULT_DATA, DIFFICULTIES, MISSIONS, validate
from main import App
import storage
from ui import THEMES, font, palette


class InterpreterTests(unittest.TestCase):
    def trace(self, code, language='Python', **values):
        return run(parse(code, language), Case('Test', values).data, language)

    def test_all_solutions_in_every_language_over_complete_domains(self):
        for mission in MISSIONS:
            for language in LANGUAGES:
                with self.subTest(mission=mission.key, language=language):
                    review = validate(mission, mission.solution(language), language)
                    self.assertTrue(review.success, review.message)
                    self.assertEqual(review.passed, review.total)
                    for case in mission.cases:
                        self.assertEqual(self.trace(mission.solution(language), language, **case.values)[-1].actions, mission.rule(case.data))

    def test_wrong_boundary_produces_replayable_counterexample(self):
        mission = BY_KEY['soglia']
        for language in LANGUAGES:
            wrong = mission.solution(language).replace('>= 30', '> 30')
            review = validate(mission, wrong, language)
            self.assertFalse(review.success)
            self.assertEqual(review.case.data['batteria'], 30)
            self.assertEqual(review.expected, ('parti',))
            self.assertEqual(review.actual, ('ricarica',))
            self.assertEqual(review.passed, 100)

    def test_if_independent_and_chain_have_different_actions(self):
        independent = 'if batteria < 20:\n    ricarica()\nif batteria < 60:\n    controlla()\n'
        chain = independent.replace('\nif batteria < 60:', '\nelif batteria < 60:')
        for language in LANGUAGES:
            self.assertEqual(self.trace(generate(parse(independent, 'Python'), language), language, batteria=10)[-1].actions, ('ricarica', 'controlla'))
            frames = self.trace(generate(parse(chain, 'Python'), language), language, batteria=10)
            self.assertEqual(frames[-1].actions, ('ricarica',))
            self.assertIn('NON VALUTATA', dict(frames[-1].statuses).values())
            self.assertEqual(len([f for f in frames if f.kind == 'condition']), 1)

    def test_nested_condition_is_not_falsified_when_skipped(self):
        for language in LANGUAGES:
            frames = self.trace(BY_KEY['annidato'].solution(language), language, badge=False, livello=3)
            conditions = [f for f in frames if f.kind == 'condition']
            self.assertEqual(len(conditions), 1)
            self.assertEqual(conditions[0].title, 'FALSO')
            self.assertEqual(frames[-1].actions, ('nega',))
            self.assertIn('NON VALUTATA', dict(frames[-1].statuses).values())

    def test_boolean_short_circuit_and_inclusive_or(self):
        for language in LANGUAGES:
            for op, data, expected in [('and', {'badge': False, 'autorizzato': True}, ('nega',)), ('or', {'badge': True, 'autorizzato': True}, ('apri',))]:
                source = f'if badge {op} autorizzato:\n    apri()\nelse:\n    nega()\n'
                frames = self.trace(generate(parse(source, 'Python'), language), language, **data)
                self.assertEqual(frames[-1].actions, expected)
                self.assertTrue(any('Cortocircuito' in f.message for f in frames))

    def test_native_not_precedence_and_chained_comparisons(self):
        notes = []
        self.assertFalse(evaluate(parse_expression('10 <= peso <= 20'), DEFAULT_DATA | {'peso': 35}, 'Python', notes))
        for language in ('C', 'JavaScript'):
            frames = self.trace('if (10 <= peso <= 20) { carica(); }', language, peso=35)
            self.assertEqual(frames[-1].actions, ('carica',))
            frames = self.trace('if (!batteria < 30) { parti(); }', language, batteria=50)
            self.assertEqual(frames[-1].actions, ('parti',))
        frames = self.trace('if not batteria < 30:\n    parti()\n', batteria=50)
        self.assertEqual(frames[-1].actions, ('parti',))
        # ! binds before >= in brace languages; Python not binds after >=.
        self.assertEqual(self.trace('if (!batteria >= 30) { parti(); }', 'C', batteria=50)[-1].actions, ())
        self.assertEqual(self.trace('if not batteria >= 30:\n    parti()\n', batteria=0)[-1].actions, ('parti',))
        with self.assertRaises(CodeError):
            parse('if (10 <= peso <= 20) { carica(); }', 'Java')

    def test_java_boolean_condition_and_static_validation(self):
        for code in ('if (batteria) { parti(); }', 'if (false) { if (batteria) { parti(); } }', 'if (badge < 2) { parti(); }', 'if (badge == 1) { parti(); }'):
            with self.assertRaises(CodeError):
                parse(code, 'Java')
        for language in ('C', 'JavaScript'):
            for value, expected in ((0, ()), (-1, ('parti',)), (2, ('parti',))):
                self.assertEqual(self.trace('if (batteria) { parti(); }', language, batteria=value)[-1].actions, expected)

    def test_javascript_strict_equality_is_not_loose_equality(self):
        self.assertEqual(self.trace('if (badge == 1) { apri(); }', 'JavaScript', badge=True)[-1].actions, ('apri',))
        self.assertEqual(self.trace('if (badge === 1) { apri(); }', 'JavaScript', badge=True)[-1].actions, ())
        for language in ('C', 'Java'):
            with self.assertRaises(CodeError):
                parse('if (livello === 1) { apri(); }', language)

    def test_else_binding_and_empty_statement_are_observable(self):
        for language in ('C', 'JavaScript', 'Java'):
            code = 'if (badge) if (livello >= 2) apri(); else accompagna();'
            self.assertEqual(self.trace(code, language, badge=False)[-1].actions, ())
            self.assertEqual(self.trace(code, language, badge=True, livello=0)[-1].actions, ('accompagna',))
            self.assertEqual(self.trace('if (badge); apri();', language, badge=False)[-1].actions, ('apri',))

    def test_dead_required_structure_does_not_win_even_on_same_line(self):
        code = 'if (false) { if (badge) { apri(); } } if (badge && livello >= 2) { apri(); } else if (badge) { accompagna(); } else { nega(); }'
        for language in ('C', 'JavaScript', 'Java'):
            review = validate(BY_KEY['annidato'], code, language)
            self.assertFalse(review.success)
            self.assertEqual(review.passed, review.total)
            self.assertIn('struttura', review.message)

    def test_host_access_and_unsupported_constructs_are_rejected(self):
        for code in ('import os', '__import__("os").system("anything")', 'while True:\n    parti()', 'if badge:\n    print(1)', 'batteria = 100', 'if badge.__class__:\n    parti()', 'if [1]:\n    parti()', 'if (lambda: True)():\n    parti()'):
            with self.assertRaises(CodeError, msg=code):
                parse(code, 'Python')
        for language in ('C', 'JavaScript', 'Java'):
            for code in ('if (batteria = 30) { parti(); }', 'while (true) { parti(); }', 'if (badge) { system(); }', 'if (badge) { apri();', 'if (badge) { apri(); } garbage'):
                with self.assertRaises(CodeError, msg=code):
                    parse(code, language)

    def test_bounded_input_and_comments_keep_real_lines(self):
        with self.assertRaises(CodeError):
            parse('#' + 'x' * MAX_CODE, 'Python')
        for language in ('C', 'JavaScript', 'Java'):
            code = '// header\n/* multiline\n comment */\nif (badge) {\n apri();\n}\n'
            frames = self.trace(code, language, badge=True)
            self.assertEqual([f.line for f in frames if f.kind == 'condition'], [4])
            self.assertEqual([f.line for f in frames if f.kind == 'action'], [5])

    def test_snapshots_do_not_change_and_data_is_readonly(self):
        data = DEFAULT_DATA | {'batteria': 10, 'fragile': True}
        original = data.copy()
        frames = run(parse(BY_KEY['indipendenti'].solution('Python'), 'Python'), data, 'Python')
        self.assertEqual(data, original)
        self.assertEqual(frames[0].actions, ())
        self.assertEqual(frames[-1].actions, ('ricarica', 'proteggi'))

    def test_quiz_counterexamples_run_consistently_in_all_languages(self):
        expected = [(), ('ricarica',), ('ricarica',), ('ricarica', 'controlla'), ('ricarica',), ('corsia_rapida',), ('apri',), ('allarme',), ('carica',), ('nega',), (), ('nega', 'registra')]
        expected += [('attendi',), ('attendi',), ('nega',), ('ricarica',), ('registra',), ('registra',), ('attendi',), ('attendi',)]
        self.assertEqual(len(QUIZZES), len(expected))
        for quiz, actions in zip(QUIZZES, expected):
            for language in LANGUAGES:
                with self.subTest(quiz=quiz.key, language=language):
                    self.assertEqual(self.trace(quiz.source(language), language, **quiz.case.values)[-1].actions, actions)


class InterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((1280, 800))

    @classmethod
    def tearDownClass(cls):
        font.cache_clear()
        pygame.quit()

    def setUp(self):
        self.app = App(self.screen, saving=False, state_path=Path(tempfile.gettempdir()) / 'nonexistent-selection-test-state.json')

    def test_learning_to_game_does_not_copy_solution_over_draft(self):
        app = self.app
        app.mode = 'game'
        app.state['difficulty'] = 'Difficile'
        app.open_mission('soglia')
        app.editor.set('# tentativo non finito\nif batteria >')
        app.action('home')
        app.action('mode:learn')
        app.open_mission('soglia')
        app.action('case:1')
        app.action('try')
        self.assertEqual(app.editor.value, '# tentativo non finito\nif batteria >')
        self.assertEqual(app.case_index, 1)
        self.assertFalse(app.state['completed'])

    def test_language_and_difficulty_drafts_are_independent(self):
        app = self.app
        app.mode = 'game'
        app.set_difficulty('Difficile')
        app.open_mission('annidato')
        app.editor.set('# bozza python')
        app.set_language('Java')
        app.editor.set('// bozza java')
        app.set_difficulty('Medio')
        self.assertIn('???', app.editor.value)
        app.set_difficulty('Difficile')
        self.assertEqual(app.editor.value, '// bozza java')
        app.set_language('Python')
        self.assertEqual(app.editor.value, '# bozza python')

    def test_settings_language_updates_editor_on_return(self):
        app = self.app
        app.mode = 'game'
        app.set_difficulty('Difficile')
        app.open_mission('soglia')
        app.editor.set('# mia bozza')
        app.action('settings')
        app.set_language('Java')
        app.action('return')
        self.assertEqual(app.page, 'lab')
        self.assertTrue(app.editor.value.startswith('//'))
        app.set_language('Python')
        self.assertEqual(app.editor.value, '# mia bozza')

    def test_modal_and_settings_pause_without_advancing_or_resetting(self):
        app = self.app
        app.open_mission('turno')
        app.start_trace()
        app.advance()
        frames, index = app.frames, app.frame_index
        app.lesson('Equivoci')
        app.update(5)
        self.assertEqual(app.frame_index, index)
        app.draw()
        self.assertGreater(app.modal_max, 0)
        app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_END, mod=0))
        app.draw()
        self.assertEqual(app.modal_scroll, app.modal_max)
        app.action('close')
        app.action('settings')
        app.action('theme:Giorno')
        app.action('return')
        self.assertIs(app.frames, frames)
        self.assertEqual(app.frame_index, index)
        self.assertFalse(app.playing)

    def test_easy_slot_picker_persists_without_revealing_solution(self):
        app = self.app
        app.mode = 'game'
        app.open_mission('turno')
        self.assertEqual(app.choices, [-1] * 8)
        app.draw()
        app.action('slot:0')
        app.draw()
        self.assertTrue(all(key.startswith(('choose:', 'close')) for key, _, _ in app.buttons))
        app.action('choose:1')
        self.assertEqual(app.choices[0], 1)
        app.open_mission('ricarica')
        app.open_mission('turno')
        self.assertEqual(app.choices[0], 1)
        self.assertEqual(app.choices[1:], [-1] * 7)

    def test_failed_verification_shows_counterexample_and_cannot_complete(self):
        app = self.app
        app.mode = 'game'
        app.set_difficulty('Difficile')
        app.open_mission('soglia')
        app.editor.set(app.mission.solution(app.language).replace('>=', '>'))
        app.verify()
        self.assertFalse(app.review.success)
        self.assertEqual(app.case.data['batteria'], 30)
        self.assertEqual(app.frames[-1].actions, ('ricarica',))
        self.assertFalse(app.state['completed'])
        app.action('solution')
        self.assertFalse(app.state['completed'])

    def test_verification_completion_requires_current_solution(self):
        app = self.app
        app.mode = 'game'
        app.open_mission('turno')
        app.choices = app.mission.correct_choices()
        app.sync_blocks()
        app.verify()
        self.assertIn(app.key(), app.state['completed'])
        app.set_language('Java')
        self.assertNotIn(app.key(), app.state['completed'])

    def test_quiz_wrong_answer_does_not_complete_and_trace_is_gated(self):
        app = self.app
        app.mode = 'quiz'
        app.open_quiz(4)
        app.draw()
        self.assertFalse(next(active for key, _, active in app.buttons if key == 'run'))
        app.quiz_choice = (app.quiz.answer + 1) % 3
        app.verify_quiz()
        self.assertFalse(app.quiz_correct)
        self.assertFalse(app.state['quizzes'])
        app.draw()
        self.assertTrue(next(active for key, _, active in app.buttons if key == 'run'))
        app.quiz_choice = app.quiz.answer
        app.verify_quiz()
        self.assertEqual(len(app.state['quizzes']), 1)

    def test_editor_typing_undo_invalidates_old_trace(self):
        app = self.app
        app.mode = 'game'
        app.set_difficulty('Difficile')
        app.open_mission('portello')
        app.editor.set('')
        app.editor.focus = True
        app.event(pygame.event.Event(pygame.TEXTINPUT, text='if badge:\n    apri()\n'))
        original = app.editor.value
        app.start_trace(False)
        app.event(pygame.event.Event(pygame.TEXTINPUT, text='# commento'))
        self.assertFalse(app.frames)
        app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_z, mod=pygame.KMOD_CTRL))
        self.assertEqual(app.editor.value, original)

    def test_render_all_modes_and_slot_scrolling_in_every_theme(self):
        app = self.app
        for theme in THEMES:
            app.c, app.state['theme'] = palette(theme), theme
            for mode in ('learn', 'game', 'quiz'):
                app.action('mode:' + mode)
                app.draw()
            app.mode = 'game'
            for difficulty in DIFFICULTIES:
                app.set_difficulty(difficulty)
                for mission in MISSIONS:
                    app.open_mission(mission.key)
                    app.draw()
                    for _, rect, _ in app.buttons:
                        self.assertTrue(pygame.Rect(0, 0, 1440, 900).contains(rect))
            app.set_difficulty('Facile')
            app.open_mission('turno')
            app.block_scroll = 10000
            app.draw()
            self.assertTrue(any(key == 'slot:7' for key, _, _ in app.buttons))


class PersistenceTests(unittest.TestCase):
    def test_roundtrip_validates_preferences_and_preserves_unfinished_drafts(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'state.json'
            state = storage.defaults()
            state['drafts'] = {'soglia:Difficile:Python': 'if ???'}
            state['blocks'] = {'ricarica': [-1, 1]}
            self.assertEqual(storage.save(state, path), '')
            loaded, warning = storage.load(path)
            self.assertEqual(loaded, state)
            self.assertEqual(warning, '')
            path.write_text(json.dumps({'language': [], 'size': True, 'blocks': {'ricarica': [99, 'bad']}}))
            loaded, _ = storage.load(path)
            self.assertEqual(loaded['language'], 'Python')
            self.assertEqual(loaded['size'], 19)
            self.assertFalse(loaded['blocks'])
            path.write_text('{broken')
            self.assertTrue(storage.load(path)[1])


if __name__ == '__main__':
    unittest.main()
