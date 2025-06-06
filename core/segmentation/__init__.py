"""
Text Segmentation Module
========================
"""

# Segmentation module exports
try:
    from .enhanced_segmentation import EnhancedSegmentationEngine
    from .segment_and_prepare_training_data import prepare_data_for_training
    from .semantic_segmentation import enhanced_segment_text
except ImportError as e:
    print(f"Warning: Could not import segmentation modules: {e}")
    EnhancedSegmentationEngine = None
    prepare_data_for_training = None
    enhanced_segment_text = None

__all__ = ['EnhancedSegmentationEngine', 'prepare_data_for_training', 'enhanced_segment_text']