#!/bin/bash
# Create app icons for macOS and Windows

echo "Creating app icons..."

# Install pillow if needed
pip install pillow

# Create icons
python3 create_icon.py

# Create macOS .icns file
if [ -f "app_icon.png" ]; then
    echo ""
    echo "Creating macOS .icns file..."
    
    # Create iconset directory
    mkdir -p app_icon.iconset
    
    # Generate all required sizes
    sips -z 16 16 app_icon.png --out app_icon.iconset/icon_16x16.png
    sips -z 32 32 app_icon.png --out app_icon.iconset/icon_16x16@2x.png
    sips -z 32 32 app_icon.png --out app_icon.iconset/icon_32x32.png
    sips -z 64 64 app_icon.png --out app_icon.iconset/icon_32x32@2x.png
    sips -z 128 128 app_icon.png --out app_icon.iconset/icon_128x128.png
    sips -z 256 256 app_icon.png --out app_icon.iconset/icon_128x128@2x.png
    sips -z 256 256 app_icon.png --out app_icon.iconset/icon_256x256.png
    sips -z 512 512 app_icon.png --out app_icon.iconset/icon_256x256@2x.png
    sips -z 512 512 app_icon.png --out app_icon.iconset/icon_512x512.png
    sips -z 1024 1024 app_icon.png --out app_icon.iconset/icon_512x512@2x.png
    
    # Convert to .icns
    iconutil -c icns app_icon.iconset
    
    # Clean up
    rm -rf app_icon.iconset
    
    echo "✓ Created app_icon.icns"
fi

echo ""
echo "Icons created:"
echo "  - app_icon.ico (Windows)"
echo "  - app_icon.icns (macOS)"
echo ""
echo "Ready to build apps with icons!"
