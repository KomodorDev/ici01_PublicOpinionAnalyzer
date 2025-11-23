"""
classification_repository.py
============================

Low-level filesystem persistence for Classification Groups and Classifications.

This repository stores all label definitions in a simple folder-based
structure:

    Classifications/
        <group_name>/
            <classification_name>.json
            <classification_name>.json
            ...

Design Principles
-----------------
• The **folder name** is the classification group name.  
• The **filename stem** (without `.json`) is the authoritative
  classification *name*.  
  The JSON file does **not** contain a `name` field—names are derived
  exclusively from filenames.

• The repository is intentionally "dumb":
  It performs **no business validation**, **no collision logic**, and **no
  normalization rules**. These responsibilities belong to the
  `ClassificationService` layer.

• All JSON files contain only the editable fields of `Classification`
  (question, explanation, output_type, categories, etc).  
  The `Classification.name` attribute is injected by the repository when
  loading from disk.

Responsibilities
----------------
This module provides **pure CRUD access**:

    - list_classification_group_names()
    - load_all_classification_groups()
    - load_classification_group(group_name)
    - load_classification(group_name, classification_name)

    - create_classification_group(group_name)
    - rename_classification_group(old_name, new_name)
    - delete_classification_group(group_name)

    - save_classification_group(group)
    - save_classification(group_name, classification)
    - rename_classification(group_name, old_name, new_name)
    - delete_classification(group_name, classification_name)
    - list_classification_names(group_name)

Atomicity & Safety
------------------
• Group and classification rename operations delegate directly to the OS
  (`os.rename()`), which is atomic on POSIX systems.  
• All file I/O uses UTF-8.  
• Missing paths raise explicit filesystem errors.

What This Repository Does NOT Do
--------------------------------
• It does not enforce uniqueness of names.  
• It does not validate classification output types or structure.  
• It does not prevent illegal or reserved names.  
• It does not maintain IDs—file names are the identity.

These checks are intentionally left to the **service layer**, which is
responsible for enforcing business rules before calling repository
methods.
"""

import os
import json
import shutil
from dataclasses import asdict
from typing import List
from enums.classification_output_enum import ClassificationOutputEnum
from models.domain import Classification, ClassificationGroup

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
    def load_classification(
        self,
        group_name: str,
        classification_name: str,
    ) -> Classification:
        """
        Load a single Classification from disk using the logical
        classification name (filename WITHOUT .json).

        This ensures:
        - Service/controller only deal with logical names
        - Repo converts to actual filename internally
        - Classification.name is derived from classification_name

        Args:
            group_name (str):
                Name of the classification group (folder name)
            classification_name (str):
                Logical name of the classification (filename stem)

        Returns:
            Classification:
                Domain object with canonical name derived from filename-stem.

        Raises:
            FileNotFoundError:
                If the JSON file does not exist.
            json.JSONDecodeError:
                If the file content is malformed.
        """
        group_path = os.path.join(self.base_path, group_name)
        file_path = os.path.join(group_path, f"{classification_name}.json")

        if not os.path.exists(file_path):
            raise FileNotFoundError(
                f"Classification not found: {group_name}/{classification_name}.json"
            )

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Safeguard: JSON must not override the canonical name
        data.pop("name", None)

        # Convert output_type to enum
        if "output_type" in data and isinstance(data["output_type"], str):
            data["output_type"] = ClassificationOutputEnum(data["output_type"])

        return Classification(name=classification_name, **data)

    # ----------------------------------------------------------------
    def rename_classification(self, group_name: str, old_name: str, new_name: str) -> None:
        """
        Rename a classification file inside a group.

        This is a pure filesystem operation:
        - old_name / new_name are filename stems (without .json)
        - No JSON content is modified here
        - Service layer must validate uniqueness before calling this

        Raises:
            FileNotFoundError: old file does not exist
            FileExistsError: new file already exists
            OSError: filesystem rename failure
        """
        group_path = os.path.join(self.base_path, group_name)
        old_path = os.path.join(group_path, f"{old_name}.json")
        new_path = os.path.join(group_path, f"{new_name}.json")

        if not os.path.exists(old_path):
            raise FileNotFoundError(f"Cannot rename: '{old_name}.json' does not exist in '{group_name}'.")

        if os.path.exists(new_path):
            raise FileExistsError(f"Cannot rename to '{new_name}.json': file already exists.")

        os.rename(old_path, new_path)

    # ----------------------------------------------------------------
    def load_classification_group(self, group_name: str) -> ClassificationGroup:
        """
        Load a classification group and all classifications inside it, deriving each name from its filename.
        """
        group_path = os.path.join(self.base_path, group_name)

        if not os.path.exists(group_path):
            raise FileNotFoundError(f"Classification group not found: {group_name}")
        if not os.path.isdir(group_path):
            raise ValueError(f"Path is not a directory: {group_path}")

        group = ClassificationGroup(name=group_name)

        for file_name in os.listdir(group_path):
            if not file_name.endswith(".json"):
                continue

            # derive classification name from filename
            classification_name = os.path.splitext(file_name)[0]

            classification = self.load_classification(group_name, classification_name)
            group.classifications.append(classification)

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
    def rename_classification_group(self, old_name: str, new_name: str) -> None:
        """
        Rename a classification group folder on disk.

        This operation is **purely filesystem-level** and intentionally does
        NOT perform any business-rule validation such as:
        - "name must not be empty"
        - "name must follow certain formatting"
        - "name must be unique in the domain sense"

        Those checks belong in the controller or service layer.

        What this method DOES guarantee:
        - The source directory must exist.
        - The target directory must NOT already exist.
        - The rename operation is performed atomically by the OS.
            (On POSIX systems, `os.rename()` is atomic. On Windows, it is
            effectively atomic unless cross-volume.)

        Args:
            old_name (str):
                Current folder name under the repository base path.
            new_name (str):
                Requested new folder name.
                Must not already exist in the filesystem; otherwise an error is raised.

        Raises:
            FileNotFoundError:
                If the source folder does not exist.
            FileExistsError:
                If the target folder already exists.
            OSError:
                If the rename operation fails due to filesystem permissions or I/O errors.
        """

        old_path = os.path.join(self.base_path, old_name)
        new_path = os.path.join(self.base_path, new_name)

        # Ensure the source exists
        if not os.path.exists(old_path):
            raise FileNotFoundError(f"Classification group not found: '{old_name}'")

        # Prevent accidental overwrite of an existing folder
        if os.path.exists(new_path):
            raise FileExistsError(
                f"Cannot rename group to '{new_name}' because that folder already exists."
            )

        # Perform the atomic rename
        os.rename(old_path, new_path)

    # ----------------------------------------------------------------
    def create_classification_group(self, group_name: str) -> None:
        """
        Create a new classification group folder on disk.   
        """
        group_path = os.path.join(self.base_path, group_name)
        os.makedirs(group_path, exist_ok=False)  # raises if exists

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

        # Convert classification to dict, excluding 'name' since it's derived from filename
        data = {k: v for k, v in asdict(classification).items() if k != "name"}

        # Write classification data to JSON file and overwrite if it exists:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

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

    # ----------------------------------------------------------------
    def list_classification_names(self, group_name: str) -> List[str]:
        """List all classification filename stems in a group."""
        group_path = os.path.join(self.base_path, group_name)
        if not os.path.isdir(group_path):
            return []

        out: List[str] = []
        for fn in os.listdir(group_path):
            if fn.endswith(".json"):
                out.append(os.path.splitext(fn)[0])
        return out

##################################################################
