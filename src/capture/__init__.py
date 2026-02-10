"""
Screenshot capture module.

This module provides functionality for capturing screenshots of HTML pages
and individual UI elements using Selenium WebDriver.
"""

from .page import PageCapture
from .element import ElementCapture
from .state_capture import StateCapture

__all__ = ["PageCapture", "ElementCapture", "StateCapture"]
