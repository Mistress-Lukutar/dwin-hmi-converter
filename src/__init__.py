"""
DWIN HMI Converter - A tool for converting HTML-based HMI designs 
into 24-bit BMP images compatible with DWIN DGUS industrial displays.

This package provides tools for:
- Capturing screenshots of HTML interfaces using Selenium
- Processing and optimizing images for DWIN displays
- Organizing UI elements for Variable Icon implementation
- Preparing DGUS project files

Example:
    >>> from src.config_loader import ProjectConfig
    >>> from src.capture.page import PageCapture
    >>> config = ProjectConfig.from_file("input/config.json")
    >>> # Use with DriverManager and PageCapture
"""

__version__ = "2.0.0"
__author__ = "ServoHMI Team"
