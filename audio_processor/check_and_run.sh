#!/bin/bash

echo "=============================================="
echo "  Verificación y Setup - HF Audio Processor"
echo "=============================================="
echo ""

# Activar venv
echo "1. Activando entorno virtual..."
source venv/bin/activate
echo "   ✓ Entorno activado"
echo ""

# Verificar BlackHole
echo "2. Verificando BlackHole..."
if system_profiler SPAudioDataType | grep -q "BlackHole"; then
    echo "   ✓ BlackHole está instalado"
else
    echo "   ✗ BlackHole NO está instalado"
    echo ""
    echo "   Para instalar BlackHole:"
    echo "   brew install blackhole-2ch"
    echo ""
    echo "   O descarga desde: https://existential.audio/blackhole/"
    echo ""
fi

# Listar dispositivos
echo "3. Dispositivos de audio disponibles:"
echo ""
python audio_processor.py --list-devices

echo ""
echo "=============================================="
echo "  Siguiente paso:"
echo "=============================================="
echo ""
echo "1. Si tienes BlackHole, configura macOS:"
echo "   System Settings → Sound → Output → BlackHole 2ch"
echo ""
echo "2. Ejecuta el procesador:"
echo "   python audio_processor.py --band 40m --mode SSB --input X --output Y"
echo ""
echo "   Reemplaza X e Y con los números de arriba:"
echo "   X = BlackHole (input)"
echo "   Y = Tus auriculares (output)"
echo ""
