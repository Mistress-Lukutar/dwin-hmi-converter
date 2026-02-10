"""DGUS project preparation module.

This module provides functionality for preparing files for DWIN DGUS
project integration, including file mapping, touch area configuration,
and project structure creation.
"""

import logging
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from PIL import Image, ImageDraw, ImageFont

from src.config_loader import ProjectConfig

logger = logging.getLogger(__name__)


class DgusPreparer:
    """Prepares files for DWIN DGUS project integration.
    
    This class handles the copying and organization of BMP files
    into the DGUS project structure, along with configuration guides.
    
    Attributes:
        config: Project configuration.
        dgus_dir: Path to DGUS project directory.
        dwin_set_dir: Path to DWIN_SET directory.
    
    Example:
        >>> preparer = DgusPreparer(config)
        >>> preparer.prepare_project()
    """
    
    def __init__(self, config: ProjectConfig):
        """Initialize the DgusPreparer.
        
        Args:
            config: Project configuration object.
        """
        self.config = config
        self.dgus_dir = config.get_dgus_path()
        self.dwin_set_dir = config.get_dwin_set_path()
    
    def prepare_project(self) -> bool:
        """Prepare the complete DGUS project.
        
        Copies page files to DWIN_SET directory with DGUS naming,
        creates touch area guide, and creates pages info file.
        
        Returns:
            True if preparation was successful, False otherwise.
        """
        logger.info("=" * 70)
        logger.info("Preparing DGUS project files")
        logger.info("=" * 70)
        
        # Check source directory exists
        pages_dir = self.config.get_pages_output_path()
        if not pages_dir.exists():
            logger.error("Output pages directory not found!")
            logger.error("Run converter first: python scripts/convert.py")
            return False
        
        # Ensure DWIN_SET directory exists
        self.dwin_set_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy files according to mapping
        copied, errors = self._copy_page_files(pages_dir)
        
        # Print results
        logger.info(f"\nCopied {len(copied)} files:")
        for msg in copied:
            logger.info(f"  {msg}")
        
        if errors:
            logger.warning(f"\nSkipped {len(errors)} files:")
            for msg in errors:
                logger.warning(f"  {msg}")
        
        # Create configuration files
        self._create_touch_guide()
        self._create_pages_info()
        
        # Create template images with element outlines
        self._create_template_images()
        
        logger.info("\n" + "=" * 70)
        logger.info("Done! Files prepared in output/dgus/DWIN_SET/")
        logger.info("Open the project in DGUS Tool and configure touch areas.")
        logger.info("=" * 70)
        
        return len(errors) == 0
    
    def _copy_page_files(
        self,
        pages_dir: Path
    ) -> Tuple[List[str], List[str]]:
        """Copy page files to DWIN_SET with DGUS naming.
        
        Args:
            pages_dir: Source directory with page files.
        
        Returns:
            Tuple of (copied_messages, error_messages).
        """
        copied = []
        errors = []
        
        # Get page mapping from config
        page_mapping = self.config.page_mapping
        
        for src_name, dst_name in page_mapping.items():
            src_path = pages_dir / src_name
            dst_path = self.dwin_set_dir / dst_name
            
            if src_path.exists():
                try:
                    shutil.copy2(src_path, dst_path)
                    copied.append(f"{src_name} -> {dst_name}")
                except Exception as e:
                    errors.append(f"{src_name}: copy failed - {e}")
            else:
                errors.append(f"{src_name}: not found")
        
        return copied, errors
    
    def _create_touch_guide(self) -> None:
        """Create the touch areas configuration guide file from config."""
        touch_map_path = self.dgus_dir / "touch_areas_guide.txt"
        
        try:
            guide_content = self._generate_touch_guide()
            touch_map_path.write_text(guide_content, encoding="utf-8")
            logger.info(f"\nTouch areas guide saved: {touch_map_path}")
        except Exception as e:
            logger.error(f"Failed to create touch guide: {e}")
    
    def _generate_touch_guide(self) -> str:
        """Generate touch areas guide content from configuration.
        
        Returns:
            Formatted guide text.
        """
        lines = [
            "=" * 80,
            "TOUCH AREAS CONFIGURATION GUIDE for DGUS Tool",
            "=" * 80,
            "",
            f"Project: {self.config.name}",
            f"Resolution: {self.config.resolution[0]}x{self.config.resolution[1]}",
            "",
        ]
        
        # Generate table for each page
        for page_num in self.config.get_page_numbers():
            page_name = self.config.get_page_name(page_num)
            page_title = self.config.get_page_title(page_num)
            touch_areas = self.config.get_touch_areas_for_page(page_name)
            
            if not touch_areas:
                continue
            
            lines.extend([
                f"PAGE {page_num:02d} ({page_title or page_name.upper()}):",
                "-" * 80,
                "| Element       | Coordinates | Size      | Action                    |",
                "|---------------|-------------|-----------|---------------------------|",
            ])
            
            for element_name, coords in touch_areas.items():
                x = coords.get("x", 0)
                y = coords.get("y", 0)
                w = coords.get("width", 0)
                h = coords.get("height", 0)
                lines.append(
                    f"| {element_name:<13} | ({x:4d},{y:4d})  | {w:3d}x{h:3d}   |                           |"
                )
            
            lines.append("")
        
        lines.extend([
            "=" * 80,
            "VARIABLE ICON ARCHITECTURE",
            "=" * 80,
            "",
            "For multi-state elements (buttons, indicators):",
            "1. Capture clean background (page without interactive elements)",
            "2. Add Variable Icon control at element position",
            "3. Use captured element states as icon images",
            "4. Add Touch Area for interaction",
            "",
            "Element states captured in output/elements/:",
        ])
        
        for element_name in self.config.element_states.keys():
            states = self.config.element_states[element_name].get("states", [])
            state_names = [s.get("name", "unknown") for s in states]
            lines.append(f"  - {element_name}: {', '.join(state_names)}")
        
        lines.extend([
            "",
            "=" * 80,
        ])
        
        return "\n".join(lines)
    
    def _create_pages_info(self) -> None:
        """Create the pages description file."""
        lines = [
            "DWIN DGUS Page Configuration",
            "=" * 40,
            "",
            f"Project: {self.config.name}",
            f"Resolution: {self.config.resolution[0]}x{self.config.resolution[1]}",
            f"Color Depth: {self.config.bmp_depth}-bit BMP",
            "",
            "Pages:",
            "-" * 40,
        ]
        
        for page_num in self.config.get_page_numbers():
            page_name = self.config.get_page_name(page_num)
            page_title = self.config.get_page_title(page_num)
            bmp_file = f"{page_num:02d}_{page_name}.bmp"
            dgus_file = self.config.page_mapping.get(bmp_file, "N/A")
            
            lines.append(f"Page {page_num:02d}: {page_title or page_name}")
            lines.append(f"  Source: {bmp_file}")
            lines.append(f"  DGUS:   {dgus_file}")
            lines.append("")
        
        lines.extend([
            "Element States:",
            "-" * 40,
        ])
        
        for element_name, element_config in self.config.element_states.items():
            states = [s.get("name") for s in element_config.get("states", [])]
            lines.append(f"  {element_name}: {', '.join(states)}")
        
        pages_info = "\n".join(lines)
        
        pages_info_path = self.dgus_dir / "pages_info.txt"
        
        try:
            pages_info_path.write_text(pages_info, encoding="utf-8")
            logger.info(f"Pages info saved: {pages_info_path}")
        except Exception as e:
            logger.error(f"Failed to create pages info: {e}")
    
    def _create_template_images(self) -> None:
        """Create template images with element outlines and labels.
        
        Generates visual reference images showing element boundaries,
        coordinates, and dimensions overlaid on page screenshots.
        These templates help with DGUS touch area configuration.
        
        Uses element coordinates captured during page screenshot phase.
        Falls back to touch_areas from config if coordinates not available.
        """
        import json as json_module
        
        logger.info("\nCreating template images with element outlines...")
        
        pages_dir = self.config.get_pages_output_path()
        templates_dir = self.dgus_dir / "templates"
        templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Color scheme for different element types
        colors = {
            "button": "#FF0000",      # Red for buttons
            "indicator": "#00FF00",   # Green for indicators  
            "display": "#0000FF",     # Blue for displays
            "default": "#FF00FF",     # Magenta for others
        }
        
        # Element type detection from name
        def get_element_color(name: str) -> str:
            name_lower = name.lower()
            if "btn_" in name_lower or "button" in name_lower:
                return colors["button"]
            elif "led_" in name_lower or "indicator" in name_lower:
                return colors["indicator"]
            elif "display" in name_lower or "status" in name_lower or "temp_" in name_lower:
                return colors["display"]
            return colors["default"]
        
        created_count = 0
        
        for page_num in self.config.get_page_numbers():
            page_name = self.config.get_page_name(page_num)
            page_title = self.config.get_page_title(page_num)
            
            # Try to load captured coordinates first
            coords_file = pages_dir / f"{page_num:02d}_{page_name}_coords.json"
            element_coords = {}
            
            if coords_file.exists():
                try:
                    with open(coords_file, 'r', encoding='utf-8') as f:
                        element_coords = json_module.load(f)
                    logger.debug(f"  Loaded coordinates for {len(element_coords)} elements from {coords_file.name}")
                except Exception as e:
                    logger.warning(f"  Could not load coordinates: {e}")
            
            # Fall back to touch_areas from config
            if not element_coords:
                element_coords = self.config.get_touch_areas_for_page(page_name)
                logger.debug(f"  Using touch_areas from config for {len(element_coords)} elements")
            
            if not element_coords:
                logger.warning(f"  No coordinates for page {page_num}, skipping template")
                continue
            
            # Load page image
            page_file = pages_dir / f"{page_num:02d}_{page_name}.bmp"
            if not page_file.exists():
                logger.warning(f"  Page file not found: {page_file}")
                continue
            
            try:
                # Open and convert to RGB for drawing
                with Image.open(page_file) as img:
                    template_img = img.convert("RGB")
                    draw = ImageDraw.Draw(template_img)
                    
                    # Try to load fonts, fall back to default
                    try:
                        font_label = ImageFont.truetype("arial.ttf", 11)
                        font_coords = ImageFont.truetype("arial.ttf", 9)
                    except:
                        font_label = ImageFont.load_default()
                        font_coords = font_label
                    
                    # Sort elements by size (larger first, so smaller labels appear on top)
                    sorted_elements = sorted(
                        element_coords.items(),
                        key=lambda x: x[1].get("width", 0) * x[1].get("height", 0),
                        reverse=True
                    )
                    
                    # Draw each element
                    for element_name, coords in sorted_elements:
                        x = coords.get("x", 0)
                        y = coords.get("y", 0)
                        w = coords.get("width", 0)
                        h = coords.get("height", 0)
                        
                        if w <= 0 or h <= 0:
                            continue
                        
                        color = get_element_color(element_name)
                        
                        # Draw rectangle outline (2px width)
                        draw.rectangle(
                            [x, y, x + w, y + h],
                            outline=color,
                            width=2
                        )
                        
                        # Prepare label text
                        label = element_name
                        coords_text = f"({x},{y}) {w}x{h}"
                        
                        # Calculate text dimensions
                        try:
                            bbox_label = draw.textbbox((0, 0), label, font=font_label)
                            bbox_coords = draw.textbbox((0, 0), coords_text, font=font_coords)
                            
                            text_w = max(bbox_label[2] - bbox_label[0], bbox_coords[2] - bbox_coords[0])
                            text_h_label = bbox_label[3] - bbox_label[1]
                            text_h_coords = bbox_coords[3] - bbox_coords[1]
                            total_text_h = text_h_label + text_h_coords + 2
                        except:
                            # Fallback for older PIL versions
                            text_w = len(label) * 6
                            total_text_h = 20
                        
                        # Position label above element, ensuring it stays within image
                        label_y = y - total_text_h - 6
                        if label_y < 0:
                            label_y = y + h + 2  # Place below if no room above
                        
                        # Draw text background
                        bg_padding = 2
                        draw.rectangle(
                            [x, label_y, x + text_w + bg_padding * 4, label_y + total_text_h + bg_padding * 2],
                            fill="#000000"
                        )
                        
                        # Draw text
                        draw.text(
                            (x + bg_padding, label_y + bg_padding),
                            label,
                            fill=color,
                            font=font_label
                        )
                        draw.text(
                            (x + bg_padding, label_y + bg_padding + text_h_label + 1),
                            coords_text,
                            fill="#FFFFFF",
                            font=font_coords
                        )
                    
                    # Add page title at top
                    title_text = f"Page {page_num}: {page_title or page_name}"
                    try:
                        title_bbox = draw.textbbox((0, 0), title_text, font=font_label)
                        title_w = title_bbox[2] - title_bbox[0]
                        title_h = title_bbox[3] - title_bbox[1]
                        
                        # Title background at top-left
                        draw.rectangle(
                            [5, 5, 10 + title_w, 10 + title_h + 4],
                            fill="#000000"
                        )
                        draw.text((7, 7), title_text, fill="#FFFFFF", font=font_label)
                    except:
                        pass
                    
                    # Add legend
                    legend_items = [
                        ("Buttons", colors["button"]),
                        ("Indicators", colors["indicator"]),
                        ("Displays", colors["display"]),
                    ]
                    legend_y = 30
                    for item_name, item_color in legend_items:
                        draw.rectangle([5, legend_y, 15, legend_y + 8], fill=item_color)
                        draw.text((18, legend_y), item_name, fill="#FFFFFF", font=font_coords)
                        legend_y += 12
                    
                    # Save template image
                    template_file = templates_dir / f"template_{page_num:02d}_{page_name}.bmp"
                    template_img.save(template_file, "BMP")
                    created_count += 1
                    logger.info(f"  Created: {template_file.name} ({len(sorted_elements)} elements)")
                    
            except Exception as e:
                logger.error(f"  Failed to create template for page {page_num}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        if created_count > 0:
            logger.info(f"\nTemplate images saved to: {templates_dir}")
            logger.info("Use these for reference when configuring touch areas in DGUS Tool")
        else:
            logger.info("No template images created (no coordinates available)")
    
    def get_page_mapping(self) -> Dict[str, str]:
        """Get the page file mapping.
        
        Returns:
            Dictionary mapping source filenames to DGUS filenames.
        """
        return self.config.page_mapping.copy()
