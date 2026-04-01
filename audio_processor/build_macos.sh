#!/bin/bash
# Build standalone macOS application (.app bundle)

echo "Building NovaSDR Audio Processor for macOS..."

# Activate virtual environment
source venv/bin/activate

# Install PyInstaller
pip install pyinstaller

# Find the novasdr_nr module
NOVASDR_MODULE=$(python3 -c "import novasdr_nr; import os; print(os.path.dirname(novasdr_nr.__file__))")
echo "NovaSDR module found at: $NOVASDR_MODULE"

# Clean previous builds
rm -rf build dist *.spec

# Build the application
pyinstaller --name="NovaSDR Audio Processor" \
    --windowed \
    --onefile \
    --add-data="recordings:recordings" \
    --add-binary="$NOVASDR_MODULE/novasdr_nr*.so:." \
    --hidden-import=numpy \
    --hidden-import=numpy.core._multiarray_umath \
    --hidden-import=scipy \
    --hidden-import=scipy.signal \
    --hidden-import=scipy.fft \
    --hidden-import=sounddevice \
    --hidden-import=_sounddevice \
    --hidden-import=novasdr_nr \
    --hidden-import=pydub \
    --hidden-import=PyQt5 \
    --hidden-import=PyQt5.QtCore \
    --hidden-import=PyQt5.QtGui \
    --hidden-import=PyQt5.QtWidgets \
    --collect-all=sounddevice \
    --collect-all=scipy \
    --copy-metadata=numpy \
    --copy-metadata=scipy \
    novasdr_gui_qt.py

echo ""
echo "✓ Build complete!"
echo "Application: dist/NovaSDR Audio Processor.app"
echo ""
echo "To run: open 'dist/NovaSDR Audio Processor.app'"
echo ""
echo "Note: The app includes all dependencies and the NovaSDR Rust module."
