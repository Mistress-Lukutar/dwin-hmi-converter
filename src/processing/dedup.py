"""Duplicate removal module.

This module provides functionality for detecting and removing
duplicate image files based on pixel content.
"""

import logging
from collections import defaultdict
from pathlib import Path
from typing import List, Tuple

from PIL import Image

logger = logging.getLogger(__name__)


class DuplicateRemover:
    """Removes duplicate image files based on pixel content.
    
    This class identifies visually identical images by comparing their
    pixel data hashes, keeping only one copy of each unique image.
    
    Attributes:
        elements_dir: Directory containing element images.
    
    Example:
        >>> remover = DuplicateRemover("output/elements")
        >>> removed, kept, unique = remover.remove_duplicates()
        >>> print(f"Removed {removed} duplicates, kept {kept} unique")
    """
    
    def __init__(self, elements_dir: Path):
        """Initialize the DuplicateRemover.
        
        Args:
            elements_dir: Path to the directory containing element images.
        """
        self.elements_dir = Path(elements_dir)
    
    def remove_duplicates(self) -> Tuple[int, int, List[Path]]:
        """Remove duplicate image files.
        
        Groups images by their pixel content hash and keeps only one
        file from each group, removing the rest.
        
        Returns:
            Tuple of (removed_count, kept_count, unique_files_list).
        """
        logger.info("Removing duplicate elements...")
        
        if not self.elements_dir.exists():
            logger.warning(f"Elements directory not found: {self.elements_dir}")
            return 0, 0, []
        
        # Get all BMP files
        element_files = list(self.elements_dir.glob("*.bmp"))
        
        if not element_files:
            logger.info("No elements found to process")
            return 0, 0, []
        
        logger.info(f"Checking {len(element_files)} files for duplicates...")
        
        # Calculate hashes for all files
        file_hashes = self._calculate_hashes(element_files)
        
        if not file_hashes:
            logger.warning("No valid image files found")
            return 0, 0, []
        
        # Group files by hash
        hash_groups = defaultdict(list)
        for filepath, file_hash in file_hashes.items():
            hash_groups[file_hash].append(filepath)
        
        # Process groups
        removed_count = 0
        unique_files = []
        
        for file_hash, duplicate_files in hash_groups.items():
            # Sort by filename for deterministic selection
            duplicate_files.sort(key=lambda x: x.name)
            
            # Keep the first file
            keep_file = duplicate_files[0]
            unique_files.append(keep_file)
            
            # Remove duplicates
            for dup_file in duplicate_files[1:]:
                try:
                    dup_file.unlink()
                    removed_count += 1
                    logger.info(f"  Removed duplicate: {dup_file.name} (kept {keep_file.name})")
                except Exception as e:
                    logger.error(f"  Failed to remove {dup_file.name}: {e}")
        
        kept_count = len(unique_files)
        total_before = len(element_files)
        
        logger.info(f"Cleanup complete:")
        logger.info(f"  Total files before: {total_before}")
        logger.info(f"  Duplicates removed: {removed_count}")
        logger.info(f"  Unique files kept: {kept_count}")
        
        return removed_count, kept_count, unique_files
    
    def _calculate_hashes(self, file_paths: List[Path]) -> dict:
        """Calculate pixel hashes for image files.
        
        Args:
            file_paths: List of paths to image files.
        
        Returns:
            Dictionary mapping file paths to their pixel hashes.
        """
        file_hashes = {}
        
        for filepath in file_paths:
            try:
                with Image.open(filepath) as img:
                    # Use pixel data for hashing
                    img_bytes = img.tobytes()
                    file_hash = hash(img_bytes)
                    file_hashes[filepath] = file_hash
            except Exception as e:
                logger.warning(f"Failed to read {filepath.name}: {e}")
                continue
        
        return file_hashes
    
    def find_duplicates(self) -> dict:
        """Find duplicate files without removing them.
        
        Returns:
            Dictionary mapping hashes to lists of duplicate file paths.
        """
        if not self.elements_dir.exists():
            return {}
        
        element_files = list(self.elements_dir.glob("*.bmp"))
        file_hashes = self._calculate_hashes(element_files)
        
        # Group by hash
        hash_groups = defaultdict(list)
        for filepath, file_hash in file_hashes.items():
            hash_groups[file_hash].append(filepath)
        
        # Return only groups with duplicates
        return {
            h: files for h, files in hash_groups.items() 
            if len(files) > 1
        }
