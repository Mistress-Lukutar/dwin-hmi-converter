"""
Utility module.

This module provides helper functions for file system operations,
image processing, and other common tasks.
"""

from .filesystem import ensure_directory, get_absolute_path
from .image import convert_to_bmp, create_template_image

__all__ = ["ensure_directory", "get_absolute_path", "convert_to_bmp", "create_template_image"]
