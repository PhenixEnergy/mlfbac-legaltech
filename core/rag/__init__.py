"""
RAG (Retrieval-Augmented Generation) Module
==========================================
"""

# RAG module exports
try:
    from .optimized_prompt_generation import OptimizedPromptGenerator
    from .prepare_rag_training_data_fixed import prepare_rag_training_data
except ImportError as e:
    print(f"Warning: Could not import RAG modules: {e}")
    OptimizedPromptGenerator = None
    prepare_rag_training_data = None

__all__ = ['OptimizedPromptGenerator', 'prepare_rag_training_data']