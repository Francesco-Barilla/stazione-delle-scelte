"""Local classroom records. No network, execution of student code, or fabricated history."""
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

MODES = ('Gioca', 'Impara', 'Quiz')
LANGUAGES = ('Python', 'JavaScript', 'C', 'Java')
DIFFICULTIES = ('Facile', 'Medio', 'Difficile')


def empty():
    return dict(version=1, student='', records={}, aids={})


def stamp():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def identity(*parts):
    return json.dumps(parts, ensure_ascii=False, separators=(',', ':'))


def clean(raw):
    result = empty()
    if not isinstance(raw, dict):
        return result
    student = raw.get('student', '')
    if isinstance(student, str):
        result['student'] = ''.join(c for c in student if c.isprintable())[:60]
    for group in ('records', 'aids'):
        records = raw.get(group)
        if not isinstance(records, dict):
            continue
        for item in records.values():
            if not isinstance(item, dict):
                continue
            if any(not isinstance(item.get(key), str) or len(item[key]) > 250 for key in ('mission', 'language', 'difficulty', 'mode')):
                continue
            if item['language'] not in LANGUAGES or item['difficulty'] not in DIFFICULTIES or item['mode'] not in MODES:
                continue
            base = {key: item[key] for key in ('mission', 'language', 'difficulty', 'mode')}
            key = identity(*base.values())
            if group == 'aids':
                kinds = item.get('kinds')
                if not isinstance(kinds, list) or any(not isinstance(k, str) or len(k) > 80 for k in kinds):
                    continue
                result[group][key] = dict(base, kinds=list(dict.fromkeys(kinds)), updated=str(item.get('updated', ''))[:40])
                continue
            if not isinstance(item.get('activity'), str) or len(item['activity']) > 250:
                continue
            if any(type(item.get(k)) is not int or item[k] < 0 for k in ('correct', 'errors', 'assisted')):
                continue
            if item['assisted'] > item['correct'] + item['errors']:
                continue
            fingerprint = item.get('last', '')
            if not isinstance(fingerprint, str) or len(fingerprint) != 64:
                continue
            key = identity(*base.values(), item['activity'])
            result[group][key] = dict(base, activity=item['activity'], correct=item['correct'], errors=item['errors'],
                                     assisted=item['assisted'], last=fingerprint,
                                     started=str(item.get('started', ''))[:40], updated=str(item.get('updated', ''))[:40])
    return result


def record_attempt(data, mission, activity, language, difficulty, mode, answer, correct):
    key = identity(mission, language, difficulty, mode, activity)
    digest = hashlib.sha256(json.dumps(answer, ensure_ascii=False, sort_keys=True, default=str).encode('utf-8')).hexdigest()
    existing = data['records'].get(key)
    if existing and existing['last'] == digest:
        return False
    now = stamp()
    record = data['records'].setdefault(key, dict(mission=mission, activity=activity, language=language, difficulty=difficulty,
                                                 mode=mode, correct=0, errors=0, assisted=0, started=now))
    record['correct' if correct else 'errors'] += 1
    aid = data['aids'].get(identity(mission, language, difficulty, mode))
    record['assisted'] += bool(aid and aid['kinds'])
    record.update(last=digest, updated=now)
    return True


def record_aid(data, mission, language, difficulty, mode, kind):
    key = identity(mission, language, difficulty, mode)
    record = data['aids'].setdefault(key, dict(mission=mission, language=language, difficulty=difficulty, mode=mode, kinds=[]))
    if kind not in record['kinds']:
        record['kinds'].append(kind)
        record['updated'] = stamp()
        return True
    return False


def matches(row, language=None, difficulty=None, mode=None):
    return all(wanted is None or row[key] == wanted for key, wanted in (('language', language), ('difficulty', difficulty), ('mode', mode)))


def summarize(data, language=None, difficulty=None, mode=None):
    records = [r for r in data['records'].values() if matches(r, language, difficulty, mode)]
    correct = sum(r['correct'] for r in records)
    errors = sum(r['errors'] for r in records)
    attempts = correct + errors
    return dict(correct=correct, errors=errors, attempts=attempts, error_percent=100 * errors / attempts if attempts else None,
                assisted=sum(r['assisted'] for r in records),
                aids=sum(len(r['kinds']) for r in data['aids'].values() if matches(r, language, difficulty, mode)))


