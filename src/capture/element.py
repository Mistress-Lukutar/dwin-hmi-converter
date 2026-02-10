"""Element screenshot capture module.

This module provides functionality for capturing screenshots of individual
UI elements using Selenium WebDriver.
"""

import logging
import time
from io import BytesIO
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver

from src.config_loader import ProjectConfig

logger = logging.getLogger(__name__)


class ElementCapture:
    """Captures screenshots of individual UI elements.
    
    This class handles the capture of individual HTML elements (buttons,
    indicators, displays, etc.) and converts them to 24-bit BMP format
    suitable for DWIN displays.
    
    Attributes:
        driver: Selenium WebDriver instance.
        config: Application configuration.
    
    Example:
        >>> capture = ElementCapture(driver, config)
        >>> element = driver.find_element(By.ID, "btnMove")
        >>> capture.capture(element, "output/elem_btn_move.bmp")
    """
    
    def __init__(self, driver: WebDriver, config: Optional[ProjectConfig] = None):
        """Initialize the ElementCapture.
        
        Args:
            driver: Selenium WebDriver instance.
            config: Configuration object. If None, uses default Config.
        """
        self.driver = driver
        self.config = config or Config()
    
    def capture(
        self,
        element: WebElement,
        filename: Path,
        add_background: bool = True,
        bg_color: Optional[Tuple[int, int, int]] = None
    ) -> bool:
        """Capture a screenshot of a single element and save as BMP.
        
        Args:
            element: WebElement to capture.
            filename: Output file path for the BMP image.
            add_background: Whether to add a background color for transparency.
            bg_color: Background color as (R, G, B) tuple. Uses config default if None.
        
        Returns:
            True if capture was successful, False otherwise.
        """
        try:
            # Validate element visibility and size
            if not element.is_displayed():
                logger.debug(f"Element not displayed: {filename.name}")
                return False
            
            size = element.size
            if size['width'] == 0 or size['height'] == 0:
                logger.debug(f"Element has zero size: {filename.name}")
                return False
            
            # Scroll element into view
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
                element
            )
            
            # Disable CSS transitions for stable capture
            self.driver.execute_script("""
                arguments[0].style.transition = 'none !important';
                arguments[0].style.animation = 'none !important';
                arguments[0].offsetHeight; // Trigger reflow
            """, element)
            
            # Wait for transitions to complete
            time.sleep(self.config.ELEMENT_CAPTURE_DELAY)
            
            # Capture screenshot via PNG
            png_data = element.screenshot_as_png
            img = Image.open(BytesIO(png_data))
            
            # Convert to RGB with optional background
            bg_color = bg_color or self.config.BG_COLOR
            img = self._convert_to_rgb(img, add_background, bg_color)
            
            # Save as 24-bit BMP
            img.save(filename, 'BMP')
            logger.debug(f"Captured element: {filename.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to capture element {filename.name}: {e}")
            return False
    
    def capture_by_selector(
        self,
        selector: str,
        filename: Path,
        add_background: bool = True,
        bg_color: Optional[Tuple[int, int, int]] = None
    ) -> bool:
        """Capture element by CSS selector.
        
        Args:
            selector: CSS selector for the element.
            filename: Output file path.
            add_background: Whether to add a background color.
            bg_color: Background color as (R, G, B) tuple.
        
        Returns:
            True if capture was successful, False otherwise.
        """
        try:
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            if not elements:
                logger.warning(f"Element not found: {selector}")
                return False
            return self.capture(elements[0], filename, add_background, bg_color)
        except Exception as e:
            logger.error(f"Failed to capture element by selector {selector}: {e}")
            return False
    
    def capture_multiple(
        self,
        elements_dict: dict,
        output_dir: Path,
        prefix: str = "elem"
    ) -> int:
        """Capture multiple elements from a dictionary.
        
        Args:
            elements_dict: Dictionary mapping {name: css_selector}.
            output_dir: Directory to save captured images.
            prefix: Filename prefix for captured elements.
        
        Returns:
            Number of successfully captured elements.
        """
        success_count = 0
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for name, selector in elements_dict.items():
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if not elements:
                    logger.debug(f"Element not found: {name} ({selector})")
                    continue
                
                for i, element in enumerate(elements):
                    suffix = f"_{i}" if len(elements) > 1 else ""
                    filename = output_dir / f"{prefix}_{name}{suffix}.bmp"
                    
                    if self.capture(element, filename):
                        success_count += 1
                        logger.info(f"  Captured: {name}{suffix}")
                    else:
                        logger.warning(f"  Failed to capture: {name}{suffix}")
                        
            except Exception as e:
                logger.error(f"  Error capturing {name}: {e}")
        
        return success_count
    
    def get_element_info(self, element: WebElement) -> dict:
        """Get information about an element for coordinate tracking.
        
        Args:
            element: WebElement to analyze.
        
        Returns:
            Dictionary with element coordinates and dimensions.
        """
        try:
            rect = self.driver.execute_script("""
                var rect = arguments[0].getBoundingClientRect();
                return {
                    x: Math.round(rect.left),
                    y: Math.round(rect.top),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height)
                };
            """, element)
            return rect
        except Exception as e:
            logger.error(f"Failed to get element info: {e}")
            return {}
    
    def _convert_to_rgb(
        self,
        img: Image.Image,
        add_background: bool,
        bg_color: Tuple[int, int, int]
    ) -> Image.Image:
        """Convert image to RGB format with optional background.
        
        Args:
            img: PIL Image to convert.
            add_background: Whether to add background for transparency.
            bg_color: Background color as (R, G, B) tuple.
        
        Returns:
            Converted RGB image.
        """
        if img.mode == 'RGB':
            return img
        
        if img.mode in ('RGBA', 'LA', 'P'):
            if add_background:
                # Create background and composite image
                background = Image.new('RGB', img.size, bg_color)
                
                if img.mode == 'P':
                    img = img.convert('RGBA')
                
                if img.mode in ('RGBA', 'LA'):
                    # Use alpha channel as mask if available
                    if len(img.split()) > 1:
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img)
                    img = background
                else:
                    img = img.convert('RGB')
            else:
                img = img.convert('RGB')
        else:
            img = img.convert('RGB')
        
        return img
