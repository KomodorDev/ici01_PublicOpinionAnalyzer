"""
prompt_template_view.py
=======================

Gradio-based view for creating, editing, and deleting Prompt Templates.

This module renders the full Prompt Template UI and wires user interactions
to controller callbacks. It is intentionally **UI-only**:
- No file I/O or business logic lives here.
- All stateful operations are delegated to the controller layer.
- The controller returns ViewModels suitable for form fields.

Core responsibilities
---------------------
1) **Render UI**: Platform/template dropdowns, text areas, read-only panels.
2) **Bridge events**: Forward user actions to controller callbacks and reflect results.
3) **Create mode**: Support a "Create new template…" sentinel with rules-only side panel.
4) **Feedback**: Display inline notifications (success/warning/info) for actions.

Design notes
------------
- The view is **stateless** between calls; it renders what the controller provides.
- Placeholder rules (required/optional) are **read-only** and come from the controller/service.
- All updates use `gr.update(...)` for efficient re-rendering.
"""

from __future__ import annotations
from typing import Callable, Dict, Optional
import gradio as gr

from models.view_models.prompt_template.prompt_view_model import PromptTemplateViewModel
from models.view_models.prompt_template.prompt_template_detail_view_model import PromptTemplateDetailViewModel

CREATE_SENTINEL = "➕ Create new template…"


