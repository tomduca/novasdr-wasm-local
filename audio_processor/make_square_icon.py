#!/usr/bin/env python3
"""Make icon perfectly square"""

from PIL import Image

# Open the icon
img = Image.open('../icon.png')
print(f"Original size: {img.size}")

width, height = img.size

# If already square, just resize
if width == height:
    print("Icon is already square!")
    square_img = img
else:
    # Make it square by cropping or padding
    max_size = max(width, height)
    
    # Create square canvas with same background color as icon edges
    # Sample the corner color
    if img.mode == 'RGBA':
        # Use the top-left corner color
        bg_color = img.getpixel((0, 0))
    else:
        bg_color = img.getpixel((0, 0))
    
    square_img = Image.new(img.mode, (max_size, max_size), bg_color)
    
    # Paste original image centered
    x_offset = (max_size - width) // 2
    y_offset = (max_size - height) // 2
    square_img.paste(img, (x_offset, y_offset))
    
    print(f"Made square: {square_img.size}")

# Resize to 1024x1024 for optimal quality
square_img = square_img.resize((1024, 1024), Image.Resampling.LANCZOS)
square_img.save('icon_1024.png')
print(f"✓ Created icon_1024.png (1024x1024)")

# Create .ico for Windows
sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
images = []
for size in sizes:
    resized = square_img.resize(size, Image.Resampling.LANCZOS)
    # Convert RGBA to RGB for .ico
    if resized.mode == 'RGBA':
        background = Image.new('RGB', resized.size, (20, 30, 50))
        background.paste(resized, mask=resized.split()[3])
        resized = background
    images.append(resized)

images[0].save('app_icon.ico', format='ICO', sizes=sizes, append_images=images[1:])
print('✓ Created app_icon.ico')
