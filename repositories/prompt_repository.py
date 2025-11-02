"""
prompt_repository.py
============================

Provides persistent storage and retrieval of prompt data using a
simple folder-based JSON repository structure.

This module defines the `PromptRepository` class responsible for
reading and writing `Prompt` and `PromptGroup` objects
to and from the filesystem. Each prompt group is represented
by a folder under the base directory (`Prompts/`), and each
prompt within that group is serialized as a `.json` file.

The repository implements full CRUD operations:
- Load all existing prompt groups and their member prompts.
- Save or update a single prompt or entire group.
- Create the directory structure automatically if missing.
- Delete individual prompts or entire prompt groups.

Directory Structure Example:
    Prompts/
        SystemPrompts/
            analysis.json
            summary.json
        UserPrompts/
            tone.json

Example:
    >>> repo = PromptRepository(base_path="Prompts")
    >>> groups = repo.load_all_prompt_groups()
    >>> new_prompt = Prompt(name="tone", content="What is the tone?")
    >>> repo.save_prompt("UserPrompts", new_prompt)
    >>> repo.delete_prompt("UserPrompts", "tone")

Attributes:
    PromptRepository:
        Main repository class providing high-level file-based persistence.

Raises:
    OSError:
        If directories cannot be created or files cannot be written.
    json.JSONDecodeError:
        If an existing prompt file is malformed.
"""


import os
import json
import shutil
from dataclasses import asdict
from typing import List
from models.prompt_model import Prompt, PromptGroup

##################################################################
class PromptRepository:
    """
    Responsible for reading and writing Prompt and PromptGroup
    objects to/from JSON files on disk.
    """

    # ----------------------------------------------------------------
    def __init__(self, base_path: str = "Prompts"):
        self.base_path = base_path

        # Create folder if it does not exist yet:
        os.makedirs(self.base_path, exist_ok=True)

    # ----------------------------------------------------------------
    def load_all_prompt_groups(self) -> List[PromptGroup]:
        """
        Load all prompt groups and their JSON‑defined prompts from disk.

        This method scans the base directory recursively:
        - Each subfolder under `Prompts/` is treated as a group.
        - Each `.json` file inside those subfolders is deserialized into a
        `Prompt` object and assigned to its group.

        Returns:
            List[PromptGroup]:
                A list of all loaded groups with their prompt objects.

        Raises:
            FileNotFoundError:
                If the base `Prompts/` folder does not exist.
            json.JSONDecodeError:
                If any prompt JSON file is malformed.
        """

        # creates an empty list called groups. ": List ...." is a type hint
        groups: List[PromptGroup] = []

        # os.listdir() returns a list of all items inside our Prompts/ directory
        for group_name in os.listdir(self.base_path):

            # We create a full path to the group folder:
            group_path = os.path.join(self.base_path, group_name)

            # if one of the items is not a folder, we skip it
            if not os.path.isdir(group_path):
                continue

            # We create a new PromptGroup object with the folder name
            group = PromptGroup(name=group_name)

            # We iterate over all files in the group folder:
            for file_name in os.listdir(group_path):

                # If a iteam is not a .json file, we skip it:
                if not file_name.endswith(".json"):
                    continue

                # If the iteam is a .json file, we load it and create a Prompt object:
                file_path = os.path.join(group_path, file_name)
                with open(file_path, "r", encoding="utf-8") as f:

                    # We read the JSON data from the file:
                    data = json.load(f)

                    # WE create a Prompt object using the data:
                    prompt_obj = Prompt(**data)

                    # We append the prompt to the group's prompts list:
                    group.prompts.append(prompt_obj)

            groups.append(group)
        return groups

    # ----------------------------------------------------------------
    def save_prompt_group(self, group: PromptGroup) -> None:
        """
        Save an entire prompt group and all its prompts as JSON files.

        This method ensures that a directory exists for the given prompt group,
        and then saves each contained prompt by delegating to
        `save_prompt()`.

        Args:
            group (PromptGroup):
                The prompt group object containing multiple
                `Prompt` instances to save.

        Raises:
            OSError:
                If the directory cannot be created or files cannot be written.
        """
        group_path = os.path.join(self.base_path, group.name)

        # Make directory if it doesn't exist:
        os.makedirs(group_path, exist_ok=True)

        # Iterate over all prompts in the group and save each one:
        for prompt_obj in group.prompts:
            self.save_prompt(group.name, prompt_obj)

    # ----------------------------------------------------------------
    def save_prompt(self, group_name: str, prompt_obj: Prompt) -> None:
        """
        Save a single prompt object to its corresponding group folder as a JSON file.

        If the target folder does not exist, it is automatically created.
        If a file with the same name already exists, it will be overwritten.

        Args:
            group_name (str):
                The name of the prompt group (maps to a folder under the base path).
            prompt_obj (Prompt):
                The prompt object to serialize and save.

        Raises:
            OSError:
                If the directory cannot be created or the file cannot be written.
            TypeError:
                If the provided prompt is not serializable to JSON.
        """
        group_path = os.path.join(self.base_path, group_name)
        file_path = os.path.join(group_path, f"{prompt_obj.name}.json")

        # Make directory if it doesn't exist:
        os.makedirs(group_path, exist_ok=True)

        # Write prompt data to JSON file and overwrite if it exists:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(asdict(prompt_obj), f, indent=4, ensure_ascii=False)

    # ----------------------------------------------------------------
    def delete_prompt_group(self, group_name: str) -> None:
        """
        Deletes an entire prompt group folder and all its contents.

        Args:
            group_name: The folder name under 'Prompts/' to remove.
        """
        group_path = os.path.join(self.base_path, group_name)

        if os.path.exists(group_path):
            shutil.rmtree(group_path)  # deletes entire folder recursively
            print(f"Deleted prompt group: {group_path}")
        else:
            print(f"Group '{group_name}' does not exist.")

    # ----------------------------------------------------------------
    def delete_prompt(self, group_name: str, prompt_name: str) -> None:
        """
        Deletes a single prompt JSON file from its group folder.

        Args:
            group_name: The name of the group (folder) under 'Prompts/'.
            prompt_name: The file name prefix (without .json).
        """
        group_path = os.path.join(self.base_path, group_name)
        file_path = os.path.join(group_path, f"{prompt_name}.json")

        if os.path.exists(file_path):
            os.remove(file_path)  # safely deletes the file
            print(f"Deleted prompt file: {file_path}")
        else:
            print(f"Prompt {prompt_name}.json not found in {group_name}")

##################################################################