def percent(number):
    return '—' if number is None else f'{number:.1f}%'.replace('.', ',')


def completed_contexts(app):
    from missions import BY_KEY
    result = set()
    for raw in app.state['completed']:
        parts = raw.replace('|', ':').split(':')
        if len(parts) == 3 and parts[0] in BY_KEY and parts[1] in DIFFICULTIES and parts[2] in LANGUAGES:
            result.add(tuple(parts))
    return sorted(result)


def excel_safe(value):
    value = str(value)
    return "'" + value if value.lstrip().startswith(('=', '+', '-', '@')) or value.startswith(('\t', '\r', '\n')) else value


def export_csv(path, data, laboratory, completed, titles):
    columns = ['Studente', 'Laboratorio', 'Tipo', 'Modalità', 'Missione', 'Attività', 'Linguaggio', 'Difficoltà',
               'Tentativi', 'Corrette', 'Errori', 'Errore %', 'Tentativi dopo aiuti', 'Aiuti consultati', 'Primo controllo UTC', 'Ultimo controllo UTC']
    with Path(path).open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.writer(stream, delimiter=';')
        writer.writerow(columns)
        def row(*values):
            writer.writerow([excel_safe(v) for v in values])
        for r in sorted(data['records'].values(), key=lambda r: (r['language'], r['difficulty'], r['mode'], r['mission'], r['activity'])):
            attempts = r['correct'] + r['errors']
            aid = data['aids'].get(identity(r['mission'], r['language'], r['difficulty'], r['mode']), {})
            row(data['student'], laboratory, 'Risposte', r['mode'], titles.get(r['mission'], r['mission']), r['activity'],
                r['language'], r['difficulty'], attempts, r['correct'], r['errors'],
                f'{100 * r["errors"] / attempts:.1f}'.replace('.', ',') if attempts else '', r['assisted'],
                ', '.join(aid.get('kinds', [])), r['started'], r['updated'])
        for r in data['aids'].values():
            row(data['student'], laboratory, 'Aiuti', r['mode'], titles.get(r['mission'], r['mission']), '', r['language'], r['difficulty'],
                '', '', '', '', '', ', '.join(r['kinds']), '', r.get('updated', ''))
        for mission, difficulty, language in completed:
            row(data['student'], laboratory, 'Completamento', 'Gioca', titles.get(mission, mission), '', language, difficulty,
                '', '', '', '', '', '', '', '')
        if not data['records'] and not completed and not data['aids']:
            row(data['student'], laboratory, 'Nessuna attività registrata', '', '', '', '', '', '', '', '', '', '', '', '', '')


def app_mode(app):
    return 'Quiz' if app.page == 'quiz' else 'Impara' if app.mode == 'learn' else 'Gioca'


def track(app, activity, right, answer, mode=None, mission=None):
    if record_attempt(app.state['classroom'], mission or app.mission.key, activity, app.language, app.difficulty, mode or app_mode(app), answer, right):
        app.persist()


def aid(app, kind):
    if record_aid(app.state['classroom'], app.mission.key, app.language, app.difficulty, app_mode(app), kind):
        app.persist()


def draw_status(app):
    import pygame
    from missions import MISSIONS
    from ui import text
    language, difficulty = app.language, app.difficulty
    summary = summarize(app.state['classroom'], language, difficulty)
    count = sum(lang == language and diff == difficulty for _, diff, lang in completed_contexts(app))
    pygame.draw.rect(app.canvas, app.c['bg'], (0, 855, 1440, 45))
    label = f'{language} · {difficulty}  |  Gioca: {count}/{len(MISSIONS)} completate  |  Risposte: {summary["correct"]} giuste · {summary["errors"]} errori ({percent(summary["error_percent"])})'
    text(app.canvas, label, (40, 859), 16, app.c['text'])
    app.button('classroom', 'Progressi e report' + (' !' if app.notice else ''), (1170, 857, 230, 30), size=16)
    text(app.canvas, app.notice or 'Realizzato dal Prof. Barillà Francesco · Registro salvato in questa copia del laboratorio', (720, 890), 12,
         app.c['danger'] if app.notice else app.c['muted'], anchor='center')


def open_report(app):
    app.playing = False
    app.editor.focus = False
    app.modal = 'classroom'
    app.modal_scroll = 0
    app.classroom_all = False
    app.classroom_edit = False
    app.classroom_message = ''


