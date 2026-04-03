#!/usr/bin/env python3
"""Fix icon by making it square and properly sized"""

from PIL import Image

# Open the original icon
img = Image.open('../icono.png')
print(f"Original size: {img.size}")

# Make it square by adding padding
width, height = img.size
max_size = max(width, height)

# Create square canvas with transparent background
square_img = Image.new('RGBA', (max_size, max_size), (0, 0, 0, 0))

# Paste original image centered
x_offset = (max_size - width) // 2
y_offset = (max_size - height) // 2
square_img.paste(img, (x_offset, y_offset))

# Resize to 1024x1024 for best quality
square_img = square_img.resize((1024, 1024), Image.Resampling.LANCZOS)

# Save as PNG
square_img.save('icon_square.png')
print(f"Created square icon: 1024x1024")

# Create Windows .ico with proper sizes
sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
images = []
for size in sizes:
    resized = square_img.resize(size, Image.Resampling.LANCZOS)
    # Convert RGBA to RGB for better .ico compatibility
    if resized.mode == 'RGBA':
        background = Image.new('RGB', resized.size, (255, 255, 255))
        background.paste(resized, mask=resized.split()[3])
        resized = background
    images.append(resized)

images[0].save('app_icon.ico', format='ICO', sizes=sizes, append_images=images[1:])
print('✓ Created app_icon.ico')

print('\nNow creating macOS .icns...')
