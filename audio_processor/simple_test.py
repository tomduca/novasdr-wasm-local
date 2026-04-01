#!/usr/bin/env python3
"""
Test simple sin AI - solo lista dispositivos
"""
import sounddevice as sd

print("\n" + "="*60)
print("  DISPOSITIVOS DE AUDIO")
print("="*60 + "\n")

devices = sd.query_devices()
print(devices)

print("\n" + "="*60)
print("Busca:")
print("  - BlackHole 2ch (INPUT)")
print("  - Tus auriculares (OUTPUT)")
print("="*60 + "\n")