def report_rows(app):
    from missions import MISSIONS
    language = None if app.classroom_all else app.language
    difficulty = None if app.classroom_all else app.difficulty
    result = []
    known = {m.key for m in MISSIONS}
    activities = [(m.key, m.title) for m in MISSIONS]
    activities += [(key, key) for key in sorted({r['mission'] for r in app.state['classroom']['records'].values()} - known)]
    completed = completed_contexts(app)
    for mission_key, title in activities:
        records = [r for r in app.state['classroom']['records'].values() if r['mission'] == mission_key and matches(r, language, difficulty)]
        correct, errors = sum(r['correct'] for r in records), sum(r['errors'] for r in records)
        done = sum(key == mission_key and (language is None or lang == language) and (difficulty is None or diff == difficulty)
                   for key, diff, lang in completed)
        aids = [r for r in app.state['classroom']['aids'].values() if r['mission'] == mission_key and matches(r, language, difficulty)]
        result.append((title, f'{done}/12' if app.classroom_all and mission_key in known else 'Sì' if done else '—', correct, errors,
                       percent(100 * errors / (correct + errors)) if correct + errors else '—',
                       'Soluzione' if any('soluzione' in r['kinds'] for r in aids) else 'Sì' if aids else '—'))
    return result


def draw_report(app):
    import pygame
    from missions import MISSIONS
    from ui import SIZE, panel, text, wrap
    s, c = app.canvas, app.c
    overlay = pygame.Surface(SIZE, pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    s.blit(overlay, (0, 0))
    app.buttons = []
    app.drawing_modal = True
    panel(s, pygame.Rect(100, 52, 1240, 800), c['panel'], c['border'], 16)
    text(s, 'Progressi e report per il docente', (130, 75), 30, c['text'], True)
    app.button('classroom_close', 'Chiudi', (1190, 73, 118, 40), size=17)
    data = app.state['classroom']
    text(s, 'Studente / codice:', (132, 140), 18, c['muted'])
    from ui import font
    student_label = data['student'] or 'Clicca e scrivi il nome / codice'
    while font(19).size(student_label + (' |' if app.classroom_edit else ''))[0] > 695:
        student_label = student_label[:-2].rstrip('…') + '…'
    app.button('classroom_name', student_label + (' |' if app.classroom_edit else ''), (315, 128, 730, 43), size=19)
    text(s, 'Invio salva' if app.classroom_edit else 'Facoltativo · identifica tutto lo storico di questa copia', (319, 178), 15, c['muted'])
    app.button('classroom_filter', 'Vedi percorso attuale' if app.classroom_all else 'Vedi tutti i percorsi', (1060, 128, 248, 43), size=17)
    text(s, 'Filtro: tutti' if app.classroom_all else app.language + ' · ' + app.difficulty, (1070, 178), 15, c['muted'])
    language = None if app.classroom_all else app.language
    difficulty = None if app.classroom_all else app.difficulty
    total = len(MISSIONS) * (12 if app.classroom_all else 1)
    done = sum((language is None or lang == language) and (difficulty is None or diff == difficulty)
               for _, diff, lang in completed_contexts(app))
    summary = summarize(data, language, difficulty)
    cards = [('MISSIONI GIOCA', f'{done}/{total} · {100 * done / total:.0f}%'), ('RISPOSTE CORRETTE', str(summary['correct'])),
             ('RISPOSTE ERRATE', str(summary['errors'])), ('PERCENTUALE DI ERRORE', percent(summary['error_percent']))]
    for i, (label, number) in enumerate(cards):
        x = 132 + i * 296
        panel(s, pygame.Rect(x, 211, 280, 100), c['card'], radius=10)
        text(s, label, (x + 14, 225), 14, c['muted'], True)
        text(s, number, (x + 14, 252), 30, c['text'], True)
    text(s, f'Errori ÷ {summary["attempts"]} risposte controllate × 100. Un controllo identico ripetuto non aggiunge tentativi.', (132, 326), 17, c['muted'])
    pieces = []
    for mode in MODES:
        part = summarize(data, language, difficulty, mode)
        pieces.append(f'{mode}: {part["correct"]} giuste / {part["errors"]} errori')
    text(s, '   ·   '.join(pieces), (132, 357), 18, c['text'])
    text(s, f'{summary["aids"]} aiuti distinti consultati · {summary["assisted"]} tentativi dopo un aiuto', (132, 390), 17, c['accent'])
    headings = [('Missione / quiz', 145), ('Gioca finita', 637), ('Giuste', 815), ('Errori', 945), ('Errore %', 1050), ('Aiuti', 1182)]
    for label, x in headings:
        text(s, label, (x, 433), 16, c['muted'], True)
    rows = report_rows(app)
    app.modal_max = max(0, len(rows) * 38 - 190)
    app.modal_scroll = min(app.modal_scroll, app.modal_max)
    original_clip = s.get_clip()
    s.set_clip(pygame.Rect(132, 464, 1176, 191))
    for i, row in enumerate(rows):
        y = 465 + i * 38 - app.modal_scroll
        if 427 < y < 657:
            pygame.draw.line(s, c['border'], (133, y + 32), (1298, y + 32))
            for j, (value, (_, x)) in enumerate(zip(row, headings)):
                wrap(s, str(value), pygame.Rect(x, y, 476 if j == 0 else 130 if j == 1 else 108, 31), 17, c['text'])
    s.set_clip(original_clip)
    text(s, 'Scorri la tabella con la rotella o con ↑ ↓. Il CSV contiene tutti i linguaggi e livelli.', (133, 669), 16, c['muted'])
    app.button('classroom_up', '↑', (1220, 661, 40, 30), size=18)
    app.button('classroom_down', '↓', (1268, 661, 40, 30), size=18)
    wrap(s, 'I vecchi completamenti restano visibili; i tentativi sono contati da questo aggiornamento. Le attività Impara e Quiz sono separate qui sopra. Il registro è locale, modificabile e non sincronizzato: consegna il CSV al docente.', pygame.Rect(132, 706, 850, 74), 16, c['muted'])
    app.button('classroom_export', 'Esporta report CSV', (1010, 720, 298, 48), size=18)
    wrap(s, app.classroom_message or app.notice or 'Il CSV viene salvato accanto al file dei progressi, nella cartella report.', pygame.Rect(132, 790, 1176, 42), 16, c['accent'])
    app.drawing_modal = False


def action(app, key):
    if key == 'classroom':
        open_report(app)
    elif key == 'classroom_close':
        app.classroom_edit = False
        app.modal = None
        app.persist()
    elif key == 'classroom_name':
        app.classroom_edit = not app.classroom_edit
        app.classroom_replace = True
        import pygame
        pygame.key.start_text_input()
    elif key == 'classroom_filter':
        app.classroom_all = not app.classroom_all
        app.modal_scroll = 0
    elif key in ('classroom_up', 'classroom_down'):
        app.modal_scroll = max(0, min(app.modal_max, app.modal_scroll + (-76 if key.endswith('up') else 76)))
    elif key == 'classroom_export':
        from missions import MISSIONS
        import storage
        root = Path(app.state_path or storage.data_path()).parent / 'report'
        try:
            root.mkdir(parents=True, exist_ok=True)
            name = 'Report-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.csv'
            path = root / name
            export_csv(path, app.state['classroom'], storage.data_path().stem, completed_contexts(app), {m.key: m.title for m in MISSIONS})
            app.classroom_message = 'Salvato nella cartella report, accanto ai progressi: ' + name
            app.persist()
        except OSError:
            app.classroom_message = 'Non riesco a esportare qui. Sposta il laboratorio in una cartella personale scrivibile e riprova.'
    else:
        return False
    return True


def event(app, event):
    import pygame
    if app.modal != 'classroom':
        return False
    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
        action(app, 'classroom_close')
        return True
    if not app.classroom_edit:
        return False
    if event.type == pygame.TEXTINPUT:
        text = ''.join(c for c in event.text if c.isprintable())
        current = '' if app.classroom_replace else app.state['classroom']['student']
        app.state['classroom']['student'] = (current + text)[:60]
        app.classroom_replace = False
        app.persist()
        return True
    if event.type == pygame.KEYDOWN:
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_TAB):
            app.classroom_edit = False
            app.persist()
        elif event.key == pygame.K_BACKSPACE:
            app.state['classroom']['student'] = '' if app.classroom_replace else app.state['classroom']['student'][:-1]
            app.classroom_replace = False
            app.persist()
        return True
    return False
