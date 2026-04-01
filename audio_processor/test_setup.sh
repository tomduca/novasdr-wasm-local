#!/bin/bash

# Script de prueba rápida para HF Audio Processor
# Uso: ./test_setup.sh

echo "=========================================="
echo "  HF Audio Processor - Test Setup"
echo "=========================================="
echo ""

# Verificar Python
echo "1. Verificando Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "   ✓ $PYTHON_VERSION"
else
    echo "   ✗ Python 3 no encontrado"
    exit 1
fi

# Verificar dependencias
echo ""
echo "2. Verificando dependencias..."
python3 -c "import sounddevice" 2>/dev/null && echo "   ✓ sounddevice" || echo "   ✗ sounddevice (pip install sounddevice)"
python3 -c "import numpy" 2>/dev/null && echo "   ✓ numpy" || echo "   ✗ numpy (pip install numpy)"
python3 -c "import scipy" 2>/dev/null && echo "   ✓ scipy" || echo "   ✗ scipy (pip install scipy)"
python3 -c "import pyrnnoise" 2>/dev/null && echo "   ✓ pyrnnoise (AI enabled)" || echo "   ⚠ pyrnnoise (AI disabled - pip install pyrnnoise)"

# Listar dispositivos
echo ""
echo "3. Dispositivos de audio disponibles:"
echo ""
python3 audio_processor.py --list-devices

echo ""
echo "=========================================="
echo "  Próximos pasos:"
echo "=========================================="
echo ""
echo "1. Instala BlackHole si no lo tienes:"
echo "   brew install blackhole-2ch"
echo ""
echo "2. Configura macOS para usar BlackHole como salida"
echo ""
echo "3. Abre un webSDR en Chrome:"
echo "   http://websdr.ewi.utwente.nl:8901/"
echo ""
echo "4. Ejecuta el procesador:"
echo "   python3 audio_processor.py --band 40m --input X --output Y"
echo ""
echo "   (Reemplaza X con el ID de BlackHole y Y con tus auriculares)"
echo ""
