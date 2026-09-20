"""Distribution checks, called only by the existing --smoke-test command."""
import csv
from pathlib import Path


def check_classroom(app, report_path, screenshot_dir=None):
    import pygame
    import classroom
    import storage
    from missions import MISSIONS
    root = Path(report_path).resolve().parent / 'classroom-check'
    root.mkdir(parents=True, exist_ok=True)
    app.state_path = root / 'classroom.json'
    app.saving = True
    app.state = storage.defaults()
    app.state.update(language='C', difficulty='Difficile')
    app.mode = 'game'
    app.modal = None
    app.open_mission(MISSIONS[0].key)
    check = app.verify_program if hasattr(app, 'verify_program') else app.verify
    app.editor.set('???')
    check()
    check()
    app.editor.set(app.mission.solution(app.language))
    check()
    check()
    totals = classroom.summarize(app.state['classroom'])
    assert (totals['correct'], totals['errors'], totals['error_percent']) == (1, 1, 50.0), totals
    assert len(classroom.completed_contexts(app)) == 1
    app.draw()
    assert any(key == 'classroom' and enabled for key, _, enabled in app.buttons)
    app.action('classroom')
    app.action('classroom_name')
    app.event(pygame.event.Event(pygame.TEXTINPUT, text='Collaudo automatico'))
    app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0))
    before = set((root / 'report').glob('*.csv'))
    app.action('classroom_export')
    created = set((root / 'report').glob('*.csv')) - before
    assert len(created) == 1, app.classroom_message
    with created.pop().open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream, delimiter=';'))
    attempt = next(row for row in rows if row['Tipo'] == 'Risposte')
    assert (attempt['Studente'], attempt['Corrette'], attempt['Errori'], attempt['Errore %']) == ('Collaudo automatico', '1', '1', '50,0'), attempt
    restored, warning = storage.load(app.state_path)
    assert not warning
    assert classroom.summarize(restored['classroom']) == totals
    app.draw()
    if screenshot_dir:
        target = Path(screenshot_dir)
        target.mkdir(parents=True, exist_ok=True)
        pygame.image.save(app.canvas, str(target / '30-progressi-e-report.png'))
    app.action('classroom_close')
    app.saving = False
