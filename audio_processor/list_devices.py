#!/usr/bin/env python3
"""
Script simple para listar dispositivos de audio
"""
import sounddevice as sd

print("\n" + "="*60)
print("  DISPOSITIVOS DE AUDIO DISPONIBLES")
print("="*60 + "\n")

try:
    devices = sd.query_devices()
    print(devices)
    print("\n" + "="*60)
    print("  INSTRUCCIONES")
    print("="*60 + "\n")
    print("Busca en la lista:")
    print("  - BlackHole 2ch (para INPUT)")
    print("  - Tus auriculares/parlantes (para OUTPUT)")
    print("\nEjemplo de uso:")
    print("  python audio_processor.py --band 40m --mode SSB --input X --output Y")
    print("\n")
except Exception as e:
    print(f"Error: {e}")
    print("\nPosibles causas:")
    print("1. macOS necesita permisos de micrófono")
    print("   Ve a: System Settings → Privacy & Security → Microphone")
    print("   Habilita Terminal o tu IDE")
    print("\n2. Problemas con sounddevice")
    print("   Reinstala: pip install --force-reinstall sounddevice")
    print()
