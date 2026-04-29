#!/bin/bash
# Build standalone macOS application (.app bundle)

echo "Building NovaSDR Audio Processor for macOS..."

# Activate virtual environment
source venv/bin/activate

# Install PyInstaller
pip install pyinstaller

# Find the novasdr_nr module (optional)
NOVASDR_MODULE=$(python3 -c "import novasdr_nr; import os; print(os.path.dirname(novasdr_nr.__file__))" 2>/dev/null || echo "")

if [ -n "$NOVASDR_MODULE" ]; then
    echo "NovaSDR module found at: $NOVASDR_MODULE"
    NOVASDR_BINARY="--add-binary=$NOVASDR_MODULE/novasdr_nr*.so:."
else
    echo "NovaSDR module not found - building without it"
    NOVASDR_BINARY=""
fi

# Clean previous builds
rm -rf build dist *.spec

# Build the application
pyinstaller --name="LU2MET_NR" \
    --windowed \
    --onedir \
    --icon=app_icon.icns \
    --osx-bundle-identifier=com.lu2met.nr \
    --add-data="recordings:recordings" \
    $NOVASDR_BINARY \
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
echo "Adding Info.plist with microphone permissions..."
cp Info.plist "dist/LU2MET_NR.app/Contents/Info.plist"

echo "Re-signing application..."
codesign --force --deep --sign - "dist/LU2MET_NR.app"

echo ""
echo "✓ Build complete!"
echo "Application: dist/LU2MET_NR.app"
echo ""
echo "To run: open 'dist/LU2MET_NR.app'"
echo ""
echo "Note: The app includes all dependencies and the NovaSDR Rust module."
echo "Note: First launch will request microphone permissions - click Allow."
