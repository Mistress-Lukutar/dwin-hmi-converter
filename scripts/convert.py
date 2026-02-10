#!/usr/bin/env python3
"""
DWIN HMI Converter - Main Entry Point

This script converts HTML-based HMI designs into 24-bit BMP images
compatible with DWIN DGUS industrial displays.

Usage:
    python scripts/convert.py [options]

Options:
    --config PATH  Path to project configuration JSON file
    --skip-dgus    Skip DGUS project preparation
    --verbose, -v  Enable verbose logging
    --help, -h     Show this help message

Examples:
    # Run with default configuration (input/config.json)
    python scripts/convert.py

    # Run with specific configuration
    python scripts/convert.py --config input/my_project.json

    # Run only HTML to BMP conversion (skip DGUS prep)
    python scripts/convert.py --skip-dgus

    # Enable verbose output
    python scripts/convert.py -v

Requirements:
    - Python 3.10+
    - Google Chrome
    - selenium, Pillow packages
"""

import argparse
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.config_loader import ProjectConfig, load_config
from src.driver import DriverManager
from src.capture.page import PageCapture
from src.capture.element import ElementCapture
from src.capture.state_capture import StateCapture
from src.processing.dedup import DuplicateRemover
from src.processing.organize import ElementOrganizer
from src.processing.verify import BmpVerifier
from src.dgus.prepare import DgusPreparer
from src.utils.filesystem import get_absolute_path, ensure_directory


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the application.
    
    Args:
        verbose: If True, set log level to DEBUG; otherwise INFO.
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    log_format = "%(levelname)s: %(message)s"
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[logging.StreamHandler()]
    )


def check_prerequisites(config: ProjectConfig) -> bool:
    """Check that required files and dependencies exist.
    
    Args:
        config: Project configuration.
    
    Returns:
        True if all prerequisites are met, False otherwise.
    """
    logger = logging.getLogger(__name__)
    
    # Check HTML file exists
    html_path = config.get_html_path()
    if not html_path.exists():
        logger.error(f"HTML file not found: {html_path}")
        logger.error(f"Expected at: {html_path.absolute()}")
        return False
    
    logger.debug(f"Found HTML file: {html_path}")
    return True


def run_conversion_pipeline(
    config: ProjectConfig,
    skip_dgus: bool = False
) -> bool:
    """Run the simplified conversion pipeline.
    
    This function orchestrates the conversion process:
    1. Setup WebDriver and load HTML
    2. Capture full page screenshots
    3. Capture static elements (single state)
    4. Capture elements in multiple states (CSS manipulation)
    5. Verify output files
    6. Remove duplicates and organize elements
    7. Prepare DGUS project files (optional)
    
    Args:
        config: Project configuration.
        skip_dgus: If True, skip DGUS project preparation.
    
    Returns:
        True if conversion was successful, False otherwise.
    """
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("DWIN HMI Converter")
    logger.info(f"Project: {config.name}")
    logger.info("=" * 60)
    
    # Ensure output directories exist
    output_dir = ensure_directory(config.get_output_path())
    ensure_directory(config.get_pages_output_path())
    ensure_directory(config.get_elements_output_path())
    
    logger.info(f"Output directory: {output_dir.absolute()}")
    
    # Initialize WebDriver
    with DriverManager(config) as driver:
        # Load HTML file
        html_path = config.get_html_path()
        file_url = html_path.as_uri()
        logger.info(f"Loading {config.html_file}...")
        driver.get(file_url)
        
        # Wait for page load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, config.container_selector))
        )
        logger.debug("Page loaded successfully")
        
        # Initialize capture classes
        page_capture = PageCapture(driver, config)
        state_capture = StateCapture(driver, config)
        
        # Dismiss self-test if present
        state_capture.dismiss_selftest()
        
        # Capture all pages
        logger.info("\n[1/4] Capturing pages...")
        captured_pages = page_capture.capture_all_pages(
            config.get_pages_output_path()
        )
        logger.info(f"Captured {len(captured_pages)} pages")
        
        # Capture static elements
        logger.info("\n[2/4] Capturing static elements...")
        static_count = state_capture.capture_static_elements(
            config.get_elements_output_path()
        )
        logger.info(f"Captured {static_count} static elements")
        
        # Capture elements in different states
        if config.element_states:
            logger.info("\n[3/4] Capturing element states...")
            state_results = state_capture.capture_element_states(
                config.get_elements_output_path()
            )
            total_states = sum(len(states) for states in state_results.values())
            logger.info(f"Captured {total_states} element states")
        else:
            logger.info("\n[3/4] No element states configured, skipping")
    
    # Post-processing (WebDriver closed)
    logger.info("\n[4/4] Post-processing...")
    
    # Verify BMP files
    verifier = BmpVerifier(config)
    verifier.verify_all(output_dir)
    
    # Remove duplicate elements
    remover = DuplicateRemover(config.get_elements_output_path())
    removed, kept, unique_files = remover.remove_duplicates()
    
    # Organize unique elements by size
    if unique_files:
        organizer = ElementOrganizer(
            config.get_icon_path(),
            config
        )
        organizer.organize_by_size(unique_files, start_folder_num=32)
    
    # Prepare DGUS project files
    if not skip_dgus:
        logger.info("\nPreparing DGUS project...")
        preparer = DgusPreparer(config)
        preparer.prepare_project()
    else:
        logger.info("\nSkipped DGUS project preparation (--skip-dgus)")
    
    # Print summary
    _print_summary(config, skip_dgus)
    
    return True


