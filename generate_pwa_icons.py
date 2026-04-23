#!/usr/bin/env python
"""
PWA Icon Generator Script
Generates multiple icon sizes from a single source image.

Usage:
    python generate_pwa_icons.py path/to/your/logo.png

Requirements:
    pip install Pillow
"""

import os
import sys
from pathlib import Path

def generate_icons(source_image_path, output_dir='static'):
    """Generate PWA icons from a source image."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("Error: Pillow is not installed.")
        print("Install it with: pip install Pillow")
        sys.exit(1)
    
    # Check if source image exists
    if not os.path.exists(source_image_path):
        print(f"Error: Source image '{source_image_path}' not found.")
        sys.exit(1)
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Icon sizes needed for PWA
    sizes = [72, 96, 128, 144, 152, 192, 384, 512]
    
    try:
        # Open and convert source image
        img = Image.open(source_image_path).convert('RGBA')
        
        print(f"Generating PWA icons from '{source_image_path}'...")
        print(f"Output directory: '{output_dir}'\n")
        
        for size in sizes:
            # Resize image
            resized = img.resize((size, size), Image.Resampling.LANCZOS)
            
            # Save icon
            output_path = os.path.join(output_dir, f'icon-{size}.png')
            resized.save(output_path, 'PNG')
            
            file_size = os.path.getsize(output_path) / 1024  # Convert to KB
            print(f"✓ Created {output_path} ({file_size:.1f} KB)")
        
        print(f"\n✅ Icon generation complete!")
        print(f"\nNext steps:")
        print(f"1. Verify icons in the {output_dir}/ directory")
        print(f"2. Update manifest.json if needed")
        print(f"3. Test the PWA in your browser")
        
    except Exception as e:
        print(f"Error generating icons: {e}")
        sys.exit(1)

def create_placeholder_icons(output_dir='static'):
    """Create simple placeholder icons if PIL is not available."""
    try:
        from PIL import Image, ImageDraw
        has_pil = True
    except ImportError:
        has_pil = False
    
    os.makedirs(output_dir, exist_ok=True)
    sizes = [72, 96, 128, 144, 152, 192, 384, 512]
    
    if has_pil:
        print("Creating placeholder PWA icons...")
        for size in sizes:
            # Create a simple blue square with white circle
            img = Image.new('RGB', (size, size), color='#4361ee')
            draw = ImageDraw.Draw(img)
            
            # Draw white circle in center
            margin = size // 8
            draw.ellipse(
                [(margin, margin), (size - margin, size - margin)],
                fill='white'
            )
            
            # Save
            output_path = os.path.join(output_dir, f'icon-{size}.png')
            img.save(output_path, 'PNG')
            print(f"✓ Created placeholder {output_path}")
        
        print("\n⚠️  These are placeholder icons. Please replace with your actual logo.")
    else:
        print("⚠️  PIL/Pillow not installed. Cannot create placeholder icons.")
        print("To create icons manually:")
        print("1. Create a logo image (PNG or SVG)")
        print("2. Use https://www.pwabuilder.com/imageGenerator")
        print("3. Download generated icons")
        print("4. Place in the 'static/' directory")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Use provided image
        source = sys.argv[1]
        output = sys.argv[2] if len(sys.argv) > 2 else 'static'
        generate_icons(source, output)
    else:
        # Create placeholder icons
        print("Usage: python generate_pwa_icons.py <source_image.png> [output_dir]")
        print("\nNo image provided. Creating placeholder icons...\n")
        create_placeholder_icons()
