# controllers/prompt_template_controller.py
from __future__ import annotations
from typing import Dict, List, Optional
from datetime import datetime, timezone
from enums.platform_enum import PlatformEnum
from models.prompt_template_model import PromptTemplate
from services.prompt_template_service import PromptTemplateService
from views.prompt_template_view import PromptTemplateView

class PromptTemplateController:
    """
    Stateless controller for PromptTemplate view.
    - Supplies platform choices and template names
    - Loads selected template
    - Exposes callbacks for platform/template dropdown changes
    """

    def __init__(self):

        self.prompt_template_view = PromptTemplateView()
        self.prompt_template_service = PromptTemplateService()

    # ---------- helpers ----------
    @staticmethod
    def _platform_choices() -> List[str]:
        return [str(p) for p in PlatformEnum]

    @staticmethod
    def _to_enum(platform_str: str) -> PlatformEnum:
        return PlatformEnum(platform_str)

    @staticmethod
    def _to_view_dict(t: PromptTemplate) -> Dict:
        return {
            "name": t.name,
            "platform": str(t.platform),
            "version": t.version,
            "description": t.description or "",
            "system_prompt": t.system_prompt or "",
            "user_prompt_template": t.user_prompt_template or "",
            "required_variables": list(t.required_variables or []),
            "last_updated": t.last_updated.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        }

    @staticmethod
    def _to_model(d: Dict) -> PromptTemplate:
        # accept ISO8601 Z or +00:00 (view may send back last_updated; repo will overwrite anyway)
        lu = d.get("last_updated")
        if isinstance(lu, str) and lu:
            if lu.endswith("Z"):
                lu = lu.replace("Z", "+00:00")
            last_updated = datetime.fromisoformat(lu).astimezone(timezone.utc)
        else:
            last_updated = datetime.now(timezone.utc)

        return PromptTemplate(
            platform=PlatformEnum(d["platform"]),
            name=d["name"],
            version=d.get("version", "1.0"),
            description=d.get("description", "") or "",
            system_prompt=d.get("system_prompt", "") or "",
            user_prompt_template=d.get("user_prompt_template", "") or "",
            required_variables=list(d.get("required_variables") or []),
            last_updated=last_updated,
        )

    # ---------- callbacks wired by the view ----------
    def on_platform_changed(self, platform_str: str):
        """Return (template_names, selected_template_dict|None) for the chosen platform."""
        plat = self._to_enum(platform_str)
        names = self.prompt_template_service.list_all_prompt_template_names(plat)
        if not names:
            return names, None
        tpl = self.prompt_template_service.load_prompt_template(plat, names[0])
        return names, self._to_view_dict(tpl)

    def on_template_changed(self, platform_str: str, template_name: str):
        """Return selected_template_dict for (platform, template_name)."""
        if not template_name:
            return None
        plat = self._to_enum(platform_str)
        tpl = self.prompt_template_service.load_prompt_template(plat, template_name)
        return self._to_view_dict(tpl)

    def on_save_clicked(self, platform_str: str, template_dict: Dict, overwrite: bool = True):
        """
        Save (create/update) a template.
        Returns: {"ok": bool, "message": str, "saved": Dict|None}
        """
        try:
            # enforce platform from dropdown, not from dict
            template_dict = dict(template_dict or {})
            template_dict["platform"] = platform_str

            model = self._to_model(template_dict)

            # minimal guards (domain/business validation should live elsewhere)
            if not model.name:
                return {"ok": False, "message": "Name is required.", "saved": None}
            if not model.system_prompt:
                return {"ok": False, "message": "System prompt is required.", "saved": None}
            if not model.user_prompt_template:
                return {"ok": False, "message": "User prompt template is required.", "saved": None}

            plat = self._to_enum(platform_str)
            path = self.prompt_template_service.save_prompt_template(plat, model, overwrite=overwrite)
            # reload to reflect repo-stamped last_updated
            saved = self.prompt_template_service.load_prompt_template(plat, model.name)
            return {"ok": True, "message": f"Saved: {path}", "saved": self._to_view_dict(saved)}
        except FileExistsError as e:
            return {"ok": False, "message": str(e), "saved": None}
        except Exception as e:
            return {"ok": False, "message": f"Save failed: {e}", "saved": None}

    def on_delete_clicked(self, platform_str: str, template_name: str):
        """
        Delete a template.
        Returns: {"ok": bool, "message": str}
        """
        try:
            plat = self._to_enum(platform_str)
            if not template_name:
                return {"ok": False, "message": "No template selected."}
            deleted = self.prompt_template_service.delete_prompt_template(plat, template_name)
            if deleted:
                return {"ok": True, "message": f"Deleted: {platform_str}/{template_name}.json"}
            return {"ok": False, "message": "Template did not exist."}
        except Exception as e:
            return {"ok": False, "message": f"Delete failed: {e}"}

    # ---------- entrypoint ----------
    def render_prompt_template_view(self, default_platform: Optional[PlatformEnum] = None):
        plat = default_platform or list(PlatformEnum)[0]
        platforms = self._platform_choices()
        names = self.prompt_template_service.list_all_prompt_template_names(plat)
        selected = self.prompt_template_service.load_prompt_template(plat, names[0]) if names else None

        self.prompt_template_view.render_prompt_template_view(
            platform_choices=platforms,
            selected_platform=str(plat),
            template_name_choices=names,
            selected_template=(self._to_view_dict(selected) if selected else None),
            on_platform_changed=self.on_platform_changed,
            on_template_changed=self.on_template_changed,
            on_save_clicked=self.on_save_clicked,       # (platform_str, template_dict, overwrite)->status
            on_delete_clicked=self.on_delete_clicked,   # (platform_str, template_name)->status
        )
