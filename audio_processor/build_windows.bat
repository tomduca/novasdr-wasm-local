@echo off
REM Build standalone Windows application (.exe)

echo Building NovaSDR Audio Processor for Windows...

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install PyInstaller
pip install pyinstaller

REM Build the application
pyinstaller --name="NovaSDR Audio Processor" ^
    --windowed ^
    --onefile ^
    --icon=..\assets\icon.ico ^
    --add-data="recordings;recordings" ^
    --hidden-import=numpy ^
    --hidden-import=scipy ^
    --hidden-import=sounddevice ^
    --hidden-import=novasdr_nr ^
    --hidden-import=pydub ^
    audio_processor_native_gui.py

echo.
echo Build complete!
echo Application: dist\NovaSDR Audio Processor.exe
echo.
echo To run: dist\NovaSDR Audio Processor.exe
pause
