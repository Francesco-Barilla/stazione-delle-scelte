# Consegne chiare: piano di implementazione

> Esecuzione inline con executing-plans; verifica indipendente prima della pubblicazione.

**Obiettivo:** rendere inequivocabili scelta, scrittura e controllo.
**Architettura:** `guidance.py` descrive lacune e consegne; `guided_ui.py` presenta lavoro e risultati; `main.py` collega focus, verifica e traccia; `activities.py` mantiene il turno dei droni.
**Tecnologie:** Python, Pygame, PyInstaller già presenti.

## Vincoli globali
Nessuna nuova dipendenza. Conservare bozze e progressi, quattro linguaggi, venti missioni e domini di verifica. Distribuire EXE e ZIP offline.

## Passi
- [x] Scrivere `tests/test_guidance.py`: click su `focus_code`, sostituzione condizione/azione, controllo nei quattro linguaggi; commenti legacy; Ctrl+Invio; errore persistente dei droni; traccia separata; previsione quiz aggiornata. Eseguire `python -m unittest discover -s tests -p test_guidance.py -q` e verificare i fallimenti attesi.
- [x] Implementare `first_gap(code, language)`, `writing_task(mission, code, language)`, `mission_brief(mission, language, code)`, `syntax_example(mission, language)` in `guidance.py`. Mostrare sintassi di if, catena, annidamento e operatori; distinguere i sensori di presenza dai testi.
- [x] Collegare focus, Ctrl+Invio, messaggi di verifica e nuova vista di traccia in `main.py`. Implementare pannelli numerati, dati automatici e confronto richiesto/ottenuto in `guided_ui.py`; rendere persistenti le risposte di `activities.py`.
- [x] Verificare la suite completa e la leggibilità di missioni, lingue, difficoltà, stati di risposta e dimensioni. Catturare schermate con `python main.py --smoke-test build/smoke-source.json --screenshots screenshots`.
- [x] Revisione indipendente, aggiornamento README e ricostruzione con `python build_release.py`; provare anche l'EXE estratto dallo ZIP.
- [ ] Copiare soltanto file di distribuzione verificati nella cartella sorella, preservando `progressi_selezione.json`; commit, push e confronto di tutti i file remoti con il commit locale.

## Verifiche della versione
46 test superati. Controllo di impaginazione su 7.212 schermate senza testi fuori area. Revisione indipendente conclusa: esempi annidati e scorrimento della traccia verificati.

Distribuzioni ricostruite. EXE estratto dallo ZIP verificato: controllo di avvio e 240 viste, otto schermate della nuova interfaccia identiche a quelle sorgenti.
