#!/usr/bin/env python3
"""
Create app icons from radio emoji
Requires: pip install pillow
"""

from PIL import Image, ImageDraw, ImageFont
import sys

def create_icon_image(size, emoji="📻"):
    """Create a square image with emoji"""
    # Create image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Try to use system font that supports emoji
    try:
        # macOS
        font = ImageFont.truetype("/System/Library/Fonts/Apple Color Emoji.ttc", int(size * 0.8))
    except:
        try:
            # Windows
            font = ImageFont.truetype("seguiemj.ttf", int(size * 0.8))
        except:
            # Fallback - create a simple colored circle
            draw.ellipse([size*0.1, size*0.1, size*0.9, size*0.9], fill=(59, 130, 246, 255))
            return img
    
    # Draw emoji centered
    bbox = draw.textbbox((0, 0), emoji, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    position = ((size - text_width) // 2, (size - text_height) // 2 - bbox[1])
    
    draw.text(position, emoji, font=font, embedded_color=True)
    return img

def create_ico(output_path):
    """Create Windows .ico file with multiple sizes"""
    sizes = [16, 32, 48, 64, 128, 256]
    images = [create_icon_image(size) for size in sizes]
    images[0].save(output_path, format='ICO', sizes=[(s, s) for s in sizes])
    print(f"✓ Created {output_path}")

def create_png(output_path, size=512):
    """Create PNG file for macOS"""
    img = create_icon_image(size)
    img.save(output_path, format='PNG')
    print(f"✓ Created {output_path}")

if __name__ == "__main__":
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("Error: Pillow not installed")
        print("Install with: pip install pillow")
        sys.exit(1)
    
    # Create Windows icon
    create_ico("app_icon.ico")
    
    # Create PNG for macOS (will need to convert to .icns)
    create_png("app_icon.png", 512)
    
    print("\nNext steps:")
    print("macOS: Convert PNG to ICNS:")
    print("  mkdir app_icon.iconset")
    print("  sips -z 16 16 app_icon.png --out app_icon.iconset/icon_16x16.png")
    print("  sips -z 32 32 app_icon.png --out app_icon.iconset/icon_16x16@2x.png")
    print("  sips -z 32 32 app_icon.png --out app_icon.iconset/icon_32x32.png")
    print("  sips -z 64 64 app_icon.png --out app_icon.iconset/icon_32x32@2x.png")
    print("  sips -z 128 128 app_icon.png --out app_icon.iconset/icon_128x128.png")
    print("  sips -z 256 256 app_icon.png --out app_icon.iconset/icon_128x128@2x.png")
    print("  sips -z 256 256 app_icon.png --out app_icon.iconset/icon_256x256.png")
    print("  sips -z 512 512 app_icon.png --out app_icon.iconset/icon_256x256@2x.png")
    print("  sips -z 512 512 app_icon.png --out app_icon.iconset/icon_512x512.png")
    print("  iconutil -c icns app_icon.iconset")
