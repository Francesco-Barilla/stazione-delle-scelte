import csv
import io
import tempfile
import unittest
from pathlib import Path
import classroom as cr
import storage


class ClassroomTests(unittest.TestCase):
    def attempt(self, data, answer, right, **extra):
        return cr.record_attempt(data, 'for_pontile', 'programma', 'Python', 'Facile', 'Gioca', answer, right, **extra)

    def test_actual_errors_and_unchanged_checks(self):
        data = cr.empty()
        self.assertTrue(self.attempt(data, 'a', False))
        self.assertFalse(self.attempt(data, 'a', False))
        self.assertTrue(self.attempt(data, 'b', False))
        self.assertTrue(self.attempt(data, 'c', True))
        summary = cr.summarize(data)
        self.assertEqual((summary['attempts'], summary['correct'], summary['errors']), (3, 1, 2))
        self.assertAlmostEqual(summary['error_percent'], 200 / 3)
        self.assertEqual(cr.summarize(data, 'C', 'Facile')['attempts'], 0)
        self.assertIsNone(cr.summarize(cr.empty())['error_percent'])

    def test_history_without_invented_attempts_and_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'progress.json'
            state = storage.defaults()
            state['completed'] = ['for_pontile|Facile|Python']
            storage.save(state, path)
            loaded, warning = storage.load(path)
            self.assertFalse(warning)
            self.assertEqual(loaded['completed'], state['completed'])
            self.assertEqual(cr.summarize(loaded['classroom'])['attempts'], 0)
            self.attempt(loaded['classroom'], 'wrong', False)
            storage.save(loaded, path)
            restored, _ = storage.load(path)
            self.assertFalse(self.attempt(restored['classroom'], 'wrong', False))
            self.assertEqual(cr.summarize(restored['classroom'])['errors'], 1)

    def test_separate_modes_and_aids(self):
        data = cr.empty()
        cr.record_aid(data, 'for_pontile', 'Python', 'Facile', 'Gioca', 'soluzione')
        cr.record_aid(data, 'for_pontile', 'Python', 'Facile', 'Gioca', 'soluzione')
        self.attempt(data, 'c', True)
        cr.record_attempt(data, 'for_pontile', 'previsione', 'Python', 'Facile', 'Impara', '0', False)
        self.assertEqual(cr.summarize(data, mode='Gioca')['correct'], 1)
        self.assertEqual(cr.summarize(data, mode='Impara')['errors'], 1)
        self.assertEqual(cr.summarize(data)['aids'], 1)
        self.assertEqual(cr.summarize(data)['assisted'], 1)

    def test_invalid_data_is_ignored_not_counted(self):
        for raw in (None, [], {'records': []}, {'records': {'bad': {'correct': -1}}}):
            self.assertEqual(cr.summarize(cr.clean(raw))['attempts'], 0)
        data = cr.empty()
        self.attempt(data, 'a', True)
        record = next(iter(data['records'].values()))
        record['correct'] = True
        self.assertEqual(cr.summarize(cr.clean(data))['attempts'], 0)

    def test_report_is_identified_escaped_and_has_completion_rows(self):
        data = cr.empty()
        data['student'] = '=1+1'
        self.attempt(data, 'a', False)
        self.attempt(data, 'b', True)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'report.csv'
            cr.export_csv(path, data, 'Robot', [('for_pontile', 'Facile', 'Python')], {'for_pontile': 'Pontile'})
            rows = list(csv.DictReader(io.StringIO(path.read_text(encoding='utf-8-sig')), delimiter=';'))
            self.assertEqual(rows[0]['Studente'], "'=1+1")
            answers = [row for row in rows if row['Tipo'] == 'Risposte']
            self.assertEqual(answers[0]['Corrette'], '1')
            self.assertEqual(answers[0]['Errori'], '1')
            self.assertEqual(answers[0]['Errore %'], '50,0')
            completed = [row for row in rows if row['Tipo'] == 'Completamento']
            self.assertEqual(completed[0]['Missione'], 'Pontile')
            self.assertEqual(completed[0]['Tentativi'], '')


if __name__ == '__main__':
    unittest.main()