def _print_summary(config: ProjectConfig, skip_dgus: bool) -> None:
    """Print conversion summary.
    
    Args:
        config: Project configuration.
        skip_dgus: Whether DGUS preparation was skipped.
    """
    logger = logging.getLogger(__name__)
    
    logger.info("\n" + "=" * 60)
    logger.info("Conversion Complete!")
    logger.info("=" * 60)
    
    logger.info("\nOutput locations:")
    logger.info(f"  - {config.output_dir}/pages/    : Page screenshots")
    logger.info(f"  - {config.output_dir}/elements/ : UI elements")
    
    if not skip_dgus:
        logger.info(f"  - {config.dgus_dir}/DWIN_SET/    : DGUS project files")
        logger.info(f"  - {config.dgus_dir}/ICON/        : Organized icon groups")
    
    logger.info("\nCaptured pages:")
    for page_num in config.get_page_numbers():
        page_name = config.get_page_name(page_num)
        page_title = config.get_page_title(page_num)
        display = f"{page_title}" if page_title else page_name
        logger.info(f"  - Page {page_num}: {display}")
    
    if config.element_states:
        logger.info("\nElement states captured:")
        for element_name, element_config in config.element_states.items():
            states = [s.get("name") for s in element_config.get("states", [])]
            logger.info(f"  - {element_name}: {', '.join(states)}")
    
    logger.info("\nNext steps:")
    if not skip_dgus:
        logger.info("  1. Open DGUS Tool")
        logger.info(f"  2. Load project from {config.dgus_dir}/ folder")
        logger.info("  3. Configure touch areas (see touch_areas_guide.txt)")
        logger.info("  4. Upload to DWIN display")
    else:
        logger.info("  Run with DGUS preparation:")
        logger.info(f"    python scripts/convert.py --config {config.config_path}")
    
    logger.info("=" * 60)


def main() -> int:
    """Main entry point.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Convert HTML HMI to DWIN-compatible BMP images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default configuration (input/config.json)
  python scripts/convert.py
  
  # Run with specific configuration
  python scripts/convert.py --config input/project_a.json
  
  # Run without DGUS preparation (faster for development)
  python scripts/convert.py --skip-dgus
  
  # Enable verbose output
  python scripts/convert.py -v
  
  # Combined options
  python scripts/convert.py --config input/custom.json --skip-dgus -v
        """
    )
    parser.add_argument(
        "--config",
        type=Path,
        metavar="PATH",
        help="Path to project configuration JSON file (default: input/config.json)"
    )
    parser.add_argument(
        "--skip-dgus",
        action="store_true",
        help="Skip DGUS project preparation"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Load configuration
    try:
        config = load_config(args.config)
    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Invalid configuration: {e}")
        return 1
    
    # Check prerequisites
    if not check_prerequisites(config):
        return 1
    
    # Run conversion
    try:
        success = run_conversion_pipeline(
            config,
            skip_dgus=args.skip_dgus
        )
        return 0 if success else 1
    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user")
        return 130
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
