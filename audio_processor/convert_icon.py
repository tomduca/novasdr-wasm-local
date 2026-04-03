#!/usr/bin/env python3
"""Convert icon to .ico format for Windows"""

from PIL import Image

# Open the icon
img = Image.open('../icono.png')

# Convert to RGB if needed (remove alpha for better compatibility)
if img.mode == 'RGBA':
    # Create white background
    background = Image.new('RGB', img.size, (255, 255, 255))
    background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
    img = background

# Create .ico with multiple sizes
sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
img.save('app_icon.ico', format='ICO', sizes=sizes)
print('✓ Created app_icon.ico')
