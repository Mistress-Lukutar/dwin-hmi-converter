"""BMP file verification module.

This module provides functionality for verifying BMP files against
DWIN DGUS requirements.
"""

import logging
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image

from src.config_loader import ProjectConfig

logger = logging.getLogger(__name__)


class BmpVerifier:
    """Verifies BMP files against DWIN DGUS requirements.
    
    Checks that generated BMP files meet the requirements:
    - Format: BMP
    - Color depth: 24-bit (RGB mode)
    - Resolution: matches target resolution (for page files)
    
    Attributes:
        config: Application configuration.
    
    Example:
        >>> verifier = BmpVerifier(config)
        >>> is_valid = verifier.verify_all("output")
        >>> if not is_valid:
        ...     print("Some files failed verification")
    """
    
    def __init__(self, config: Optional[ProjectConfig] = None):
        """Initialize the BmpVerifier.
        
        Args:
            config: Configuration object. If None, uses default Config.
        """
        self.config = config or Config()
    
    def verify_all(self, output_dir: Path) -> bool:
        """Verify all BMP files in the output directory.
        
        Args:
            output_dir: Root output directory to scan.
        
        Returns:
            True if all files pass verification, False otherwise.
        """
        logger.info("Verifying BMP files...")
        
        output_dir = Path(output_dir)
        bmp_files = list(output_dir.rglob("*.bmp"))
        
        logger.info(f"Found {len(bmp_files)} BMP files")
        
        if not bmp_files:
            logger.warning("No BMP files found to verify")
            return True
        
        issues = []
        page_files = []
        element_files = []
        
        for bmp_file in bmp_files:
            result = self.verify_file(bmp_file)
            
            if result['errors']:
                issues.extend([f"{bmp_file.name}: {e}" for e in result['errors']])
            
            # Categorize by location
            if "pages" in str(bmp_file):
                page_files.append((bmp_file.name, result['size'], result['mode']))
            else:
                element_files.append((bmp_file.name, result['size'], result['mode']))
        
        # Print summary
        self._print_summary(page_files, element_files, issues)
        
        return len(issues) == 0
    
    def verify_file(self, filepath: Path) -> dict:
        """Verify a single BMP file.
        
        Args:
            filepath: Path to the BMP file.
        
        Returns:
            Dictionary with verification results:
            - valid: Whether file passed all checks
            - format: Image format
            - mode: Color mode
            - size: Image dimensions
            - errors: List of error messages
        """
        result = {
            'valid': False,
            'format': None,
            'mode': None,
            'size': None,
            'errors': []
        }
        
        try:
            with Image.open(filepath) as img:
                result['format'] = img.format
                result['mode'] = img.mode
                result['size'] = img.size
                
                # Check format
                if img.format != 'BMP':
                    result['errors'].append(f"Not BMP format (found: {img.format})")
                
                # Check color mode (DWIN requires 24-bit RGB)
                if img.mode != 'RGB':
                    result['errors'].append(f"Wrong mode: {img.mode} (expected: RGB)")
                
                # Check resolution for page files
                is_page = "pages" in str(filepath)
                if is_page and img.size != self.config.RESOLUTION:
                    result['errors'].append(
                        f"Wrong size: {img.size} (expected: {self.config.RESOLUTION})"
                    )
                
                result['valid'] = len(result['errors']) == 0
                
        except Exception as e:
            result['errors'].append(f"Read error: {e}")
        
        return result
    
    def verify_pages(self, pages_dir: Path) -> Tuple[bool, List[str]]:
        """Verify only page BMP files.
        
        Args:
            pages_dir: Directory containing page BMP files.
        
        Returns:
            Tuple of (all_valid, list_of_errors).
        """
        pages_dir = Path(pages_dir)
        if not pages_dir.exists():
            return False, ["Pages directory not found"]
        
        errors = []
        page_files = list(pages_dir.glob("*.bmp"))
        
        for page_file in page_files:
            result = self.verify_file(page_file)
            if result['errors']:
                errors.extend([f"{page_file.name}: {e}" for e in result['errors']])
        
        return len(errors) == 0, errors
    
    def get_file_info(self, filepath: Path) -> dict:
        """Get detailed information about a BMP file.
        
        Args:
            filepath: Path to the BMP file.
        
        Returns:
            Dictionary with file information or error message.
        """
        try:
            with Image.open(filepath) as img:
                return {
                    'filename': filepath.name,
                    'format': img.format,
                    'mode': img.mode,
                    'size': img.size,
                    'width': img.size[0],
                    'height': img.size[1],
                    'valid_dwin': (
                        img.format == 'BMP' and 
                        img.mode == 'RGB'
                    )
                }
        except Exception as e:
            return {
                'filename': filepath.name,
                'error': str(e)
            }
    
    def _print_summary(
        self,
        page_files: List[Tuple[str, tuple, str]],
        element_files: List[Tuple[str, tuple, str]],
        issues: List[str]
    ) -> None:
        """Print verification summary.
        
        Args:
            page_files: List of (name, size, mode) tuples for pages.
            element_files: List of (name, size, mode) tuples for elements.
            issues: List of error messages.
        """
        logger.info(f"\nPages ({len(page_files)}):")
        for name, size, mode in page_files:
            logger.info(f"  ✓ {name}: {size}, {mode}")
        
        logger.info(f"\nElements ({len(element_files)}):")
        for name, size, mode in element_files:
            logger.info(f"  ✓ {name}: {size}, {mode}")
        
        if issues:
            logger.warning("\nIssues found:")
            for issue in issues:
                logger.warning(f"  - {issue}")
        else:
            logger.info("\n✓ All files meet DWIN requirements!")
