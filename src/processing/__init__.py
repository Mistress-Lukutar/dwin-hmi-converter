"""
Image processing module.

This module provides functionality for processing captured images,
including duplicate removal, size-based organization, and format verification.
"""

from .dedup import DuplicateRemover
from .organize import ElementOrganizer
from .verify import BmpVerifier

__all__ = ["DuplicateRemover", "ElementOrganizer", "BmpVerifier"]
