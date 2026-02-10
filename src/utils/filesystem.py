"""File system utility module.

This module provides helper functions for file system operations
used throughout the application.
"""

import logging
from pathlib import Path
from typing import Union

logger = logging.getLogger(__name__)


def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path as string or Path object.
    
    Returns:
        Path object pointing to the ensured directory.
    
    Example:
        >>> output_dir = ensure_directory("output/pages")
        >>> print(output_dir.exists())
        True
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_absolute_path(filename: Union[str, Path]) -> str:
    """Get absolute file path as URI for browser loading.
    
    Converts a relative or absolute file path to a file:// URI
    that can be loaded by the browser.
    
    Args:
        filename: Path to the file as string or Path object.
    
    Returns:
        File URI string (e.g., "file:///C:/path/to/file.html").
    
    Example:
        >>> uri = get_absolute_path("UI_Non_Auto.html")
        >>> print(uri.startswith("file://"))
        True
    """
    return Path(filename).resolve().as_uri()


def get_file_hash(filepath: Path) -> int:
    """Calculate a simple hash for file comparison.
    
    Uses file size and modification time for quick comparison.
    For more accurate comparison, use image hashing.
    
    Args:
        filepath: Path to the file.
    
    Returns:
        Hash value for the file.
    
    Raises:
        FileNotFoundError: If the file doesn't exist.
    """
    stat = filepath.stat()
    return hash((stat.st_size, stat.st_mtime))


def clean_directory(path: Union[str, Path], pattern: str = "*") -> int:
    """Remove all files matching a pattern from a directory.
    
    Args:
        path: Directory path to clean.
        pattern: Glob pattern for files to remove (default: "*" for all).
    
    Returns:
        Number of files removed.
    
    Example:
        >>> count = clean_directory("output/elements", "*.bmp")
        >>> print(f"Removed {count} files")
    """
    path = Path(path)
    if not path.exists():
        return 0
    
    removed = 0
    for file_path in path.glob(pattern):
        if file_path.is_file():
            try:
                file_path.unlink()
                removed += 1
            except Exception as e:
                logger.warning(f"Failed to remove {file_path}: {e}")
    
    return removed


def copy_file(src: Union[str, Path], dst: Union[str, Path]) -> bool:
    """Copy a file from source to destination.
    
    Creates destination directory if it doesn't exist.
    
    Args:
        src: Source file path.
        dst: Destination file path.
    
    Returns:
        True if copy was successful, False otherwise.
    """
    try:
        src = Path(src)
        dst = Path(dst)
        
        # Ensure destination directory exists
        dst.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy file with metadata
        import shutil
        shutil.copy2(src, dst)
        return True
        
    except Exception as e:
        logger.error(f"Failed to copy {src} to {dst}: {e}")
        return False
