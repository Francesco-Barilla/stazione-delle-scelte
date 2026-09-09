@echo off
cd /d "%~dp0"
if exist StazioneScelte.exe (
    start "" "%~dp0StazioneScelte.exe"
) else (
    python main.py
    if errorlevel 1 (
        echo.
        echo Per i sorgenti servono Python 3.10 o successivo e Pygame.
        echo Installa Pygame con: python -m pip install -r requirements.txt
        pause
    )
)
