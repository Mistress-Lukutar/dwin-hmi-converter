"""Page screenshot capture module.

This module provides functionality for capturing full-page screenshots
of the HMI interface using Selenium WebDriver.
"""

import json
import logging
import time
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.config_loader import ProjectConfig
from src.capture.element import ElementCapture

logger = logging.getLogger(__name__)


class PageCapture:
    """Captures full-page screenshots of the HMI interface.
    
    This class handles the capture of complete HMI pages and the creation
    of template images with button coordinates for DGUS configuration.
    
    Attributes:
        driver: Selenium WebDriver instance.
        config: Application configuration.
        element_capture: ElementCapture instance for element operations.
    
    Example:
        >>> capture = PageCapture(driver, config)
        >>> capture.capture_page(0, output_dir)  # Capture main page
    """
    
    def __init__(self, driver: WebDriver, config: Optional[ProjectConfig] = None):
        """Initialize the PageCapture.
        
        Args:
            driver: Selenium WebDriver instance.
            config: Configuration object. If None, uses default Config.
        """
        self.driver = driver
        self.config = config or Config()
        self.element_capture = ElementCapture(driver, config)
    
    def capture_full_page(
        self,
        filename: Path,
        container_selector: str = ".hmi-container"
    ) -> bool:
        """Capture a full page screenshot and save as BMP.
        
        Args:
            filename: Output file path for the BMP image.
            container_selector: CSS selector for the page container.
        
        Returns:
            True if capture was successful, False otherwise.
        """
        try:
            # Disable CSS transitions for stable capture
            self._disable_page_transitions()
            time.sleep(self.config.ANIMATION_DISABLE_DELAY)
            
            # Find container element
            container = self.driver.find_element(By.CSS_SELECTOR, container_selector)
            
            # Capture screenshot
            png_data = container.screenshot_as_png
            img = Image.open(BytesIO(png_data))
            
            # Verify resolution
            if img.size != self.config.RESOLUTION:
                logger.warning(
                    f"Screenshot size {img.size} doesn't match expected "
                    f"resolution {self.config.RESOLUTION}. Check Windows "
                    f"scaling or Chrome settings."
                )
            
            # Convert to RGB and save
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            img.save(filename, 'BMP')
            logger.debug(f"Captured page: {filename.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to capture page {filename.name}: {e}")
            return False
    
    def capture_page(
        self,
        page_num: int,
        output_dir: Path,
        suffix: str = ""
    ) -> bool:
        """Switch to a page and capture a screenshot.
        
        Args:
            page_num: Page number to capture (0-3).
            output_dir: Directory to save the screenshot.
            suffix: Optional suffix for the filename.
        
        Returns:
            True if capture was successful, False otherwise.
        """
        page_name = self.config.get_page_name(page_num)
        file_suffix = f"_{suffix}" if suffix else ""
        
        try:
            # Switch to the page via JavaScript
            self.driver.execute_script(f"changePage({page_num})")
            time.sleep(self.config.PAGE_TRANSITION_DELAY)
            
            # Capture screenshot
            output_file = output_dir / f"{page_num:02d}_{page_name}{file_suffix}.bmp"
            if self.capture_full_page(output_file):
                mode_str = f" [{suffix}]" if suffix else ""
                logger.info(f"  Captured page {page_name}{mode_str} ({page_num})")
                return True
                
        except Exception as e:
            logger.error(f"Failed to capture page {page_name}: {e}")
        
        return False
    
    def capture_all_pages(self, output_dir: Path) -> List[str]:
        """Capture screenshots of all pages with element coordinates.
        
        Args:
            output_dir: Directory to save screenshots.
        
        Returns:
            List of successfully captured page names.
        """
        captured = []
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for page_num in self.config.get_page_numbers():
            if self.capture_page_with_elements(page_num, output_dir):
                page_name = self.config.get_page_name(page_num)
                captured.append(page_name)
        
        return captured
    
    def capture_page_with_elements(
        self,
        page_num: int,
        output_dir: Path
    ) -> bool:
        """Capture a page and save element coordinates.
        
        Args:
            page_num: Page number to capture.
            output_dir: Directory to save the screenshot and coordinates.
        
        Returns:
            True if capture was successful, False otherwise.
        """
        # First capture the page
        if not self.capture_page(page_num, output_dir):
            return False
        
        # Get element coordinates for this page
        try:
            coords = self._get_element_coordinates_for_page(page_num)
            if coords:
                # Save coordinates to JSON
                coords_file = output_dir / f"{page_num:02d}_{self.config.get_page_name(page_num)}_coords.json"
                with open(coords_file, 'w', encoding='utf-8') as f:
                    json.dump(coords, f, indent=2, ensure_ascii=False)
                logger.debug(f"  Saved coordinates for {len(coords)} elements")
        except Exception as e:
            logger.warning(f"  Could not save coordinates: {e}")
        
        return True
    
    def _get_element_coordinates_for_page(self, page_num: int) -> Dict[str, dict]:
        """Get coordinates of all elements on a page via JavaScript.
        
        Args:
            page_num: Page number.
        
        Returns:
            Dictionary mapping element names to their coordinates.
        """
        # Collect all selectors for this page
        elements_to_find = {}
        
        # From elements config
        for name, selector in self.config.elements.items():
            elements_to_find[name] = selector
        
        # From element_states config (they have page specified)
        for name, config in self.config.element_states.items():
            if config.get("page") == page_num:
                elements_to_find[name] = config.get("selector", "")
        
        if not elements_to_find:
            return {}
        
        # Build JavaScript to find all elements
        js_code = """
            var elements = %s;
            var results = {};
            
            for (var name in elements) {
                var selector = elements[name];
                try {
                    var el = document.querySelector(selector);
                    if (el) {
                        var rect = el.getBoundingClientRect();
                        results[name] = {
                            x: Math.round(rect.left),
                            y: Math.round(rect.top),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height),
                            selector: selector
                        };
                    }
                } catch (e) {
                    // Element not found or invalid selector
                }
            }
            
            return results;
        """ % json.dumps(elements_to_find)
        
        try:
            return self.driver.execute_script(js_code)
        except Exception as e:
            logger.warning(f"Failed to get element coordinates: {e}")
            return {}
    
    def capture_clean_background(
        self,
        output_dir: Path
    ) -> Dict[str, dict]:
        """Capture clean background (without buttons) and create template.
        
        Creates a clean background image for Variable Icon implementation
        and a template with button outlines and coordinates.
        
        Args:
            output_dir: Directory to save the images.
        
        Returns:
            Dictionary mapping button names to their coordinates.
        """
        logger.info("Creating clean background and template...")
        
        try:
            # Switch to main page
            self.driver.execute_script("changePage(0)")
            time.sleep(self.config.PAGE_TRANSITION_DELAY)
            
            # Get button coordinates before hiding
            buttons_info = self._get_button_coordinates()
            
            # Hide buttons for clean background
            self._hide_buttons()
            time.sleep(0.2)
            
            # Capture clean background
            output_file = output_dir / "00_main_bg_clean.bmp"
            if self.capture_full_page(output_file):
                logger.info(f"  Clean background saved: {output_file.name}")
            
            # Restore buttons for template
            self._show_buttons()
            time.sleep(0.2)
            
            # Create template with outlines
            self._create_template(output_dir, buttons_info)
            
            # Save coordinates to JSON
            coords_file = output_dir / "button_coordinates.json"
            with open(coords_file, 'w', encoding='utf-8') as f:
                json.dump(buttons_info, f, indent=2, ensure_ascii=False)
            logger.info(f"  Coordinates saved: {coords_file.name}")
            
            return buttons_info
            
        except Exception as e:
            logger.error(f"Failed to create clean background: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def _get_button_coordinates(self) -> Dict[str, dict]:
        """Get coordinates of main buttons via JavaScript.
        
        Returns:
            Dictionary mapping button names to coordinate dictionaries.
        """
        return self.driver.execute_script("""
            var buttons = [
                {id: 'btnMove', name: 'btn_move'},
                {id: 'btnHeater', name: 'btn_heater'},
                {selector: "button[onclick='changePage(1)']", name: 'btn_settings'},
                {selector: "button[onclick='changePage(2)']", name: 'btn_logs'}
            ];
            
            var results = {};
            buttons.forEach(function(btn) {
                var el = btn.id ? document.getElementById(btn.id) 
                                : document.querySelector(btn.selector);
                if (el) {
                    var rect = el.getBoundingClientRect();
                    results[btn.name] = {
                        x: Math.round(rect.left),
                        y: Math.round(rect.top),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    };
                }
            });
            return results;
        """)
    
    def _hide_buttons(self) -> None:
        """Hide control buttons via JavaScript."""
        self.driver.execute_script("""
            document.querySelectorAll('.control-buttons, .btn-main, 
                                       button[onclick^="changePage"]').forEach(
                function(el) { el.style.visibility = 'hidden'; }
            );
            document.querySelectorAll('.nav-buttons button').forEach(
                function(el) { el.style.visibility = 'hidden'; }
            );
            document.body.offsetHeight;
        """)
    
    def _show_buttons(self) -> None:
        """Show control buttons via JavaScript."""
        self.driver.execute_script("""
            document.querySelectorAll('.control-buttons, .btn-main, 
                                       button[onclick^="changePage"]').forEach(
                function(el) { el.style.visibility = 'visible'; }
            );
            document.querySelectorAll('.nav-buttons button').forEach(
                function(el) { el.style.visibility = 'visible'; }
            );
            document.body.offsetHeight;
        """)
    
    def _create_template(
        self,
        output_dir: Path,
        buttons_info: Dict[str, dict]
    ) -> None:
        """Create template image with button outlines.
        
        Args:
            output_dir: Directory to save the template.
            buttons_info: Dictionary of button coordinates.
        """
        # Capture base image
        container = self.driver.find_element(By.CSS_SELECTOR, ".hmi-container")
        png_data = container.screenshot_as_png
        img = Image.open(BytesIO(png_data))
        
        # Draw outlines and labels
        draw = ImageDraw.Draw(img)
        
        # Try to load fonts, fall back to default
        try:
            font = ImageFont.truetype("arial.ttf", 14)
            font_small = ImageFont.truetype("arial.ttf", 11)
        except:
            font = ImageFont.load_default()
            font_small = font
        
        # Color mapping for different buttons
        colors = {
            'btn_move': '#FF0000',
            'btn_heater': '#00FF00',
            'btn_settings': '#0000FF',
            'btn_logs': '#FF00FF'
        }
        
        # Draw each button's outline and label
        for name, coords in buttons_info.items():
            x, y = coords['x'], coords['y']
            w, h = coords['width'], coords['height']
            color = colors.get(name, '#FFFFFF')
            
            # Draw outline
            draw.rectangle([x, y, x + w, y + h], outline=color, width=3)
            
            # Create label with coordinates
            label = f"{name}\n({x},{y}) {w}x{h}"
            
            # Draw label background
            bbox = draw.textbbox((0, 0), label, font=font_small)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            draw.rectangle([x, y - text_h - 4, x + text_w + 4, y], 
                          fill='#000000')
            
            # Draw label text
            draw.text((x + 2, y - text_h - 2), label, fill=color, 
                     font=font_small)
        
        # Save template
        template_file = output_dir / "00_main_template.bmp"
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img.save(template_file, 'BMP')
        logger.info(f"  Template saved: {template_file.name}")
    
    def _disable_page_transitions(self) -> None:
        """Disable CSS transitions on the page."""
        self.driver.execute_script("""
            document.querySelectorAll('.btn, .indicator, .led').forEach(
                function(el) {
                    el.style.transition = 'none';
                    el.style.animation = 'none';
                }
            );
            document.body.offsetHeight;
        """)
