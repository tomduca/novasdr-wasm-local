#!/bin/bash

# Script para ejecutar el procesador de audio con el entorno virtual

# Activar el entorno virtual
source venv/bin/activate

# Ejecutar el procesador con los argumentos proporcionados
python audio_processor.py "$@"
