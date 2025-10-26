# CRUD for label groups
# services/classification_service.py
from typing import List
from models.classification_models import ClassificationGroup
from repositories.classification_repository import ClassificationRepository


##################################################################
class ClassificationService:
    """Handles business logic for classification management."""

    # ----------------------------------------------------------------
    def __init__(self):
        self.repository = ClassificationRepository()

    # ----------------------------------------------------------------
    def load_all_groups(self) -> List[ClassificationGroup]:
        """Load all classification groups from the repository."""
        return self.repository.load_all_classification_groups()

    # ----------------------------------------------------------------
    def save_group(self, group: ClassificationGroup) -> None:
        """Save a classification group."""
        self.repository.save_classification_group(group)

    # ----------------------------------------------------------------
    def delete_group(self, group_name: str) -> None:
        """Delete a classification group."""
        self.repository.delete_classification_group(group_name)

    # ----------------------------------------------------------------

##################################################################
