"""
models package
-------------------
Holds all model classes used throughout the application.
"""

from .classification_models import Classification, ClassificationGroup

# Define what’s publicly importable from this package
__all__ = ["Classification", "ClassificationGroup"]
