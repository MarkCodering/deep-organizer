"""Deep Organizer - AI-powered file organization tool."""

__version__ = "1.0.0"
__author__ = "Deep Organizer"
__license__ = "MIT"

from .core import FileOrganizer
from .gui import run_app

__all__ = ["FileOrganizer", "run_app"]
