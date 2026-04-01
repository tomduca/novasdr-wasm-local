#!/bin/bash
# Build standalone macOS application (.app bundle)

echo "Building NovaSDR Audio Processor for macOS..."

# Activate virtual environment
source venv/bin/activate

# Install PyInstaller
pip install pyinstaller

# Build the application
pyinstaller --name="NovaSDR Audio Processor" \
    --windowed \
    --onefile \
    --add-data="recordings:recordings" \
    --hidden-import=numpy \
    --hidden-import=scipy \
    --hidden-import=sounddevice \
    --hidden-import=novasdr_nr \
    --hidden-import=pydub \
    --hidden-import=PyQt5 \
    novasdr_gui_qt.py

echo ""
echo "✓ Build complete!"
echo "Application: dist/NovaSDR Audio Processor.app"
echo ""
echo "To run: open 'dist/NovaSDR Audio Processor.app'"
echo ""
echo "The app will automatically open your browser to the interface."
