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
from models.prompt_template_model import PromptTemplateModel


##################################################################
class PromptTemplateRepository:
    """Repository for CRUD operations on prompt templates."""

    # ----------------------------------------------------------------
    def __init__(self, prompts_base_path: str = "Prompt_Templates"):
        self.base_path = Path(prompts_base_path)

    # ----------------------------------------------------------------
    # READ Operations
    # ----------------------------------------------------------------

    # ----------------------------------------------------------------
    def load_prompt_template(
        self, platform: PlatformEnum, template_name: str
    ) -> PromptTemplateModel:
        """
        Load a single prompt template.

        Args:
            platform: Platform enum (e.g., Platform.YOUTUBE)
            template_name: Template filename without .json

        Returns:
            PromptTemplateModel instance

        Raises:
            FileNotFoundError: If template doesn't exist
        """
        template_path = self._get_prompt_template_path(platform, template_name)
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        with open(template_path, "r", encoding="utf-8") as f:
            template_data = json.load(f)
        return PromptTemplateModel(**template_data)

    # ----------------------------------------------------------------
    def load_all_prompt_templates(
        self, platform: Optional[PlatformEnum] = None
    ) -> List[PromptTemplateModel]:
        """
        Load all templates, optionally filtered by platform.

        Args:
            platform: Optional Platform enum. If None, loads from all platforms.

        Returns:
            List of PromptTemplateModel instances
        """
        templates = []

        if platform:
            platforms = [platform]
        else:
            # Use all enum members defined in Platform
            platforms = list(PlatformEnum)

        for plat in platforms:
            platform_path = self.base_path / str(plat)
            if not platform_path.exists():
                continue

            for file in platform_path.glob("*.json"):
                if file.name == "metadata.json":
                    continue
                with open(file, "r", encoding="utf-8") as f:
                    template_data = json.load(f)
                    templates.append(PromptTemplateModel(**template_data))

        return templates

    # ----------------------------------------------------------------
    def list_all_prompt_template_names(
        self, platform: PlatformEnum
    ) -> List[dict]:
        """
        List template metadata for a specific platform.

        Args:
            platform: Platform enum

        Returns:
            List of template metadata dicts (without full template content)
        """
        templates = []
        platform_path = self.base_path / str(platform)
        if not platform_path.exists():
            return []

        for file in platform_path.glob("*.json"):
            if file.name == "metadata.json":
                continue
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                templates.append({
                    "filename": file.stem,
                    "template_id": data.get("template_id"),
                    "name": data.get("name"),
                    "version": data.get("version"),
                    "description": data.get("description"),
                })
        return templates

    # ----------------------------------------------------------------
    # CREATE / UPDATE Operations
    # ----------------------------------------------------------------

    # ----------------------------------------------------------------
    def save_prompt_template(
        self,
        platform: PlatformEnum,
        prompt_model: PromptTemplateModel,
        overwrite: bool = False
    ) -> str:
        """
        Save a prompt template.

        Args:
            platform: Platform enum
            prompt_model: PromptTemplateModel instance to save
            overwrite: If False, raises error if template exists

        Returns:
            Path to saved template

        Raises:
            FileExistsError: If template exists and overwrite=False
        """
        template_name = prompt_model.name  # Use name directly from the model

        template_path = self._get_prompt_template_path(platform, template_name)
        if template_path.exists() and not overwrite:
            raise FileExistsError(
                f"Template already exists: {template_path}. Use overwrite=True to replace."
            )

        prompt_model.last_updated = datetime.now(timezone.utc)

        template_path.parent.mkdir(parents=True, exist_ok=True)
        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(prompt_model), f, indent=2, ensure_ascii=False)
        return str(template_path)


    # ----------------------------------------------------------------
    # DELETE Operations
    # ----------------------------------------------------------------

    # ----------------------------------------------------------------
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
