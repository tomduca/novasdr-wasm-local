#!/bin/bash
# Run NovaSDR Audio Processor Standalone App

cd "$(dirname "$0")"
source venv/bin/activate

python3 novasdr_app.py