##################################################################
class PromptTemplateView:
    """
    Gradio view for managing prompt templates.

    Parameters (via `render_prompt_template_view`)
    ----------------------------------------------
    view_model : PromptTemplateViewModel
        The complete view state including platform choices, template names, and selected template.
        
    on_platform_changed : Callable[[str], PromptTemplateViewModel]
        Controller callback. Given a platform string, returns updated PromptTemplateViewModel.
        
    on_template_changed : Callable[[str, str], Optional[PromptTemplateDetailViewModel]]
        Controller callback. Given (platform_str, template_name), returns
        the selected template as a PromptTemplateDetailViewModel (or None).
        
    on_save_clicked : Optional[Callable[[Dict, bool], PromptTemplateViewModel]]
        Controller callback. Given (template_dict, overwrite=True) returns
        updated PromptTemplateViewModel with refreshed template list and selected template.
        
    on_delete_clicked : Optional[Callable[[str, str], PromptTemplateViewModel]]
        Controller callback. Given (platform_str, template_name) returns
        updated PromptTemplateViewModel.

    Behavior
    --------
    - Uses a sentinel option **"Create new template…"** to enter create mode.
    - Right-side panels display platform-specific placeholder rules (read-only).
    - Save/Delete update dropdowns and fields based on controller responses.
    """

    # ================================================================
    # ENTRY POINT
    # ================================================================
    def render_prompt_template_view(
        self,
        *,
        view_model: PromptTemplateViewModel,
        on_platform_changed: Callable[[str], PromptTemplateViewModel],
        on_template_changed: Callable[[str, str], Optional[PromptTemplateDetailViewModel]],
        on_save_clicked: Optional[Callable[[Dict, bool], PromptTemplateViewModel]] = None,
        on_delete_clicked: Optional[Callable[[str, str], PromptTemplateViewModel]] = None,
    ) -> None:
        """
        Render the complete Prompt Template management view using Gradio components.

        This view provides a full UI for creating, editing, and deleting prompt templates
        across different platforms. It builds the layout (dropdowns, textboxes, and buttons)
        and wires all user interactions (platform/template selection, save, delete) to
        controller-supplied callback functions.
        """

        # ================================================================
        # HELPERS
        # ================================================================
        def _tpl_to_fields(vm: Optional[PromptTemplateDetailViewModel]):
            """Return tuple of fields to populate textboxes."""
            if not vm:
                return ("", "", "", "", "-")
            return (
                vm.name,
                vm.description or "",
                vm.system_prompt or "",
                vm.user_prompt or "",
                vm.last_updated or "-",
            )

        def _fields_to_dict(plat, nm, ds, sp, up, lu) -> Dict:
            """Build payload sent to controller on save."""
            return {
                "platform": plat,
                "name": (nm or "").strip(),
                "version": "",
                "description": ds or "",
                "system_prompt": sp or "",
                "user_prompt": up or "",
                "last_updated": lu if lu and lu != "-" else "",
            }

        # ================================================================
        # INITIAL STATE
        # ================================================================
        initial_names = [CREATE_SENTINEL] + list(view_model.template_name_choices or [])
        initial_selected_name = (
            view_model.selected_template.name 
            if view_model.selected_template and view_model.selected_template.name 
            else CREATE_SENTINEL
        )
        init_name, init_desc, init_system, init_user, init_lastupd = _tpl_to_fields(view_model.selected_template)

        # ================================================================
        # LAYOUT
        # ================================================================
        with gr.Column():

            # ---------------- HEADER: Platform / Template selectors ----------------
            with gr.Row():
                platform_dd = gr.Dropdown(
                    label="Platform",
                    choices=view_model.platform_choices,
                    value=(
                        view_model.selected_platform
                        if view_model.selected_platform in view_model.platform_choices
                        else (view_model.platform_choices[0] if view_model.platform_choices else None)
                    ),
                    interactive=True,
                    scale=1,
                )
                template_dd = gr.Dropdown(
                    label="Template",
                    choices=initial_names,
                    value=(
                        initial_selected_name
                        if initial_selected_name in initial_names
                        else CREATE_SENTINEL
                    ),
                    interactive=True,
                    scale=1,
                )

            # Separation Line
            gr.Markdown("---")

            # ---------------- BODY: Left = form fields, Right = read-only panels ----------------
            with gr.Row():

                # ---------------- LEFT COLUMN: editable fields ----------------
                with gr.Column(scale=3):
                    name_tb = gr.Textbox(label="Name", value=init_name, interactive=True)
                    desc_tb = gr.Textbox(label="Description", value=init_desc, lines=2, interactive=True)
                    system_tb = gr.Textbox(label="System Prompt", value=init_system, lines=6, interactive=True)
                    user_tb = gr.Textbox(label="User Prompt", value=init_user, lines=32, interactive=True)

                # ---------------- RIGHT COLUMN: read-only placeholder rules + last updated ----------------
                with gr.Column(scale=1):
                    req_ph_tb = gr.Textbox(
                        label="Required Placeholders (read-only)",
                        value="\n".join(view_model.selected_template.placeholders_required) if view_model.selected_template else "",
                        lines=18,
                        interactive=False,
                    )
                    opt_ph_tb = gr.Textbox(
                        label="Optional Placeholders (read-only)",
                        value="\n".join(view_model.selected_template.placeholders_optional) if view_model.selected_template else "",
                        lines=18,
                        interactive=False,
                    )
                    lastupd_tb = gr.Textbox(
                        label="Last Updated (read-only)",
                        value=init_lastupd,
                        interactive=False,
                        scale=3,
                    )

            # ---------------- FOOTER: actions ----------------
            with gr.Row():
                save_btn = gr.Button("Save", variant="primary", scale=1)
                delete_btn = gr.Button("Delete", variant="stop", scale=1)

        # ================================================================
        # EVENT WIRING
        # ================================================================
        # ----------------------------------------------------------------
        def _clear_fields():
            """Clear text inputs and placeholder panels when 'Create new…'."""
            return (
                gr.update(value=""),  # name
                gr.update(value=""),  # desc
                gr.update(value=""),  # system
                gr.update(value=""),  # user
                gr.update(value=""),  # req placeholders
                gr.update(value=""),  # opt placeholders
                gr.update(value="-"), # last updated
            )

        # ----------------------------------------------------------------
        def _handle_platform_change(plat: str):
            """Refresh template names, current template (if any), and placeholder panels."""
            new_vm = on_platform_changed(plat)
            choices = [CREATE_SENTINEL] + (new_vm.template_name_choices or [])

            nm, ds, sp, up, lu = _tpl_to_fields(new_vm.selected_template)
            req = "\n".join(new_vm.selected_template.placeholders_required if new_vm.selected_template else [])
            opt = "\n".join(new_vm.selected_template.placeholders_optional if new_vm.selected_template else [])

            desired = nm or CREATE_SENTINEL
            value = desired if (desired in choices) else choices[0]  # Ensure selected value exists in choices, otherwise default to first choice

            del_enabled = value != CREATE_SENTINEL
            return (
                gr.update(choices=choices, value=value),                      # template_dd
                gr.update(value=nm if value != CREATE_SENTINEL else ""),      # name_tb
                gr.update(value=ds if value != CREATE_SENTINEL else ""),      # desc_tb
                gr.update(value=sp if value != CREATE_SENTINEL else ""),      # system_tb
                gr.update(value=up if value != CREATE_SENTINEL else ""),      # user_tb
                gr.update(value=req),                                         # req_ph_tb
                gr.update(value=opt),                                         # opt_ph_tb
                gr.update(value=lu if value != CREATE_SENTINEL else "-"),     # lastupd_tb
                gr.update(interactive=del_enabled),                           # delete_btn
            )

        platform_dd.change( # pylint: disable=no-member
            fn=_handle_platform_change,
            inputs=[platform_dd],   # Selected element, every Gradio component has a internal value property
            outputs=[
                template_dd,
                name_tb,
                desc_tb,
                system_tb,
                user_tb,
                req_ph_tb,
                opt_ph_tb,
                lastupd_tb,
                delete_btn,
            ],
        )

        # ----------------------------------------------------------------
        def _handle_template_change(plat: str, tpl_name: str):
            if tpl_name == CREATE_SENTINEL:
                # fetch platform rules so required/optional boxes are populated in "create" mode
                # Reuse on_platform_changed to reload the platform state, including placeholder rules for "create" mode (fields may not be empty)
                new_vm = on_platform_changed(plat)  # <- reuse existing callback which returns VM
                
                req = "\n".join(new_vm.selected_template.placeholders_required if new_vm.selected_template else [])
                opt = "\n".join(new_vm.selected_template.placeholders_optional if new_vm.selected_template else [])
                del_enabled = False
                return (
                    gr.update(value=""),  # name
                    gr.update(value=""),  # desc
                    gr.update(value=""),  # system
                    gr.update(value=""),  # user
                    gr.update(value=req), # required placeholders (READ-ONLY)
                    gr.update(value=opt), # optional placeholders (READ-ONLY)
                    gr.update(value="-"), # last updated
                    gr.update(interactive=del_enabled),
                )

            # existing branch for loading an actual template
            vm = on_template_changed(plat, tpl_name)
            nm, ds, sp, up, lu = _tpl_to_fields(vm)
            req = "\n".join(vm.placeholders_required if vm else [])
            opt = "\n".join(vm.placeholders_optional if vm else [])
            del_enabled = True
            return (
                gr.update(value=nm),
                gr.update(value=ds),
                gr.update(value=sp),
                gr.update(value=up),
                gr.update(value=req),
                gr.update(value=opt),
                gr.update(value=lu),
                gr.update(interactive=del_enabled),
            )


        template_dd.change( # pylint: disable=no-member
            fn=_handle_template_change,
            inputs=[platform_dd, template_dd],
            outputs=[
                name_tb,
                desc_tb,
                system_tb,
                user_tb,
                req_ph_tb,
                opt_ph_tb,
                lastupd_tb,
                delete_btn,
            ],
        )

        # ----------------------------------------------------------------
        def _handle_save(plat, tpl_name_sel, nm, ds, sp, up, lu):
            """Send payload to controller; controller responds with full PromptTemplateViewModel."""
            if on_save_clicked is None:
                gr.Info("Save not wired.")
                return (gr.update(),) * 9

            payload = _fields_to_dict(plat, nm, ds, sp, up, lu)
            vm = on_save_clicked(payload, True)
            
            # Check for error message
            if vm.error_message:
                gr.Warning(vm.error_message)
                # On error, return unchanged state
                return (gr.update(),) * 9

            # Success - use the returned ViewModel directly
            if vm.info_message:
                gr.Success(vm.info_message)
            
            # Build choices from ViewModel
            choices = [CREATE_SENTINEL] + (vm.template_name_choices or [])
            
            # Get selected template from ViewModel
            saved_vm = vm.selected_template
            new_value = saved_vm.name if saved_vm and saved_vm.name else (tpl_name_sel or CREATE_SENTINEL)
            
            # Extract fields from selected template
            nm2, ds2, sp2, up2, lu2 = _tpl_to_fields(saved_vm)
            req2 = "\n".join(saved_vm.placeholders_required if saved_vm else [])
            opt2 = "\n".join(saved_vm.placeholders_optional if saved_vm else [])
            del_enabled = new_value != CREATE_SENTINEL

            return (
                gr.update(choices=choices, value=new_value),  # template_dd
                gr.update(value=nm2),
                gr.update(value=ds2),
                gr.update(value=sp2),
                gr.update(value=up2),
                gr.update(value=req2),
                gr.update(value=opt2),
                gr.update(value=lu2),
                gr.update(interactive=del_enabled),
            )

        save_btn.click(     # pylint: disable=no-member
            fn=_handle_save,
            inputs=[
                platform_dd,
                template_dd,
                name_tb,
                desc_tb,
                system_tb,
                user_tb,
                lastupd_tb,
            ],
            outputs=[
                template_dd,
                name_tb,
                desc_tb,
                system_tb,
                user_tb,
                req_ph_tb,
                opt_ph_tb,
                lastupd_tb,
                delete_btn,
            ],
        )

        # ----------------------------------------------------------------
        def _handle_delete(plat: str, tpl_name: str):
            if on_delete_clicked is None:
                gr.Info("Delete not wired.")
                return (
                    gr.update(choices=[CREATE_SENTINEL], value=CREATE_SENTINEL),  # template_dd
                    *(_clear_fields()),  # 7 elements: name, desc, system, user, req, opt, lastupd
                    gr.update(interactive=False),  # delete_btn
                )

            if not tpl_name or tpl_name == CREATE_SENTINEL:
                gr.Warning("No template selected to delete.")
                return (
                    gr.update(choices=[CREATE_SENTINEL], value=CREATE_SENTINEL),  # template_dd
                    *(_clear_fields()),  # 7 elements: name, desc, system, user, req, opt, lastupd
                    gr.update(interactive=False),  # delete_btn
                )

            # returns PromptTemplateViewModel
            new_vm = on_delete_clicked(plat, tpl_name)
            
            if new_vm.error_message:
                gr.Warning(new_vm.error_message)
                # Return unchanged state if error
                return (gr.update(),) * 9

            if new_vm.info_message:
                gr.Success(new_vm.info_message)

            choices = [CREATE_SENTINEL] + (new_vm.template_name_choices or [])
            
            # After delete, controller logic selects first available or dummy.
            # new_vm.selected_template is populated.
            sel_vm = new_vm.selected_template
            nm, ds, sp, up, lu = _tpl_to_fields(sel_vm)
            req = "\n".join(sel_vm.placeholders_required if sel_vm else [])
            opt = "\n".join(sel_vm.placeholders_optional if sel_vm else [])
            
            new_val = sel_vm.name if sel_vm and sel_vm.name else CREATE_SENTINEL
            del_enabled = new_val != CREATE_SENTINEL

            return (
                gr.update(choices=choices, value=new_val),  # template_dd
                gr.update(value=nm),
                gr.update(value=ds),
                gr.update(value=sp),
                gr.update(value=up),
                gr.update(value=req),
                gr.update(value=opt),
                gr.update(value=lu),
                gr.update(interactive=del_enabled),
            )

        delete_btn.click( # pylint: disable=no-member
            fn=_handle_delete,
            inputs=[platform_dd, template_dd],
            outputs=[
                template_dd,
                name_tb,
                desc_tb,
                system_tb,
                user_tb,
                req_ph_tb,
                opt_ph_tb,
                lastupd_tb,
                delete_btn,
            ],
        )

##################################################################
