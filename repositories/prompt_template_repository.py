"""
prompt_template_repository.py
============================
"""

import json
from pathlib import Path
from typing import List, Optional


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
    def load_prompt_template(self, platform: str, template_name: str) -> dict:
        """
        Load a single prompt template.
        
        Args:
            platform: Platform name (e.g., 'youtube')
            template_name: Template filename without .json
            
        Returns:
            Template dict
            
        Raises:
            FileNotFoundError: If template doesn't exist
        """
        template_path = self._get_prompt_template_path(platform, template_name)

        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        with open(template_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    # ----------------------------------------------------------------
    def load_all_prompt_templates(self, platform: Optional[str] = None) -> List[dict]:
        """
        Load all templates, optionally filtered by platform.
        
        Args:
            platform: Optional platform filter. If None, loads from all platforms.
            
        Returns:
            List of template dicts with metadata
        """
        templates = []

        if platform:
            platforms = [platform]
        else:
            platforms = [p.name for p in self.base_path.iterdir() if p.is_dir()]

        for plat in platforms:
            platform_path = self.base_path / plat

            if not platform_path.exists():
                continue

            for file in platform_path.glob("*.json"):
                # Skip metadata files
                if file.name == "metadata.json":
                    continue

                with open(file, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                    templates.append({
                        "platform": plat,
                        "filename": file.stem,
                        "template_id": template_data.get("template_id"),
                        "name": template_data.get("name"),
                        "version": template_data.get("version"),
                        "description": template_data.get("description"),
                        "full_data": template_data  # Include full template if needed
                    })

        return templates

    # ----------------------------------------------------------------
    def list_all_prompt_template_names(self, platform: str) -> List[dict]:
        """
        List template metadata for a specific platform.
        
        Args:
            platform: Platform name
            
        Returns:
            List of template metadata dicts (without full template content)
        """
        templates = []
        platform_path = self.base_path / platform

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
                    "description": data.get("description")
                })

        return templates

    # ----------------------------------------------------------------
    # CREATE / UPDATE Operations
    # ----------------------------------------------------------------

    # ----------------------------------------------------------------
    def save_prompt_template(
        self,
        platform: str,
        template_name: str,
        template_data: dict,
        overwrite: bool = False
    ) -> str:
        """
        Save a prompt template.
        
        Args:
            platform: Platform name
            template_name: Template filename without .json
            template_data: Template dict to save
            overwrite: If False, raises error if template exists
            
        Returns:
            Path to saved template
            
        Raises:
            FileExistsError: If template exists and overwrite=False
        """
        template_path = self._get_prompt_template_path(platform, template_name)

        # Check if exists
        if template_path.exists() and not overwrite:
            raise FileExistsError(
                f"Template already exists: {template_path}. Use overwrite=True to replace."
            )

        # Ensure platform directory exists
        template_path.parent.mkdir(parents=True, exist_ok=True)

        # Save template
        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(template_data, f, indent=2, ensure_ascii=False)

        return str(template_path)

    # ----------------------------------------------------------------
    # DELETE Operations
    # ----------------------------------------------------------------

    # ----------------------------------------------------------------
    def delete_prompt_template(self, platform: str, template_name: str) -> bool:
        """
        Delete a prompt template.
        
        Args:
            platform: Platform name
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
    def _get_prompt_template_path(self, platform: str, template_name: str) -> Path:
        """Get full path to template file."""
        return self.base_path / platform / f"{template_name}.json"

    # ----------------------------------------------------------------
    def prompt_template_exists(self, platform: str, template_name: str) -> bool:
        """Check if a template exists."""
        return self._get_prompt_template_path(platform, template_name).exists()

    # ----------------------------------------------------------------

##################################################################
