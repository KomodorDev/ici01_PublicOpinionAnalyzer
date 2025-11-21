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
from typing import Dict, Optional, Any
from datetime import timezone
from enums.platform_enum import PlatformEnum
from models.domain import PromptTemplate
from models.view_models.prompt_template.prompt_view_model import PromptTemplateViewModel
from models.view_models.prompt_template.prompt_template_detail_view_model import PromptTemplateDetailViewModel
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
    def _build_detail_view_model(self, t: PromptTemplate) -> PromptTemplateDetailViewModel:
        """
        Build the ViewModel shown in the view for a selected PromptTemplate.

        Includes all metadata fields plus platform-specific placeholder rules
        (required, optional) and the placeholders currently found in the
        system and user prompts.
        """
        req = self.prompt_template_service.get_required_placeholders(t.platform)
        opt = self.prompt_template_service.get_optional_placeholders(t.platform)
        found = self.prompt_template_service.extract_placeholders(t)

        return PromptTemplateDetailViewModel(
            name=t.name,
            platform=str(t.platform),
            description=t.description or "",
            system_prompt=t.system_prompt or "",
            user_prompt=t.user_prompt or "",
            placeholders_required=req,
            placeholders_optional=opt,
            placeholders_found=found,
            last_updated=t.last_updated.astimezone(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
        )

    # ----------------------------------------------------------------
    def _build_view_model_for_platform(
        self,
        platform: PlatformEnum,
        *,
        info_message: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> PromptTemplateViewModel:
        """
        Construct the full PromptTemplateViewModel for a given platform,
        optionally including status messages.
        """
        # 1) Load template names for this platform
        names = self.prompt_template_service.list_all_prompt_template_names(platform)

        # 2) Pick the first template (if any) otherwise build a "create mode" VM
        selected_vm: Optional[PromptTemplateDetailViewModel] = None
        if names:
            first_name = names[0]
            try:
                tpl = self.prompt_template_service.load_prompt_template(platform, first_name)
                selected_vm = self._build_detail_view_model(tpl)
            except Exception as e:
                print(
                    f"[WARN] load first template '{first_name}' for {platform.value} failed: {e}"
                )

        if not selected_vm:
            selected_vm = PromptTemplateDetailViewModel(
                name="",
                platform=str(platform),
                description="",
                system_prompt="",
                user_prompt="",
                placeholders_required=self.prompt_template_service.get_required_placeholders(
                    platform
                ),
                placeholders_optional=self.prompt_template_service.get_optional_placeholders(
                    platform
                ),
                last_updated="-",
            )

        return PromptTemplateViewModel(
            platform_choices=PlatformEnum.to_list(),
            selected_platform=str(platform),
            template_name_choices=names,
            selected_template=selected_vm,
            info_message=info_message,
            error_message=error_message,
        )

    # ================================================================
    # Callbacks wired by the view
    # ================================================================
    # ----------------------------------------------------------------
    def on_platform_changed(
        self, platform_str: str
    ) -> PromptTemplateViewModel:
        """
        Return updated PromptTemplateViewModel:
        - If any templates exist: payload is the FIRST template converted via
            _build_detail_view_model(...)
        - If none exist: payload has only required/optional placeholders so the
            view can show rules in 'Create new' mode.
        """

        platform = PlatformEnum.from_str(platform_str)
        return self._build_view_model_for_platform(platform)

    # ----------------------------------------------------------------
    def on_template_changed(
        self, platform_str: str, template_name: str
    ) -> Optional[PromptTemplateDetailViewModel]:
        """Return selected_template_vm for (platform, template_name)."""

        # No template selected
        if not template_name:
            return None
        plat = PlatformEnum.from_str(platform_str)

        # Load and return the selected template
        tpl = self.prompt_template_service.load_prompt_template(plat, template_name)
        return self._build_detail_view_model(tpl)

    # ----------------------------------------------------------------
    def on_save_clicked(self, template_dict: Dict, overwrite: bool = True) -> Dict[str, Any]:
        """
        Save (create/update) a template.
        Returns: {"ok": bool, "message": str, "saved": PromptTemplateDetailViewModel|None}
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
                "saved": self._build_detail_view_model(saved),
            }

        # Return failure with error message
        except ValueError as e:
            return {"ok": False, "message": str(e), "saved": None}
        except FileExistsError as e:
            return {"ok": False, "message": str(e), "saved": None}
        except Exception as e:
            return {"ok": False, "message": f"Save failed: {e}", "saved": None}

    # ----------------------------------------------------------------
    def on_delete_clicked(self, platform_str: str, template_name: str) -> PromptTemplateViewModel:
        """
        Delete a template.
        Returns: Updated PromptTemplateViewModel reflecting the deletion.
        """
        plat = PlatformEnum.from_str(platform_str)

        try:
            # No template selected
            if not template_name:
                return self._build_view_model_for_platform(
                    plat, error_message="No template selected."
                )

            # Call Service to delete
            deleted = self.prompt_template_service.delete_prompt_template(
                plat, template_name
            )

            # Return status
            if deleted:
                return self._build_view_model_for_platform(
                    plat, info_message=f"Deleted: {platform_str}/{template_name}.json"
                )
            
            # Return failure - not found
            return self._build_view_model_for_platform(
                plat, error_message="Template did not exist."
            )

        # Return failure with error message
        except Exception as e:
            return self._build_view_model_for_platform(
                plat, error_message=f"Delete failed: {e}"
            )

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

        # Construct the full ViewModel via shared helper
        vm = self._build_view_model_for_platform(plat)

        # Render the view with current state and callback bindings
        self.prompt_template_view.render_prompt_template_view(
            view_model=vm,
            on_platform_changed=self.on_platform_changed,
            on_template_changed=self.on_template_changed,
            on_save_clicked=self.on_save_clicked,
            on_delete_clicked=self.on_delete_clicked,
        )

    # ----------------------------------------------------------------

##################################################################
