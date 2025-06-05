"""
LegalTech NLP Pipeline - Core Module
==================================

This module contains the core functionality for the LegalTech NLP Pipeline,
organized into specialized sub-modules for better maintainability and modularity.

Sub-modules:
- conversion: Data format conversion utilities
- segmentation: Text segmentation and preparation
- rag: RAG (Retrieval-Augmented Generation) functionality
- orchestration: Pipeline orchestration and integration
- validation: Quality validation and testing
"""

__version__ = "2.0.0"
__author__ = "LegalTech NLP Pipeline Team"

# Import main functionality from sub-modules for easy access
from .conversion import *
from .segmentation import *
from .rag import *
from .orchestration import *
from .validation import *
