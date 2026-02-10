"""Simplified state capture module.

This module provides a lightweight way to capture UI elements in different
states by manipulating CSS classes directly, without complex state simulation.

Example:
    Instead of simulating button clicks and tracking application state,
    simply toggle CSS classes:
    
    # LED off -> LED green
    element.classList.remove('red', 'gray')
    element.classList.add('green')
"""

import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from src.config_loader import ProjectConfig
from src.capture.element import ElementCapture

logger = logging.getLogger(__name__)


class StateCapture:
    """Captures elements in different states via CSS manipulation.
    
    This is a simplified alternative to StateSimulator that doesn't simulate
    button clicks or track application logic. Instead, it directly manipulates
    CSS classes to show elements in different visual states.
    
    For example, to capture a LED in different colors:
    1. Navigate to the element's page
    2. Apply CSS classes for state 1 (e.g., gray/off)
    3. Capture the element
    4. Apply CSS classes for state 2 (e.g., green/on)
    5. Capture the element
    
    Attributes:
        driver: Selenium WebDriver instance.
        config: Project configuration.
        element_capture: ElementCapture instance.
    
    Example:
        >>> capture = StateCapture(driver, config)
        >>> capture.capture_element_states(output_dir)
    """
    
    def __init__(self, driver: WebDriver, config: ProjectConfig):
        """Initialize the StateCapture.
        
        Args:
            driver: Selenium WebDriver instance.
            config: Project configuration object.
        """
        self.driver = driver
        self.config = config
        self.element_capture = ElementCapture(driver, config)
    
    def capture_element_states(
        self,
        output_dir: Path,
        specific_elements: Optional[List[str]] = None
    ) -> Dict[str, List[str]]:
        """Capture all configured elements in their different states.
        
        Iterates through element_states configuration, switches to the
        appropriate page, applies each state via CSS manipulation, and
        captures the element.
        
        Args:
            output_dir: Directory to save captured element images.
            specific_elements: Optional list of element names to capture.
                              If None, captures all configured elements.
        
        Returns:
            Dictionary mapping element names to lists of captured state names.
        """
        logger.info("Capturing element states via CSS manipulation...")
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        captured = {}
        
        for element_name, element_config in self.config.element_states.items():
            # Skip if not in specific list
            if specific_elements and element_name not in specific_elements:
                continue
            
            try:
                states = self._capture_element_in_states(
                    element_name,
                    element_config,
                    output_dir
                )
                captured[element_name] = states
                
            except Exception as e:
                logger.error(f"Failed to capture states for {element_name}: {e}")
                continue
        
        total_states = sum(len(states) for states in captured.values())
        logger.info(f"Captured {total_states} states for {len(captured)} elements")
        
        return captured
    
    def _capture_element_in_states(
        self,
        element_name: str,
        element_config: dict,
        output_dir: Path
    ) -> List[str]:
        """Capture a single element in all its configured states.
        
        Args:
            element_name: Name of the element.
            element_config: Configuration dict with selector and states.
            output_dir: Output directory for images.
        
        Returns:
            List of successfully captured state names.
        """
        selector = element_config.get("selector")
        page_num = element_config.get("page", 0)
        states = element_config.get("states", [])
        
        if not selector or not states:
            logger.warning(f"Invalid configuration for {element_name}: missing selector or states")
            return []
        
        # Navigate to the element's page
        self._switch_to_page(page_num)
        
        # Find the element
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
        except Exception as e:
            logger.error(f"Element not found: {selector} ({element_name})")
            return []
        
        captured_states = []
        
        for state in states:
            state_name = state.get("name", "unknown")
            js_code = state.get("js", "")
            
            try:
                # Apply the state via JavaScript
                if js_code:
                    self._apply_state(selector, js_code)
                    time.sleep(0.1)  # Brief pause for render
                
                # Capture the element
                filename = output_dir / f"{element_name}_{state_name}.bmp"
                if self.element_capture.capture(element, filename):
                    captured_states.append(state_name)
                    logger.info(f"  Captured: {element_name} [{state_name}]")
                else:
                    logger.warning(f"  Failed to capture: {element_name} [{state_name}]")
                
            except Exception as e:
                logger.error(f"  Error capturing {element_name} [{state_name}]: {e}")
                continue
        
        return captured_states
    
    def _apply_state(self, selector: str, js_code: str) -> None:
        """Apply a state to an element via JavaScript.
        
        Wraps the user's JavaScript with element lookup.
        
        Args:
            selector: CSS selector for the element.
            js_code: JavaScript code to execute. 'el' variable refers to the element.
        """
        full_js = f"""
            var el = document.querySelector('{selector}');
            if (!el) {{
                throw new Error('Element not found: {selector}');
            }}
            {js_code}
            // Force reflow to ensure styles are applied
            el.offsetHeight;
        """
        self.driver.execute_script(full_js)
    
    def _switch_to_page(self, page_num: int) -> None:
        """Switch to a specific page.
        
        Args:
            page_num: Page number to switch to.
        """
        try:
            self.driver.execute_script(f"changePage({page_num})")
            time.sleep(0.3)  # Wait for page transition
        except Exception as e:
            logger.debug(f"Could not switch to page {page_num}: {e}")
    
    def capture_static_elements(
        self,
        output_dir: Path,
        specific_page: Optional[int] = None
    ) -> int:
        """Capture static elements (single state).
        
        Captures all elements defined in config.elements that don't
        have state definitions (or captures them once if they do).
        
        Args:
            output_dir: Directory to save captured element images.
            specific_page: If specified, only capture elements for this page.
        
        Returns:
            Number of successfully captured elements.
        """
        logger.info("Capturing static elements...")
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        success_count = 0
        
        # Group elements by page for efficiency
        elements_by_page: Dict[int, List[Tuple[str, str]]] = {}
        
        for name, selector in self.config.elements.items():
            # Skip elements that have state definitions (captured separately)
            if name in self.config.element_states:
                continue
            
            # Determine page from element_states or default to 0
            page_num = 0
            if name in self.config.element_states:
                page_num = self.config.element_states[name].get("page", 0)
            
            if specific_page is not None and page_num != specific_page:
                continue
            
            if page_num not in elements_by_page:
                elements_by_page[page_num] = []
            elements_by_page[page_num].append((name, selector))
        
        # Capture elements page by page
        for page_num, elements in sorted(elements_by_page.items()):
            self._switch_to_page(page_num)
            
            logger.info(f"  Page {page_num}: {len(elements)} elements")
            
            for name, selector in elements:
                try:
                    elements_found = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if not elements_found:
                        logger.warning(f"    Element not found: {name} ({selector})")
                        continue
                    
                    # Capture first matching element
                    filename = output_dir / f"{name}.bmp"
                    if self.element_capture.capture(elements_found[0], filename):
                        success_count += 1
                        logger.info(f"    Captured: {name}")
                    else:
                        logger.warning(f"    Failed: {name}")
                        
                except Exception as e:
                    logger.error(f"    Error capturing {name}: {e}")
        
        logger.info(f"Captured {success_count} static elements")
        return success_count
    
    def dismiss_selftest(self) -> None:
        """Dismiss the self-test dialog if present.
        
        Some HMI designs have a startup self-test page that blocks
        interaction. This method attempts to dismiss it.
        """
        try:
            # Try to find and click the continue button
            button = self.driver.find_element(By.CSS_SELECTOR, "#continueButton")
            if button.is_displayed():
                logger.debug("Dismissing self-test dialog...")
                # Try to trigger continue via JavaScript first
                self.driver.execute_script("if (typeof continueToMain === 'function') continueToMain();")
                time.sleep(0.3)
        except Exception:
            # Dialog not present or already dismissed
            pass
