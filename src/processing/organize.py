"""Element organization module.

This module provides functionality for organizing UI elements by size
into folder structures suitable for DGUS Variable Icon implementation.
"""

import json
import logging
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

from PIL import Image

from src.config_loader import ProjectConfig

logger = logging.getLogger(__name__)


class ElementOrganizer:
    """Organizes UI elements by size for DGUS Variable Icon implementation.
    
    Groups elements by their dimensions and organizes them into folders:
    - Folder 32: Single icons (unique sizes, 1 element per size)
    - Folders 33+: Groups with multiple elements of the same size
    
    Attributes:
        icon_dir: Root directory for icon folders.
        config: Application configuration.
    
    Example:
        >>> organizer = ElementOrganizer("HMI/ICON")
        >>> groups = organizer.organize_by_size(unique_files, start_folder=32)
    """
    
    def __init__(self, icon_dir: Path, config: Optional[ProjectConfig] = None):
        """Initialize the ElementOrganizer.
        
        Args:
            icon_dir: Path to the icon root directory.
            config: Configuration object. If None, uses default Config.
        """
        self.icon_dir = Path(icon_dir)
        self.config = config or Config()
    
    def organize_by_size(
        self,
        unique_files: List[Path],
        start_folder_num: int = 32
    ) -> Dict[str, dict]:
        """Organize elements by size into DGUS-compatible folders.
        
        Args:
            unique_files: List of paths to unique image files.
            start_folder_num: Starting folder number (DGUS convention: 32).
        
        Returns:
            Dictionary with organization information for each group.
        """
        logger.info("Organizing elements by size...")
        logger.info(f"  Folder {start_folder_num}/ - single icons (unique sizes)")
        logger.info(f"  Folders {start_folder_num + 1}+ - groups with multiple elements")
        
        if not unique_files:
            logger.warning("No files to organize")
            return {}
        
        # Ensure icon directory exists
        self.icon_dir.mkdir(parents=True, exist_ok=True)
        
        # Group files by size
        size_groups = self._group_by_size(unique_files)
        
        if not size_groups:
            logger.warning("Failed to group files by size")
            return {}
        
        # Separate single icons from groups
        single_icons = []
        multi_groups = {}
        
        for size_key, files in size_groups.items():
            if len(files) == 1:
                single_icons.append(files[0])
            else:
                multi_groups[size_key] = files
        
        logger.info(f"Found {len(size_groups)} size groups:")
        logger.info(f"  - Single icons (unique): {len(single_icons)}")
        logger.info(f"  - Multi-element groups: {len(multi_groups)}")
        
        groups_info = {}
        
        # Create folder for single icons
        if single_icons:
            folder_info = self._create_icon_folder(
                single_icons, 
                start_folder_num,
                "Single icons (unique sizes)"
            )
            groups_info['single_icons'] = folder_info
        
        # Create folders for multi-element groups
        if multi_groups:
            # Sort by area (width * height) for consistent ordering
            sorted_sizes = sorted(
                multi_groups.keys(),
                key=lambda s: int(s.split('x')[0]) * int(s.split('x')[1])
            )
            
            folder_num = start_folder_num + 1
            
            for size_key in sorted_sizes:
                files = multi_groups[size_key]
                folder_info = self._create_icon_folder(
                    files,
                    folder_num,
                    f"Size {size_key}"
                )
                groups_info[size_key] = folder_info
                folder_num += 1
        
        # Create info file
        self._create_groups_info(groups_info, multi_groups, start_folder_num)
        
        total_folders = (1 if single_icons else 0) + len(multi_groups)
        logger.info(f"Organization complete:")
        logger.info(f"  Created {total_folders} folders in {self.icon_dir}")
        
        return groups_info
    
    def _group_by_size(self, file_paths: List[Path]) -> Dict[str, List[Path]]:
        """Group image files by their dimensions.
        
        Args:
            file_paths: List of paths to image files.
        
        Returns:
            Dictionary mapping "WxH" size strings to file lists.
        """
        size_groups = defaultdict(list)
        
        for filepath in file_paths:
            try:
                with Image.open(filepath) as img:
                    size_key = f"{img.size[0]}x{img.size[1]}"
                    size_groups[size_key].append(filepath)
            except Exception as e:
                logger.warning(f"Failed to read {filepath.name}: {e}")
                continue
        
        return dict(size_groups)
    
    def _create_icon_folder(
        self,
        files: List[Path],
        folder_num: int,
        description: str
    ) -> dict:
        """Create an icon folder and copy files with DGUS naming.
        
        Args:
            files: List of files to copy.
            folder_num: Folder number (e.g., 32, 33).
            description: Description for this group.
        
        Returns:
            Dictionary with folder information.
        """
        folder_name = f"{folder_num:02d}"
        group_folder = self.icon_dir / folder_name
        group_folder.mkdir(exist_ok=True)
        
        # Sort files by name for deterministic ordering
        files = sorted(files, key=lambda x: x.name)
        
        logger.info(f"\n  Folder {folder_name}/ ({description}): {len(files)} elements")
        
        # Copy files with DGUS naming (00.bmp, 01.bmp, ...)
        for idx, src_file in enumerate(files):
            dst_name = f"{idx:02d}.bmp"
            dst_file = group_folder / dst_name
            
            try:
                shutil.copy2(src_file, dst_file)
                logger.info(f"    {src_file.name} -> {folder_name}/{dst_name}")
            except Exception as e:
                logger.error(f"    Failed to copy {src_file.name}: {e}")
        
        return {
            'folder': folder_name,
            'count': len(files),
            'files': [f.name for f in files],
            'description': description
        }
    
    def _create_groups_info(
        self,
        groups_info: dict,
        multi_groups: dict,
        start_folder_num: int
    ) -> None:
        """Create the icon_groups_info.txt reference file.
        
        Args:
            groups_info: Dictionary with group information.
            multi_groups: Dictionary of multi-element size groups.
            start_folder_num: Starting folder number.
        """
        info_file = self.icon_dir / "icon_groups_info.txt"
        
        with open(info_file, 'w', encoding='utf-8') as f:
            f.write("DGUS ICON Groups Information\n")
            f.write("=" * 60 + "\n\n")
            f.write("Unique elements organized by size:\n")
            f.write(f"- Folder {start_folder_num:02d}/ - single icons (unique sizes)\n")
            f.write(f"- Folders {start_folder_num + 1:02d}+ - groups with multiple elements\n\n")
            
            # Single icons section
            if 'single_icons' in groups_info:
                info = groups_info['single_icons']
                f.write(f"Folder {info['folder']}/ - {info['description']}\n")
                f.write("-" * 40 + "\n")
                
                # Get sizes for single icons
                for idx, fname in enumerate(info['files']):
                    try:
                        # Find original file path
                        for filepath in self.icon_dir.glob(f"*/{fname}"):
                            with Image.open(filepath) as img:
                                size_str = f"{img.size[0]}x{img.size[1]}"
                                f.write(f"  {idx:02d}.bmp <- {fname} ({size_str})\n")
                                break
                    except:
                        f.write(f"  {idx:02d}.bmp <- {fname}\n")
                f.write("\n")
            
            # Multi-element groups section
            if multi_groups:
                f.write("Groups by size:\n")
                f.write("-" * 40 + "\n")
                
                sorted_sizes = sorted(
                    multi_groups.keys(),
                    key=lambda s: int(s.split('x')[0]) * int(s.split('x')[1])
                )
                
                folder_num = start_folder_num + 1
                for size_key in sorted_sizes:
                    folder_name = f"{folder_num:02d}"
                    info = groups_info.get(size_key, {})
                    f.write(f"\nFolder {folder_name}/ - Size {size_key} ({len(multi_groups[size_key])} elements)\n")
                    f.write("-" * 40 + "\n")
                    
                    for idx, fname in enumerate(sorted([f.name for f in multi_groups[size_key]])):
                        f.write(f"  {idx:02d}.bmp <- {fname}\n")
                    
                    folder_num += 1
            
            # Usage instructions
            f.write("\n\nUsage in DGUS:\n")
            f.write("-" * 40 + "\n")
            f.write("1. Icons are stored in ICON/32/, ICON/33/, etc.\n")
            f.write("2. Folder 32/ contains single icons of different sizes\n")
            f.write("3. Folders 33+ contain groups of same-size icons\n")
            f.write("4. File names: 00.bmp, 01.bmp, 02.bmp, ...\n")
            f.write("5. For Variable Icon: specify folder ID and starting index\n")
        
        logger.info(f"\n  Group info saved: {info_file}")
