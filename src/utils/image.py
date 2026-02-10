"""Image processing utility module.

This module provides helper functions for image processing operations
used throughout the application.
"""

import logging
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


def convert_to_bmp(
    img: Image.Image,
    filename: Path,
    target_mode: str = 'RGB'
) -> bool:
    """Convert an image to 24-bit BMP format.
    
    Args:
        img: PIL Image to convert.
        filename: Output file path.
        target_mode: Target color mode (default: 'RGB' for 24-bit).
    
    Returns:
        True if conversion was successful, False otherwise.
    """
    try:
        if img.mode != target_mode:
            img = img.convert(target_mode)
        img.save(filename, 'BMP')
        return True
    except Exception as e:
        logger.error(f"Failed to convert image to BMP: {e}")
        return False


def create_template_image(
    base_image: Image.Image,
    buttons_info: dict,
    colors: Optional[dict] = None
) -> Image.Image:
    """Create a template image with button outlines.
    
    Draws colored rectangles around buttons and adds coordinate labels.
    
    Args:
        base_image: Base screenshot image.
        buttons_info: Dictionary mapping button names to coordinates.
        colors: Optional color mapping for buttons.
    
    Returns:
        Modified image with button outlines.
    """
    # Default color mapping
    if colors is None:
        colors = {
            'btn_move': '#FF0000',
            'btn_heater': '#00FF00',
            'btn_settings': '#0000FF',
            'btn_logs': '#FF00FF'
        }
    
    # Create drawing context
    draw = ImageDraw.Draw(base_image)
    
    # Try to load fonts
    try:
        font = ImageFont.truetype("arial.ttf", 14)
        font_small = ImageFont.truetype("arial.ttf", 11)
    except:
        font = ImageFont.load_default()
        font_small = font
    
    # Draw each button's outline and label
    for name, coords in buttons_info.items():
        x, y = coords['x'], coords['y']
        w, h = coords['width'], coords['height']
        color = colors.get(name, '#FFFFFF')
        
        # Draw outline rectangle
        draw.rectangle([x, y, x + w, y + h], outline=color, width=3)
        
        # Create label with coordinates
        label = f"{name}\n({x},{y}) {w}x{h}"
        
        # Calculate text dimensions
        bbox = draw.textbbox((0, 0), label, font=font_small)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        
        # Draw text background
        draw.rectangle(
            [x, y - text_h - 4, x + text_w + 4, y],
            fill='#000000'
        )
        
        # Draw text
        draw.text((x + 2, y - text_h - 2), label, fill=color, font=font_small)
    
    return base_image


def get_image_hash(img: Image.Image) -> int:
    """Calculate a hash for image comparison.
    
    Uses pixel data for accurate comparison.
    
    Args:
        img: PIL Image to hash.
    
    Returns:
        Hash value for the image.
    """
    return hash(img.tobytes())


def get_image_info(img_path: Path) -> Optional[dict]:
    """Get information about an image file.
    
    Args:
        img_path: Path to the image file.
    
    Returns:
        Dictionary with image information or None if failed.
    """
    try:
        with Image.open(img_path) as img:
            return {
                'filename': img_path.name,
                'format': img.format,
                'mode': img.mode,
                'size': img.size,
                'width': img.size[0],
                'height': img.size[1],
            }
    except Exception as e:
        logger.error(f"Failed to get image info for {img_path}: {e}")
        return None


def resize_if_needed(
    img: Image.Image,
    target_size: Tuple[int, int],
    resample: int = Image.Resampling.LANCZOS
) -> Image.Image:
    """Resize an image if it doesn't match the target size.
    
    Args:
        img: PIL Image to resize.
        target_size: Target (width, height) tuple.
        resample: Resampling filter (default: LANCZOS).
    
    Returns:
        Resized image or original if already correct size.
    """
    if img.size != target_size:
        return img.resize(target_size, resample)
    return img


def validate_bmp(img_path: Path, expected_size: Optional[Tuple[int, int]] = None) -> dict:
    """Validate a BMP file against DWIN requirements.
    
    Args:
        img_path: Path to the BMP file.
        expected_size: Optional expected (width, height) tuple.
    
    Returns:
        Dictionary with validation results:
        - valid: Whether the file is valid
        - format: Image format
        - mode: Color mode
        - size: Image size
        - errors: List of error messages if any
    """
    result = {
        'valid': False,
        'format': None,
        'mode': None,
        'size': None,
        'errors': []
    }
    
    try:
        with Image.open(img_path) as img:
            result['format'] = img.format
            result['mode'] = img.mode
            result['size'] = img.size
            
            # Check format
            if img.format != 'BMP':
                result['errors'].append(f"Not a BMP file (found: {img.format})")
            
            # Check color mode (DWIN requires RGB/24-bit)
            if img.mode != 'RGB':
                result['errors'].append(f"Wrong color mode: {img.mode} (expected: RGB)")
            
            # Check size if provided
            if expected_size and img.size != expected_size:
                result['errors'].append(
                    f"Wrong size: {img.size} (expected: {expected_size})"
                )
            
            result['valid'] = len(result['errors']) == 0
            
    except Exception as e:
        result['errors'].append(f"Failed to open image: {e}")
    
    return result
