"""
Vocabulary re-export module.
Imports the full 8-category Urdu domain vocabulary from vocabulary_expanded.py
so that other modules can do: from vocabulary import VOCABULARY
"""
from vocabulary_expanded import VOCABULARY

__all__ = ["VOCABULARY"]
