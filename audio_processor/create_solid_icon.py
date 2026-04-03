#!/usr/bin/env python3
"""Create icon with solid background for better macOS compatibility"""

from PIL import Image, ImageDraw

# Open the original icon
img = Image.open('../icono.png')
print(f"Original size: {img.size}")

# Make it square by adding padding
width, height = img.size
max_size = max(width, height)

# Create square canvas with SOLID DARK BLUE background (matching the icon)
square_img = Image.new('RGB', (max_size, max_size), (20, 30, 50))  # Dark blue

# If original has alpha, composite it properly
if img.mode == 'RGBA':
    # Create a temp image with the background color
    temp = Image.new('RGB', img.size, (20, 30, 50))
    temp.paste(img, (0, 0), img)
    img = temp

# Paste original image centered
x_offset = (max_size - width) // 2
y_offset = (max_size - height) // 2
square_img.paste(img, (x_offset, y_offset))

# Resize to 1024x1024 for best quality
square_img = square_img.resize((1024, 1024), Image.Resampling.LANCZOS)

# Save as PNG
square_img.save('icon_solid.png')
print(f"Created solid background icon: 1024x1024")

# Create Windows .ico
sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
images = []
for size in sizes:
    resized = square_img.resize(size, Image.Resampling.LANCZOS)
    images.append(resized)

images[0].save('app_icon.ico', format='ICO', sizes=sizes, append_images=images[1:])
print('✓ Created app_icon.ico with solid background')
