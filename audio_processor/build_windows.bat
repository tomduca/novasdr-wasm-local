@echo off
REM Build standalone Windows application (.exe)

echo Building NovaSDR Audio Processor for Windows...

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install PyInstaller
pip install pyinstaller

REM Find NovaSDR module location
for /f "delims=" %%i in ('python -c "import novasdr_nr; import os; print(os.path.dirname(novasdr_nr.__file__).replace('/', '\\'))"') do set NOVASDR_MODULE=%%i
echo NovaSDR module found at: %NOVASDR_MODULE%

REM Clean previous builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "NovaSDR Audio Processor.spec" del "NovaSDR Audio Processor.spec"

REM Build the application
pyinstaller --name="LU2MET_NR" ^
    --windowed ^
    --onefile ^
    --icon=app_icon.ico ^
    --add-data="recordings;recordings" ^
    --add-binary="%NOVASDR_MODULE%\novasdr_nr*.pyd;." ^
    --hidden-import=numpy ^
    --hidden-import=numpy.core._multiarray_umath ^
    --hidden-import=scipy ^
    --hidden-import=scipy.signal ^
    --hidden-import=scipy.fft ^
    --hidden-import=sounddevice ^
    --hidden-import=_sounddevice ^
    --hidden-import=novasdr_nr ^
    --hidden-import=pydub ^
    --hidden-import=PyQt5 ^
    --hidden-import=PyQt5.QtCore ^
    --hidden-import=PyQt5.QtGui ^
    --hidden-import=PyQt5.QtWidgets ^
    --collect-all=sounddevice ^
    --collect-all=scipy ^
    --collect-all=novasdr_nr ^
    --copy-metadata=numpy ^
    --copy-metadata=scipy ^
    novasdr_gui_qt.py

echo.
echo Build complete!
echo Application: dist\LU2MET_NR.exe
echo.
echo To run: dist\LU2MET_NR.exe
echo.
echo File size should be approximately 100-150 MB
echo.
echo Note: The application includes all dependencies and the NovaSDR Rust module.
pause
