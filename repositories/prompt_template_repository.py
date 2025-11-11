"""
prompt_template_repository.py
============================
"""

import json
from pathlib import Path
from typing import List, Optional
from dataclasses import asdict
from datetime import datetime, timezone

from enums.platform_enum import PlatformEnum
from models.prompt_template_model import PromptTemplate


##################################################################
class PromptTemplateRepository:
    """Repository for CRUD operations on prompt templates."""

    # ----------------------------------------------------------------
    def __init__(self, prompts_base_path: str = "Prompt_Templates"):
        self.base_path = Path(prompts_base_path)

    # ----------------------------------------------------------------
    # LOAD SINGLE
    def load_prompt_template(
        self, platform: PlatformEnum, template_name: str
    ) -> PromptTemplate:
        """
        Load a single prompt template.

        Args:
            platform: Platform enum (e.g., PlatformEnum.YOUTUBE)
            template_name: Template filename without .json

        Returns:
            PromptTemplate instance

        Raises:
            FileNotFoundError: If template doesn't exist
        """
        
        # Get path
        template_path = self._get_prompt_template_path(platform, template_name)
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        # Get template_data
        with open(template_path, "r", encoding="utf-8") as f:
            template_data = json.load(f)

        # Coerce platform (str) -> PlatformEnum
        plat = template_data.get("platform")
        template_data["platform"] = plat if isinstance(plat, PlatformEnum) else PlatformEnum(plat)

        # Coerce last_updated (ISO string) -> datetime (UTC)
        lu = template_data.get("last_updated")
        if isinstance(lu, str):
            # accept ...Z or ...+00:00
            if lu.endswith("Z"):
                lu = lu.replace("Z", "+00:00")
            template_data["last_updated"] = datetime.fromisoformat(lu).astimezone(timezone.utc)
        elif lu is None:
            template_data["last_updated"] = datetime.now(timezone.utc)

        # Ensure required_variables is a list (defensive)
        rv = template_data.get("required_variables")
        if rv is None:
            template_data["required_variables"] = []
        elif not isinstance(rv, list):
            template_data["required_variables"] = list(rv)

        return PromptTemplate(**template_data)

    # ----------------------------------------------------------------
    # LOAD ALL
    def load_all_prompt_templates(
        self, platform: Optional[PlatformEnum] = None
    ) -> List[PromptTemplate]:
        """
        Load all templates, optionally filtered by platform.

        Args:
            platform: Optional Platform enum. If None, loads from all platforms.

        Returns:
            List of PromptTemplate instances
        """
        
        # Initialize empty list for all loaded templates
        templates: List[PromptTemplate] = []

        # Determine which platforms to load from:
        # - If a specific platform is passed, use only that one.
        # - Otherwise, iterate over all defined PlatformEnum members.
        platforms = [platform] if platform else list(PlatformEnum)

        # Iterate through all selected platforms
        for plat in platforms:
            platform_path = self.base_path / str(plat)
            
            # Skip if the directory for that platform does not exist
            if not platform_path.exists():
                continue

            # Iterate through all JSON files in this platform folder
            for file in platform_path.glob("*.json"):
                
                # Skip any metadata.json files (not a real prompt template)
                if file.name == "metadata.json":
                    continue
                
                # Load the template using the single-file loader
                # This ensures platform enums and datetimes are parsed consistently
                try:
                    templates.append(self.load_prompt_template(plat, file.stem))
                except FileNotFoundError:
                    # Template disappeared between the time we listed and tried to read it.
                    # Non-critical; skip it and continue.
                    continue
                except Exception as e:
                    # Catch any other exception (e.g., JSON decode error, wrong schema).
                    # For strict behavior, replace `continue` with `raise`.
                    # Example: `raise ValueError(f"Failed to load {file}: {e}")`
                    continue

        return templates

    # ----------------------------------------------------------------
    # CREATE / UPDATE
    def save_prompt_template(
        self,
        platform: PlatformEnum,
        prompt_model: PromptTemplate,
        overwrite: bool = False
    ) -> str:
        """
        Save a prompt template to disk as JSON.

        - Updates `last_updated` to current UTC time.
        - Creates platform directory if missing.
        - Optionally protects against overwriting existing templates.
        """
        
        # Get filename from template name
        template_name = prompt_model.name
        
        # Build full save path (e.g. Prompt_Templates/youtube/template.json)
        template_path = self._get_prompt_template_path(platform, template_name)

        # Stop if file exists and overwrite is not allowed
        if template_path.exists() and not overwrite:
            raise FileExistsError(
                f"Template already exists: {template_path}. Use overwrite=True to replace."
            )

        # Update modification timestamp
        prompt_model.last_updated = datetime.now(timezone.utc)

        # Convert dataclass to dict for JSON serialization
        data = asdict(prompt_model)
        
        # Ensure enum and datetime fields are stored as strings
        data["platform"] = str(prompt_model.platform)       # PlatformEnum -> str
        data["last_updated"] = prompt_model.last_updated.isoformat()

        # Create platform directory if it doesn’t exist
        template_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the JSON file to disk
        with open(template_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Return the saved file path as string
        return str(template_path)


    # ----------------------------------------------------------------
    # DELETE
    def delete_prompt_template(
        self, platform: PlatformEnum, template_name: str
    ) -> bool:
        """
        Delete a prompt template.

        Args:
            platform: Platform enum
            template_name: Template filename without .json

        Returns:
            True if deleted, False if didn't exist
        """
        template_path = self._get_prompt_template_path(platform, template_name)
        if not template_path.exists():
            return False
        template_path.unlink()
        return True
    
    # ----------------------------------------------------------------
    # LIST PROMPT TEMPLATE NAMES
    def list_all_prompt_template_names(
        self, platform: Optional[PlatformEnum] = None
    ) -> List[str]:
        """
        List all prompt template names.

        Args:
            platform: Optional Platform enum. If None, lists templates across all platforms.

        Returns:
            List[str]: Template names (filenames without .json).
        """
        names: List[str] = []

        # Determine platforms to scan
        platforms = [platform] if platform else list(PlatformEnum)

        # Iterate through platform directories
        for plat in platforms:
            platform_path = self.base_path / str(plat)

            # Skip missing directories
            if not platform_path.exists():
                continue

            # Add all JSON filenames except metadata.json
            for file in platform_path.glob("*.json"):
                if file.name == "metadata.json":
                    continue
                names.append(file.stem)

        return names

    # ----------------------------------------------------------------
    # Helper Methods
    # ----------------------------------------------------------------

    # ----------------------------------------------------------------
    def _get_prompt_template_path(self, platform: PlatformEnum, template_name: str) -> Path:
        """Get full path to template file."""
        return self.base_path / str(platform) / f"{template_name}.json"

    # ----------------------------------------------------------------
    def prompt_template_exists(self, platform: PlatformEnum, template_name: str) -> bool:
        """Check if a template exists."""
        return self._get_prompt_template_path(platform, template_name).exists()

    # ----------------------------------------------------------------

##################################################################
