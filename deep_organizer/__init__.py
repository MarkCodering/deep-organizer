"""
Deep Organizer - AI-powered file organization tool.

An intelligent AI agent that automatically organizes files in your directories
using advanced language models and content analysis.
"""

__version__ = "1.0.0"
__author__ = "Deep Organizer"
__license__ = "MIT"

from .core import FileOrganizer
from .cli import main

__all__ = ["FileOrganizer", "main"]