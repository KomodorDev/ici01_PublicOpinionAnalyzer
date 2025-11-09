"""
classification_repository.py
============================

Provides persistent storage and retrieval of classification data using a
simple folder-based JSON repository structure.

This module defines the `ClassificationRepository` class responsible for
reading and writing `Classification` and `ClassificationGroup` objects
to and from the filesystem. Each classification group is represented
by a folder under the base directory (`Classifications/`), and each
classification within that group is serialized as a `.json` file.

The repository implements full CRUD operations:
- Load all existing classification groups and their member classifications.
- Load a single classification group by name
- List all available classification group names
- Save or update a single classification or entire group.
- Create the directory structure automatically if missing.
- Delete individual classifications or entire classification groups.

Directory Structure Example:
    Classifications/
        Political/
            pro_taiwan.json
            anti_china.json
        Tone/
            tone.json

Example:
    >>> repo = ClassificationRepository(base_path="Classifications")
    >>> groups = repo.load_all_classification_groups()
    >>> new_class = Classification(name="tone", question="What is the tone?")
    >>> repo.save_classification("Tone", new_class)
    >>> repo.delete_classification("Tone", "tone")

Attributes:
    ClassificationRepository:
        Main repository class providing high-level file-based persistence.

Raises:
    OSError:
        If directories cannot be created or files cannot be written.
    json.JSONDecodeError:
        If an existing classification file is malformed.
"""


import os
import json
import shutil
from dataclasses import asdict
from typing import List
from enums.classification_output_enum import ClassificationOutputEnum
from models.classification_models import Classification, ClassificationGroup

##################################################################
class ClassificationRepository:
    """
    Responsible for reading and writing Classification and ClassificationGroup
    objects to/from JSON files on disk.
    """

    # ----------------------------------------------------------------
    def __init__(self, base_path: str = "Classifications"):
        self.base_path = base_path

        # Create folder if it does not exist yet:
        os.makedirs(self.base_path, exist_ok=True)

    # ----------------------------------------------------------------
    def load_all_classification_groups(self) -> List[ClassificationGroup]:
        """
        Load all classification groups and their JSON‑defined classifications from disk.

        This method scans the base directory recursively:
        - Each subfolder under `Classifications/` is treated as a group.
        - Each `.json` file inside those subfolders is deserialized into a
        `Classification` object and assigned to its group.

        Returns:
            List[ClassificationGroup]:
                A list of all loaded groups with their classification objects.

        Raises:
            FileNotFoundError:
                If the base `Classifications/` folder does not exist.
            json.JSONDecodeError:
                If any classification JSON file is malformed.
        """
        if not os.path.exists(self.base_path):
            raise FileNotFoundError(f"Base classification directory not found: {self.base_path}")

        groups: List[ClassificationGroup] = []

        for group_name in os.listdir(self.base_path):
            group_path = os.path.join(self.base_path, group_name)
            if not os.path.isdir(group_path):
                continue
            group = self.load_classification_group(group_name)
            groups.append(group)
        return groups

    # ----------------------------------------------------------------
    def load_classification_group(self, group_name: str) -> ClassificationGroup:
        """
        Load a single classification group by name.
        
        Args:
            group_name: Name of the classification group (folder name)
            
        Returns:
            ClassificationGroup: The loaded group with all its classifications
            
        Raises:
            FileNotFoundError: If the group folder does not exist
            json.JSONDecodeError: If any classification JSON file is malformed
        """
        # Build path to the group folder
        group_path = os.path.join(self.base_path, group_name)

        # Check if group folder exists
        if not os.path.exists(group_path):
            raise FileNotFoundError(f"Classification group not found: {group_name}")

        if not os.path.isdir(group_path):
            raise ValueError(f"Path is not a directory: {group_path}")

        # Create ClassificationGroup object
        group = ClassificationGroup(name=group_name)

        # Load all classification JSON files in the group folder
        for file_name in os.listdir(group_path):

            # Skip non-JSON files
            if not file_name.endswith(".json"):
                continue

            # Load the classification from JSON
            file_path = os.path.join(group_path, file_name)
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Convert output_type to Enum if it's present and is a string
                if "output_type" in data and isinstance(data["output_type"], str):
                    data["output_type"] = ClassificationOutputEnum(data["output_type"])
                classification = Classification(**data)
                group.classifications.append(classification)

        # Check if group has any classifications
        # if not group.classifications:
        #    raise ValueError(f"No classifications found in group: {group_name}")

        return group

    # ----------------------------------------------------------------
    def list_classification_group_names(self) -> List[str]:
        """
        List all available classification group names.
        
        Returns:
            List[str]: List of group names (folder names)
        """
        groups = []

        for item in os.listdir(self.base_path):
            item_path = os.path.join(self.base_path, item)

            # Only include directories
            if os.path.isdir(item_path):
                groups.append(item)

        return groups

    # ----------------------------------------------------------------
    def save_classification_group(self, group: ClassificationGroup) -> None:
        """
        Save an entire classification group and all its classifications as JSON files.

        This method ensures that a directory exists for the given classification group,
        and then saves each contained classification by delegating to
        `save_classification()`.

        Args:
            group (ClassificationGroup):
                The classification group object containing multiple
                `Classification` instances to save.

        Raises:
            OSError:
                If the directory cannot be created or files cannot be written.
        """
        group_path = os.path.join(self.base_path, group.name)

        # Make directory if it doesn't exist:
        os.makedirs(group_path, exist_ok=True)

        # Iterate over all classifications in the group and save each one:
        for classification in group.classifications:
            self.save_classification(group.name, classification)

    # ----------------------------------------------------------------
    def save_classification(self, group_name: str, classification: Classification) -> None:
        """
        Save a single classification object to its corresponding group folder as a JSON file.

        If the target folder does not exist, it is automatically created.
        If a file with the same name already exists, it will be overwritten.

        Args:
            group_name (str):
                The name of the classification group (maps to a folder under the base path).
            classification (Classification):
                The classification object to serialize and save.

        Raises:
            OSError:
                If the directory cannot be created or the file cannot be written.
            TypeError:
                If the provided classification is not serializable to JSON.
        """
        group_path = os.path.join(self.base_path, group_name)
        file_path = os.path.join(group_path, f"{classification.name}.json")

        # Make directory if it doesn't exist:
        os.makedirs(group_path, exist_ok=True)

        # Write classification data to JSON file and overwrite if it exists:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(asdict(classification), f, indent=4, ensure_ascii=False)

    # ----------------------------------------------------------------
    def delete_classification_group(self, group_name: str) -> None:
        """
        Deletes an entire classification group folder and all its contents.

        Args:
            group_name: The folder name under 'Classifications/' to remove.
        """
        group_path = os.path.join(self.base_path, group_name)

        if os.path.exists(group_path):
            shutil.rmtree(group_path)  # deletes entire folder recursively
            print(f"Deleted classification group: {group_path}")
        else:
            print(f"Group '{group_name}' does not exist.")

    # ----------------------------------------------------------------
    def delete_classification(self, group_name: str, classification_name: str) -> None:
        """
        Deletes a single classification JSON file from its group folder.

        Args:
            group_name: The name of the group (folder) under 'Classifications/'.
            classification_name: The file name prefix (without .json).
        """
        group_path = os.path.join(self.base_path, group_name)
        file_path = os.path.join(group_path, f"{classification_name}.json")

        if os.path.exists(file_path):
            os.remove(file_path)  # safely deletes the file
            print(f"Deleted classification file: {file_path}")
        else:
            print(f"Classification {classification_name}.json not found in {group_name}")

##################################################################
