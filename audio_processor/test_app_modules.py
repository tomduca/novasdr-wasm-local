#!/usr/bin/env python3
"""Test if modules load correctly in the app"""

import sys
print("Python executable:", sys.executable)
print("Python version:", sys.version)
print("\nTrying to import modules...")

try:
    import numpy
    print("✓ numpy imported successfully")
    print(f"  Version: {numpy.__version__}")
except Exception as e:
    print(f"✗ numpy failed: {e}")

try:
    import scipy
    print("✓ scipy imported successfully")
    print(f"  Version: {scipy.__version__}")
except Exception as e:
    print(f"✗ scipy failed: {e}")

try:
    import sounddevice
    print("✓ sounddevice imported successfully")
    print(f"  Version: {sounddevice.__version__}")
except Exception as e:
    print(f"✗ sounddevice failed: {e}")

try:
    import novasdr_nr
    print("✓ novasdr_nr imported successfully")
    print(f"  Location: {novasdr_nr.__file__}")
    
    # Try to create an instance
    nr = novasdr_nr.SpectralNoiseReduction(48000, 1.0/16384.0, 0.99, 1.0)
    print("✓ SpectralNoiseReduction created successfully")
    
    # Try to process some data
    import numpy as np
    test_data = np.random.randn(2048).astype(np.float32)
    result = nr.process(test_data)
    print(f"✓ Processing works! Input: {len(test_data)}, Output: {len(result)}")
    
except Exception as e:
    print(f"✗ novasdr_nr failed: {e}")
    import traceback
    traceback.print_exc()

try:
    from PyQt5 import QtWidgets
    print("✓ PyQt5 imported successfully")
except Exception as e:
    print(f"✗ PyQt5 failed: {e}")

print("\nAll tests complete!")
input("Press Enter to exit...")
