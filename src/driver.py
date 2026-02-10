"""WebDriver management module.

This module provides functionality for setting up and managing the Selenium
Chrome WebDriver used for capturing screenshots.
"""

import logging
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from src.config_loader import ProjectConfig

logger = logging.getLogger(__name__)


class DriverManager:
    """Manages the Chrome WebDriver instance for screenshot capture.
    
    This class handles the creation and configuration of a headless Chrome
    WebDriver with settings optimized for 1:1 pixel capture at the target
    resolution.
    
    Attributes:
        driver: The Selenium WebDriver instance.
        config: Application configuration instance.
    
    Example:
        >>> with DriverManager() as driver:
        ...     driver.get("file:///path/to/file.html")
        ...     # Perform operations with driver
    """
    
    def __init__(self, config: Optional[ProjectConfig] = None):
        """Initialize the DriverManager.
        
        Args:
            config: Configuration object. If None, uses default Config.
        """
        self.config = config
        self.driver: Optional[webdriver.Chrome] = None
    
    def __enter__(self) -> webdriver.Chrome:
        """Context manager entry - creates and returns the driver.
        
        Returns:
            Configured Chrome WebDriver instance.
        """
        self.driver = self.create_driver()
        return self.driver
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - quits the driver.
        
        Args:
            exc_type: Exception type if an exception occurred.
            exc_val: Exception value if an exception occurred.
            exc_tb: Exception traceback if an exception occurred.
        """
        self.quit()
    
    def create_driver(self) -> webdriver.Chrome:
        """Create and configure a headless Chrome WebDriver.
        
        Configures Chrome with settings for:
        - Headless mode (no GUI)
        - Exact pixel ratio (1:1)
        - Target window size
        - Disabled animations
        - Hidden scrollbars
        
        Returns:
            Configured Chrome WebDriver instance.
        """
        logger.info("Creating Chrome WebDriver...")
        
        chrome_options = Options()
        
        # Headless and sandbox settings
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Window size - add extra height for browser chrome/scrollbars
        window_height = self.config.resolution[1] + 100
        chrome_options.add_argument(
            f"--window-size={self.config.resolution[0]},{window_height}"
        )
        
        # Hide scrollbars for clean screenshots
        chrome_options.add_argument("--hide-scrollbars")
        
        # Force 1:1 pixel ratio for accurate capture
        chrome_options.add_argument(f"--force-device-scale-factor={1}")
        chrome_options.add_argument("--high-dpi-support=1")
        chrome_options.add_argument("--disable-gpu")
        
        # Disable automation detection
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Create driver
        driver = webdriver.Chrome(options=chrome_options)
        
        # Set device metrics for exact pixel ratio
        driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
            'width': self.config.resolution[0],
            'height': self.config.resolution[1],
            'deviceScaleFactor': 1,
            'mobile': False
        })
        
        logger.info("Chrome WebDriver created successfully")
        return driver
    
    def quit(self) -> None:
        """Quit the WebDriver and clean up resources."""
        if self.driver:
            logger.info("Quitting Chrome WebDriver...")
            self.driver.quit()
            self.driver = None
    
    def get_driver(self) -> Optional[webdriver.Chrome]:
        """Get the current WebDriver instance.
        
        Returns:
            The current WebDriver instance or None if not created.
        """
        return self.driver
    
    def disable_transitions(self) -> None:
        """Disable CSS transitions and animations on the current page.
        
        This should be called before taking screenshots to ensure
        consistent capture without animation artifacts.
        """
        if not self.driver:
            return
        
        self.driver.execute_script("""
            document.querySelectorAll('.btn, .indicator, .led').forEach(function(el) {
                el.style.transition = 'none';
                el.style.animation = 'none';
            });
            document.body.offsetHeight; // Force reflow
        """)
