"""Learner journeys using the controls shown on screen and actual typing."""
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
from pathlib import Path
import tempfile
import unittest
import pygame
from main import App
from native_io import output_statement
from engine import LANGUAGES, parse, run
from guidance import first_gap, mission_brief, syntax_example
from missions import MISSIONS
import ui


class GuidanceTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.app = App(pygame.display.set_mode((1280, 800)), Path(self.temp.name) / 'progress.json', saving=False)
        self.app.mode = 'game'

    def click(self, key):
        app = self.app
        app.draw()
        options = [rect for name, rect, active in app.buttons if name == key and active]
        self.assertTrue(options, 'Comando accessibile mancante: ' + key)
        x, y = options[0].center
        pos = (round(x * 1280 / 1440), round(y * 800 / 900))
        for kind in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            app.event(pygame.event.Event(kind, pos=pos, button=1))

    def test_medium_selects_condition_then_action_and_preserves_surrounding_code(self):
        app = self.app
        app.set_difficulty('Medio')
        for language in LANGUAGES:
            app.set_language(language)
            app.open_mission('portello')
            for replacement in ('badge', output_statement('apri', language).rstrip(';')):
                before = app.editor.value
                self.click('focus_code')
                a, b = sorted((app.editor.caret, app.editor.anchor))
                self.assertEqual(before[a:b], '???')
                app.event(pygame.event.Event(pygame.TEXTINPUT, text=replacement))
                self.assertEqual(app.editor.value, before[:a] + replacement + before[b:])
            self.click('verify')
            self.assertTrue(app.review.success, language)

    def test_hard_typing_does_not_get_swallowed_by_legacy_comment(self):
        app = self.app
        app.set_difficulty('Difficile')
        app.open_mission('ricarica')
        app.editor.set('# appunti')
        self.click('focus_code')
        app.event(pygame.event.Event(pygame.TEXTINPUT, text='if batteria < 30:\n    print("ricarica")'))
        self.click('verify')
        self.assertTrue(app.editor.value.startswith('# appunti\n'))
        self.assertTrue(app.review.success)

    def test_control_enter_checks_without_modifying_the_draft(self):
        app = self.app
        app.set_difficulty('Difficile')
        app.open_mission('portello')
        app.editor.set(app.mission.solution('Python'))
        app.editor.focus = True
        before = app.editor.value
        app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=pygame.KMOD_CTRL))
        self.assertEqual(app.editor.value, before)
        self.assertIsNotNone(app.review)
        self.assertTrue(app.review.success)

    def test_wrong_drone_answer_stays_selected_until_retry(self):
        app = self.app
        app.open_activity('annidato')
        correct = app.activity_options.index(app.mission.rule(app.case.data))
        wrong = (correct + 1) % len(app.activity_options)
        self.click('order:' + str(wrong))
        self.assertEqual(getattr(app, 'activity_attempt', None), wrong)
        self.assertFalse(app.activity_correct)
        self.assertFalse(app.frames)
        self.click('order:' + str(correct))
        self.assertTrue(app.activity_correct)
        self.assertEqual(app.frames[-1].actions, ('nega',))

    def test_trace_has_its_own_editor_and_keeps_the_writing_position(self):
        app = self.app
        app.set_difficulty('Difficile')
        app.set_language('Java')
        app.open_mission('turno')
        app.editor.set(app.mission.solution('Java'))
        self.click('focus_code')
        before = app.editor.snapshot()
        self.click('trace_view')
        self.assertEqual(app.modal, 'trace')
        app.action('step')
        app.action('close')
        self.assertEqual(app.editor.snapshot(), before)
        self.click('verify')
        self.assertTrue(app.review.success)

    def test_changed_quiz_answer_requires_another_check(self):
        app = self.app
        app.open_quiz(4)
        app.quiz_choice = app.quiz.answer
        app.verify_quiz()
        app.action('answer:' + str((app.quiz.answer + 1) % 3))
        self.assertFalse(app.quiz_correct)
        self.assertFalse(app.quiz_attempted)
        self.assertFalse(app.feedback)

    def test_empty_program_error_explains_what_to_write(self):
        app = self.app
        app.set_difficulty('Difficile')
        app.open_mission('ricarica')
        app.editor.set('')
        self.click('verify')
        self.assertIn('Scrivi qui', app.feedback)
        self.assertNotIn(app.key(), app.state['completed'])

    def test_lesson_code_button_opens_an_editable_game_not_another_readonly_lesson(self):
        app = self.app
        app.mode = 'learn'
        app.open_activity('portello')
        self.click('activity_code')
        self.assertEqual((app.page, app.mode), ('lab', 'game'))
        self.assertTrue(app.easy)
        self.click('next_slot')
        self.assertEqual(app.modal, 'slot')

    def test_real_gaps_ignore_notes_with_question_marks_in_every_language(self):
        app = self.app
        app.set_difficulty('Medio')
        for language in LANGUAGES:
            app.set_language(language)
            app.open_mission('portello')
            note = ('# ' if language == 'Python' else '// ') + 'dubbio ???\n'
            app.editor.set(note + app.mission.starter(language, 'Medio'))
            for value in ('badge', output_statement('apri', language).rstrip(';')):
                self.click('focus_code')
                self.assertGreaterEqual(app.editor.anchor, len(note))
                app.event(pygame.event.Event(pygame.TEXTINPUT, text=value))
            self.click('verify')
            self.assertTrue(app.review.success, (language, app.feedback))

    def test_guide_examples_are_executable_in_the_selected_language(self):
        for mission in MISSIONS:
            for language in LANGUAGES:
                source = syntax_example(mission, language)
                frames = run(parse(source, language), mission.cases[0].data, language)
                self.assertTrue(frames)
                self.assertIn(source, mission_brief(mission, language, ''))

    def test_block_verification_keeps_the_blocks_available_for_correction(self):
        app = self.app
        app.open_mission('portello')
        app.choices = app.mission.correct_choices()
        app.choices[0] = (app.choices[0] + 1) % len(app.mission.slots[0].options)
        app.sync_blocks()
        self.click('verify')
        self.assertFalse(app.review.success)
        self.assertFalse(app.code_view)
        self.click('slot:0')
        self.assertEqual(app.modal, 'slot')

    def test_displayed_help_retains_the_indentation_of_nested_python(self):
        app = self.app
        app.set_difficulty('Difficile')
        app.open_mission('annidato')
        self.click('writing_help')
        self.assertEqual(app.modal, 'writing')
        source = syntax_example(app.mission, 'Python')
        rows = ui.rich_lines(app.modal_text, source, 995, 21)
        displayed_code = [line for line, mono in rows if mono]
        self.assertEqual(displayed_code, source.splitlines())
        self.assertEqual(run(parse('\n'.join(displayed_code), 'Python'), app.case.data, 'Python')[-1].actions, ('attendi',))

    def test_trace_can_scroll_horizontally_to_read_long_conditions(self):
        app = self.app
        app.set_difficulty('Difficile')
        app.open_mission('portello')
        app.editor.set('if ' + ' or '.join(['badge'] * 20) + ':\n    print("apri")\nelse:\n    print("nega")')
        self.click('trace_view')
        app.draw()
        try:
            pygame.key.set_mods(pygame.KMOD_SHIFT)
            app.event(pygame.event.Event(pygame.MOUSEWHEEL, y=-5, x=0))
        finally:
            pygame.key.set_mods(0)
        self.assertGreater(app.trace_editor.xscroll, 0)
        self.assertEqual(app.trace_editor.scroll, 0)


if __name__ == '__main__':
    unittest.main()
