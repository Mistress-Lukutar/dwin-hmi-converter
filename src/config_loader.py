"""Configuration loader module.

This module provides functionality for loading project configurations
from JSON files stored alongside HTML files in the input/ directory.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)


class ProjectConfig:
    """Project configuration loaded from JSON file.
    
    This class replaces the hardcoded Config class with a flexible
    configuration loaded from external JSON files.
    
    Attributes:
        name: Project name for display purposes.
        html_file: Path to the source HTML file.
        resolution: Target display resolution (width, height).
        bmp_depth: Color depth for BMP output.
        container_selector: CSS selector for the main container.
        pages: Dictionary mapping page numbers to page info.
        elements: Dictionary mapping element names to CSS selectors.
        element_states: Configuration for multi-state element capture.
        touch_areas: Touch area coordinates for DGUS configuration.
        page_mapping: Mapping of output filenames to DGUS filenames.
        config_path: Path to the configuration file.
    
    Example:
        >>> config = ProjectConfig.from_file("input/config.json")
        >>> print(config.resolution)
        (1024, 768)
    """
    
    def __init__(self, config_path: Path):
        """Initialize from a JSON configuration file.
        
        Args:
            config_path: Path to the JSON configuration file.
        """
        self.config_path = Path(config_path)
        self._data = self._load_json()
        self._validate()
        
        # Basic settings
        self.name: str = self._data.get("name", "Unnamed Project")
        self.html_file: str = self._data.get("html_file", "index.html")
        self.resolution: Tuple[int, int] = tuple(self._data.get("resolution", [1024, 768]))
        self.bmp_depth: int = self._data.get("bmp_depth", 24)
        self.container_selector: str = self._data.get("container_selector", ".hmi-container")
        
        # Page configuration
        self.pages: Dict[str, dict] = self._data.get("pages", {})
        
        # Element selectors
        self.elements: Dict[str, str] = self._data.get("elements", {})
        
        # Element states for multi-state capture
        self.element_states: Dict[str, dict] = self._data.get("element_states", {})
        
        # Touch areas configuration
        self.touch_areas: Dict[str, dict] = self._data.get("touch_areas", {})
        
        # Page mapping for DGUS
        self.page_mapping: Dict[str, str] = self._data.get("page_mapping", {})
        
        # Output directories (relative to project root)
        self.output_dir: str = "output"
        self.dgus_dir: str = "output/dgus"  # DGUS project files go here
        self.OUTPUT_DIR: str = self.output_dir  # Backwards compatibility
        
        # Timing settings (with defaults)
        self.PAGE_TRANSITION_DELAY: float = self._data.get("page_transition_delay", 0.3)
        self.ANIMATION_DISABLE_DELAY: float = self._data.get("animation_disable_delay", 0.05)
        self.ELEMENT_CAPTURE_DELAY: float = self._data.get("element_capture_delay", 0.15)
        self.SELFWAIT_TIMEOUT: int = self._data.get("selfwait_timeout", 10)
        
        # Visual settings (with defaults)
        self.BG_COLOR: Tuple[int, int, int] = tuple(self._data.get("bg_color", [26, 26, 26]))
        
        # Backwards compatibility aliases
        self.PAGE_NAMES = {int(k): v for k, v in self.pages.items()}
        self.RESOLUTION = self.resolution
        
        # Timing settings (with defaults)
        self.PAGE_TRANSITION_DELAY: float = self._data.get("page_transition_delay", 0.3)
        self.ANIMATION_DISABLE_DELAY: float = self._data.get("animation_disable_delay", 0.05)
        self.ELEMENT_CAPTURE_DELAY: float = self._data.get("element_capture_delay", 0.15)
        self.SELFWAIT_TIMEOUT: int = self._data.get("selfwait_timeout", 10)
        
        # Visual settings (with defaults)
        self.BG_COLOR: Tuple[int, int, int] = tuple(self._data.get("bg_color", [26, 26, 26]))
        
        # Backwards compatibility aliases
        self.PAGE_NAMES = {int(k): v for k, v in self.pages.items()}
        self.RESOLUTION = self.resolution
    
    @classmethod
    def from_file(cls, config_path: Path) -> "ProjectConfig":
        """Create a ProjectConfig instance from a JSON file.
        
        Args:
            config_path: Path to the JSON configuration file.
        
        Returns:
            ProjectConfig instance.
        
        Raises:
            FileNotFoundError: If the configuration file doesn't exist.
            ValueError: If the configuration is invalid.
        """
        return cls(config_path)
    
    def _load_json(self) -> dict:
        """Load and parse the JSON configuration file.
        
        Returns:
            Dictionary with configuration data.
        
        Raises:
            FileNotFoundError: If the file doesn't exist.
            json.JSONDecodeError: If the file contains invalid JSON.
        """
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}\n"
                f"Absolute path: {self.config_path.absolute()}"
            )
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Loaded configuration from: {self.config_path}")
            return data
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
    
    def _validate(self) -> None:
        """Validate the configuration data.
        
        Raises:
            ValueError: If required fields are missing or invalid.
        """
        required_fields = ["html_file", "pages"]
        missing = [f for f in required_fields if f not in self._data]
        
        if missing:
            raise ValueError(f"Missing required fields in config: {missing}")
        
        # Validate resolution format
        resolution = self._data.get("resolution", [1024, 768])
        if not isinstance(resolution, (list, tuple)) or len(resolution) != 2:
            raise ValueError("Resolution must be a list/tuple of two integers [width, height]")
        
        # Validate pages
        pages = self._data.get("pages", {})
        if not pages:
            logger.warning("No pages defined in configuration")
        
        # Log configuration summary
        logger.info(f"Project: {self._data.get('name', 'Unnamed')}")
        logger.info(f"HTML file: {self._data.get('html_file')}")
        logger.info(f"Resolution: {resolution[0]}x{resolution[1]}")
        logger.info(f"Pages: {len(pages)}")
        logger.info(f"Elements: {len(self._data.get('elements', {}))}")
        logger.info(f"Element states: {len(self._data.get('element_states', {}))}")
    
    def get_html_path(self) -> Path:
        """Get the absolute path to the HTML file.
        
        Returns:
            Path object pointing to the HTML file.
        """
        # If html_file is relative, resolve relative to config file directory
        html_path = Path(self.html_file)
        if not html_path.is_absolute():
            html_path = self.config_path.parent / html_path
        return html_path.resolve()
    
    def get_output_path(self) -> Path:
        """Get the output directory path.
        
        Returns:
            Path object pointing to the output directory.
        """
        return Path(self.output_dir)
    
    def get_pages_output_path(self) -> Path:
        """Get the pages output subdirectory path.
        
        Returns:
            Path object pointing to the pages output directory.
        """
        return self.get_output_path() / "pages"
    
    def get_elements_output_path(self) -> Path:
        """Get the elements output subdirectory path.
        
        Returns:
            Path object pointing to the elements output directory.
        """
        return self.get_output_path() / "elements"
    
    def get_dgus_path(self) -> Path:
        """Get the DGUS project directory path.
        
        Returns:
            Path object pointing to the DGUS directory.
        """
        return Path(self.dgus_dir)
    
    def get_dwin_set_path(self) -> Path:
        """Get the DWIN_SET directory path for DGUS project.
        
        Returns:
            Path object pointing to the DWIN_SET directory.
        """
        return self.get_dgus_path() / "DWIN_SET"
    
    def get_icon_path(self) -> Path:
        """Get the ICON directory path for DGUS project.
        
        Returns:
            Path object pointing to the ICON directory.
        """
        return self.get_dgus_path() / "ICON"
    
    def get_page_name(self, page_num: int) -> str:
        """Get the name for a page number.
        
        Args:
            page_num: Page number.
        
        Returns:
            Page name string or "page{N}" if not found.
        """
        page_str = str(page_num)
        if page_str in self.pages:
            return self.pages[page_str].get("name", f"page{page_num}")
        return f"page{page_num}"
    
    def get_page_title(self, page_num: int) -> str:
        """Get the title for a page number.
        
        Args:
            page_num: Page number.
        
        Returns:
            Page title string or empty string if not found.
        """
        page_str = str(page_num)
        if page_str in self.pages:
            return self.pages[page_str].get("title", "")
        return ""
    
    def get_page_numbers(self) -> List[int]:
        """Get a sorted list of page numbers.
        
        Returns:
            List of integer page numbers.
        """
        return sorted([int(k) for k in self.pages.keys() if k.isdigit()])
    
    def get_element_states_for_page(self, page_num: int) -> Dict[str, dict]:
        """Get element states configuration for a specific page.
        
        Args:
            page_num: Page number to filter by.
        
        Returns:
            Dictionary of element states for the specified page.
        """
        result = {}
        for name, config in self.element_states.items():
            if config.get("page") == page_num:
                result[name] = config
        return result
    
    def get_touch_areas_for_page(self, page_name: str) -> Dict[str, dict]:
        """Get touch areas for a page by name.
        
        Args:
            page_name: Page name (e.g., "main", "settings").
        
        Returns:
            Dictionary of touch area configurations.
        """
        return self.touch_areas.get(page_name, {})


def load_config(config_path: Optional[Path] = None) -> ProjectConfig:
    """Load a project configuration.
    
    If no path is provided, looks for default config files in order:
    1. input/config.json
    2. config.json (in project root)
    
    Args:
        config_path: Optional explicit path to configuration file.
    
    Returns:
        ProjectConfig instance.
    
    Raises:
            FileNotFoundError: If no configuration file is found.
    """
    if config_path:
        return ProjectConfig.from_file(config_path)
    
    # Try default locations
    default_paths = [
        Path("input/config.json"),
        Path("config.json"),
    ]
    
    for path in default_paths:
        if path.exists():
            logger.info(f"Using default configuration: {path}")
            return ProjectConfig.from_file(path)
    
    raise FileNotFoundError(
        "No configuration file found. Expected one of:\n" +
        "\n".join([f"  - {p}" for p in default_paths]) +
        "\nOr provide explicit path with --config"
    )
