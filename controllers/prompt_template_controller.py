"""
prompt_template_controller.py
=============================

Controller module for managing **PromptTemplate** interactions between the
view (`PromptTemplateView`) and the service layer (`PromptTemplateService`).

This controller is responsible for:
- Handling user-triggered events in the Prompt Template UI (e.g. platform or template selection, save/delete actions).
- Providing data to the view in a consistent, serializable dictionary format.
- Delegating all persistence and validation logic to `PromptTemplateService`.
- Acting as a stateless coordinator — it performs no direct I/O or business logic itself.

Key responsibilities:
----------------------
1. **Platform Changes (`on_platform_changed`)**
   - When the user switches the platform (e.g., OpenAI, Anthropic, etc.), the controller:
     - Lists all existing templates for that platform.
     - Automatically loads the first available template (if any) or provides placeholder rules for "Create new" mode.

2. **Template Changes (`on_template_changed`)**
   - Loads the selected template and returns its metadata and placeholder information.

3. **Saving (`on_save_clicked`)**
   - Creates or updates templates through the service layer.
   - Ensures only valid models are persisted.
   - Reloads the saved template to include accurate timestamps.

4. **Deleting (`on_delete_clicked`)**
   - Removes templates for the selected platform.

5. **Rendering (`render_prompt_template_view`)**
   - Initializes and renders the entire Prompt Template view with current state, callbacks, and default selections.

Notes:
------
- This controller is intentionally stateless — all persistent state and validation logic
  reside in the `PromptTemplateService`.
- The controller ensures graceful degradation: if a template fails to load, it falls back
  to showing only placeholder rules instead of raising an error.

Typical Flow:
--------------
User interacts with UI → View calls Controller callback → Controller fetches data
from Service → View updates displayed template → User saves/deletes → Controller
writes via Service → View re-renders.

"""

from __future__ import annotations
from typing import Dict, Optional
from datetime import timezone
from enums.platform_enum import PlatformEnum
from models.prompt_template_model import PromptTemplate
from services.prompt_template_service import PromptTemplateService
from views.prompt_template_view import PromptTemplateView


