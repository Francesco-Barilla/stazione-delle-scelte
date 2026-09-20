"""Exercise the real submit, replay and report paths of each portable lab."""
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
from pathlib import Path
import tempfile
import unittest
import pygame
import classroom
from main import App
from missions import MISSIONS
import storage


class ClassroomUITests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.app = App(pygame.display.set_mode((1440, 900)), Path(self.folder.name) / 'state.json', saving=True)
        self.app.state = storage.defaults()
        self.app.mode = 'game'
        self.app.state['difficulty'] = 'Difficile'
        self.app.open_mission(MISSIONS[0].key)

    def tearDown(self):
        from ui import font
        font.cache_clear()
        pygame.quit()

    def submit(self):
        if hasattr(self.app, 'verify_program'):
            self.app.verify_program()
        else:
            self.app.verify()

    def test_wrong_correct_repeat_and_trace(self):
        app = self.app
        app.editor.set('???')
        self.submit()
        self.submit()
        self.assertEqual(classroom.summarize(app.state['classroom'])['errors'], 1)
        app.editor.set(app.mission.solution(app.language))
        self.submit()
        self.submit()
        summary = classroom.summarize(app.state['classroom'])
        self.assertEqual((summary['correct'], summary['errors']), (1, 1))
        self.assertEqual(summary['error_percent'], 50)
        self.assertEqual(len(classroom.completed_contexts(app)), 1)
        app.action('trace' if hasattr(app, 'verify_program') else 'trace_view')
        for _ in range(12):
            app.update(1)
        self.assertEqual(classroom.summarize(app.state['classroom']), summary)
        restored, _ = storage.load(app.state_path)
        self.assertEqual(classroom.summarize(restored['classroom']), summary)

    def test_report_visible_typing_export_and_no_attempt(self):
        app = self.app
        app.draw()
        self.assertTrue(any(key == 'classroom' for key, _, _ in app.buttons))
        app.action('classroom')
        app.draw()
        self.assertEqual(app.modal, 'classroom')
        app.action('classroom_name')
        app.event(pygame.event.Event(pygame.TEXTINPUT, text='Studente 4'))
        app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0))
        self.assertEqual(app.state['classroom']['student'], 'Studente 4')
        app.action('classroom_export')
        paths = list((Path(self.folder.name) / 'report').glob('*.csv'))
        self.assertEqual(len(paths), 1)
        self.assertIn('Studente 4', paths[0].read_text(encoding='utf-8-sig'))
        self.assertEqual(classroom.summarize(app.state['classroom'])['attempts'], 0)
        app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0))
        self.assertIsNone(app.modal)

    def test_solution_consultation_survives_reopen(self):
        app = self.app
        if hasattr(app, 'verify_program'):
            app.action('hint')
            for _ in range(3):
                app.action('more_hint')
        else:
            app.action('solution')
        app.action('close')
        app.editor.set(app.mission.solution(app.language))
        self.submit()
        summary = classroom.summarize(app.state['classroom'])
        self.assertEqual(summary['assisted'], 1)
        self.assertTrue(any('soluzione' in row['kinds'] for row in app.state['classroom']['aids'].values()))

    def test_real_learning_and_quiz_answers_are_separate(self):
        app = self.app
        app.mode = 'learn'
        if hasattr(app, 'open_activity'):
            app.open_activity(MISSIONS[0].key)
            correct = app.activity_options.index(app.mission.rule(app.case.data))
            wrong = (correct + 1) % len(app.activity_options)
            app.choose_order(wrong)
            app.choose_order(wrong)
            app.choose_order(correct)
        elif hasattr(app, 'choose_prediction'):
            app.open_mission(MISSIONS[0].key)
            expected = app.frames[app.frame_index + 1].after
            correct = next(i for i, value in enumerate(app.prediction_options) if app.equivalent(value, expected))
            wrong = next(i for i, value in enumerate(app.prediction_options) if not app.equivalent(value, expected))
            app.choose_prediction(wrong)
            app.choose_prediction(wrong)
            app.choose_prediction(correct)
        else:
            from guidance import PREDICTIONS
            app.open_mission(MISSIONS[0].key)
            correct = PREDICTIONS[app.mission.key].correct
            wrong = (correct + 1) % 3
            app.action('predict:' + str(wrong))
            app.action('predict:' + str(wrong))
            app.action('predict:' + str(correct))
        learn = classroom.summarize(app.state['classroom'], mode='Impara')
        self.assertEqual((learn['correct'], learn['errors']), (1, 1))
        self.assertEqual(classroom.summarize(app.state['classroom'], mode='Gioca')['attempts'], 0)
        if hasattr(app, 'open_quiz'):
            app.open_quiz(0)
            correct = app.quiz.correct(app.language) if hasattr(app.quiz, 'correct') else app.quiz.answer
            app.quiz_choice = (correct + 1) % len(app.quiz.choices)
            check = app.check_quiz if hasattr(app, 'check_quiz') else app.verify_quiz
            check()
            check()
            app.quiz_choice = correct
            check()
            quiz = classroom.summarize(app.state['classroom'], mode='Quiz')
            self.assertEqual((quiz['correct'], quiz['errors']), (1, 1))
            self.assertEqual(classroom.summarize(app.state['classroom'], mode='Impara'), learn)
        restored, _ = storage.load(app.state_path)
        self.assertEqual(classroom.summarize(restored['classroom']), classroom.summarize(app.state['classroom']))


if __name__ == '__main__':
    unittest.main()
