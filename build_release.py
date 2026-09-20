"""Build and verify the offline Windows distribution."""
import json
import os
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parent


def archives():
    output = ROOT / 'dist'
    output.mkdir(exist_ok=True)
    docs = ('README.md', 'README.txt', 'LICENZE.txt', 'Avvia_Stazione.cmd')
    previews = [ROOT / 'screenshots' / name for name in ('30-progressi-e-report.png', '18-completa-condizione.png', '25-corretto-anche-da-fermo.png')]
    packages = {
        'StazioneScelte-Windows.zip': [ROOT / 'StazioneScelte.exe'] + [ROOT / name for name in docs] + previews,
        'StazioneScelte-Sorgenti.zip': list(ROOT.glob('*.py')) + [ROOT / name for name in docs + ('requirements.txt', 'StazioneScelte.spec', 'PIANO.md', '.gitignore', '.gitattributes')] + list((ROOT / 'assets').glob('*')) + list((ROOT / 'tests').glob('*.py')) + list((ROOT / 'docs').rglob('*.md')) + list((ROOT / 'screenshots').glob('*.png')),
    }
    for name, files in packages.items():
        with ZipFile(output / name, 'w', ZIP_DEFLATED) as archive:
            for path in files:
                if path.is_file():
                    archive.write(path, path.relative_to(ROOT).as_posix())
        with ZipFile(output / name) as archive:
            assert archive.testzip() is None
            assert 'progressi_selezione.json' not in archive.namelist()
            for member in archive.namelist():
                assert archive.read(member) == (ROOT / member).read_bytes(), member
        print('Verificato:', name)


if __name__ == '__main__':
    os.chdir(ROOT)
    os.environ['PYINSTALLER_CONFIG_DIR'] = str(ROOT / 'build' / 'cache')
    subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-q'], check=True)
    subprocess.run([sys.executable, '-m', 'PyInstaller', '--noconfirm', '--distpath', '.', 'StazioneScelte.spec'], check=True)
    report = ROOT / 'build' / 'smoke-windows.json'
    report.unlink(missing_ok=True)
    subprocess.run([str(ROOT / 'StazioneScelte.exe'), '--smoke-test', str(report)], check=True, timeout=120,
                   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    assert json.loads(report.read_text(encoding='utf-8'))['ok'] is True
    archives()
    print('Pronti: StazioneScelte.exe e i due ZIP in dist.')