##################################################################
class PromptTemplateController:
    """
    Stateless controller for PromptTemplate view.
    - Supplies platform choices and template names
    - Loads selected template
    - Exposes callbacks for platform/template dropdown changes
    """

    # ----------------------------------------------------------------
    def __init__(self):
        self.prompt_template_view = PromptTemplateView()
        self.prompt_template_service = PromptTemplateService()

    # ================================================================
    # Helpers
    # ================================================================
    # ----------------------------------------------------------------
    def build_view_dict_for_prompt_template(self, t: PromptTemplate) -> Dict:
        """
        Build the dictionary shown in the view for a selected PromptTemplate.

        Includes all metadata fields plus platform-specific placeholder rules
        (required, optional) and the placeholders currently found in the
        system and user prompts.
        """
        req = self.prompt_template_service.get_required_placeholders(t.platform)
        opt = self.prompt_template_service.get_optional_placeholders(t.platform)
        found = self.prompt_template_service.extract_placeholders(t)

        return {
            "name": t.name,
            "platform": str(t.platform),
            "version": t.version,
            "description": t.description or "",
            "system_prompt": t.system_prompt or "",
            "user_prompt": t.user_prompt or "",
            "placeholders_required": req,
            "placeholders_optional": opt,
            "placeholders_found": found,
            "last_updated": t.last_updated.astimezone(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
        }

    # ================================================================
    # Callbacks wired by the view
    # ================================================================
    # ----------------------------------------------------------------
    def on_platform_changed(
        self, platform_str: str
    ) -> tuple[list[str], Optional[Dict]]:
        """
        Return (template_names, payload_dict):
        - If any templates exist: payload is the FIRST template converted via
            build_view_dict_for_prompt_template(...)
        - If none exist: payload has only required/optional placeholders so the
            view can show rules in 'Create new' mode.
        """

        platform = PlatformEnum.from_str(platform_str)

        # Get all template names for this platform
        names = self.prompt_template_service.list_all_prompt_template_names(platform)

        # If we have templates, load the first one
        if names:
            first = names[0]
            try:
                tpl = self.prompt_template_service.load_prompt_template(platform, first)
                return names, self.build_view_dict_for_prompt_template(tpl)
            except Exception as e:
                # degrade gracefully to rules-only if the first template fails to load
                print(
                    f"[WARN] load first template '{first}' for {platform.value} failed: {e}"
                )

        # no templates (or failed to load): return rules-only payload, view will then show CREATE SENTINEL
        return (
            names,  # likely []
            {
                "name": "",
                "description": "",
                "system_prompt": "",
                "user_prompt": "",
                "placeholders_required": self.prompt_template_service.get_required_placeholders(
                    platform
                ),
                "placeholders_optional": self.prompt_template_service.get_optional_placeholders(
                    platform
                ),
                "last_updated": "-",
                # optional: include platform so the view/controller can keep context
                "platform": str(platform),
            },
        )

    # ----------------------------------------------------------------
    def on_template_changed(self, platform_str: str, template_name: str):
        """Return selected_template_dict for (platform, template_name)."""

        # No template selected
        if not template_name:
            return None
        plat = PlatformEnum.from_str(platform_str)

        # Load and return the selected template
        tpl = self.prompt_template_service.load_prompt_template(plat, template_name)
        return self.build_view_dict_for_prompt_template(tpl)

    # ----------------------------------------------------------------
    def on_save_clicked(self, template_dict: Dict, overwrite: bool = True):
        """
        Save (create/update) a template.
        Returns: {"ok": bool, "message": str, "saved": Dict|None}
        """
        try:
            # Ensure we have a dict copy (otherwise we later delete "last_updated" from the caller's object)
            template_dict = dict(template_dict or {})

            # Discard user-sent timestamp
            template_dict.pop("last_updated", None)

            # Build model from dict
            model = PromptTemplate.from_dict(template_dict)

            # Persist (Validation happens inside)
            path = self.prompt_template_service.save_prompt_template(
                model, overwrite=overwrite
            )

            # Reload to reflect repo-stamped last_updated
            saved = self.prompt_template_service.load_prompt_template(
                model.platform, model.name
            )

            # Return success with saved model dict
            return {
                "ok": True,
                "message": f"Saved: {path}",
                "saved": self.build_view_dict_for_prompt_template(saved),
            }

        # Return failure with error message
        except ValueError as e:
            return {"ok": False, "message": str(e), "saved": None}
        except FileExistsError as e:
            return {"ok": False, "message": str(e), "saved": None}
        except Exception as e:
            return {"ok": False, "message": f"Save failed: {e}", "saved": None}

    # ----------------------------------------------------------------
    def on_delete_clicked(self, platform_str: str, template_name: str):
        """
        Delete a template.
        Returns: {"ok": bool, "message": str}
        """
        try:
            plat = PlatformEnum.from_str(platform_str)

            # No template selected
            if not template_name:
                return {"ok": False, "message": "No template selected."}

            # Call Service to delete
            deleted = self.prompt_template_service.delete_prompt_template(
                plat, template_name
            )

            # Return status
            if deleted:
                return {
                    "ok": True,
                    "message": f"Deleted: {platform_str}/{template_name}.json",
                }
            # Return failure - not found
            return {"ok": False, "message": "Template did not exist."}

        # Return failure with error message
        except Exception as e:
            return {"ok": False, "message": f"Delete failed: {e}"}

    # ================================================================
    # Entrypoint
    # ================================================================
    # ----------------------------------------------------------------
    def render_prompt_template_view(
        self, default_platform: Optional[PlatformEnum] = None
    ):
        """
        Render the entire Prompt Template view.

        - Determines the platform to display first (either the given default or the first available enum).
        - Lists all prompt templates for that platform.
        - Preloads the first available template (if any) as the initially selected one.
        - Passes all state and event callbacks to the view for rendering.
        """
        # Choose which platform to show on startup
        plat = default_platform or list(PlatformEnum)[0]

        # List of all available platforms (for the dropdown)
        platforms = PlatformEnum.to_list()

        # List all templates for the selected/default platform
        print("plat =", plat, "| type:", type(plat), "| str:", str(plat))

        names = self.prompt_template_service.list_all_prompt_template_names(plat)

        # Load the first template (if any) so the view shows something populated on load
        selected = (
            self.prompt_template_service.load_prompt_template(plat, names[0])
            if names
            else None
        )

        # Render the view with current state and callback bindings
        self.prompt_template_view.render_prompt_template_view(
            platform_choices=platforms,                             # dropdown options for platforms
            selected_platform=str(plat),                            # current platform selection
            template_name_choices=names,                            # dropdown options for templates
            selected_template=(
                self.build_view_dict_for_prompt_template(selected) if selected else None
            ),                                                      # preloaded template details (or None)
            on_platform_changed=self.on_platform_changed,           # callback: user changes platform
            on_template_changed=self.on_template_changed,           # callback: user changes template
            on_save_clicked=self.on_save_clicked,                   # callback: user saves template
            on_delete_clicked=self.on_delete_clicked,               # callback: user deletes template
        )

    # ----------------------------------------------------------------

##################################################################
