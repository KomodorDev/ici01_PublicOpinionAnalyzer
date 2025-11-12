"""
prompt_template_view.py
=======================

Gradio-based view for creating, editing, and deleting Prompt Templates.

This module renders the full Prompt Template UI and wires user interactions
to controller callbacks. It is intentionally **UI-only**:
- No file I/O or business logic lives here.
- All stateful operations are delegated to the controller layer.
- The controller returns serializable dict payloads suitable for form fields.

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
from typing import Callable, Dict, List, Optional
import gradio as gr

CREATE_SENTINEL = "➕ Create new template…"


##################################################################
class PromptTemplateView:
    """
    Gradio view for managing prompt templates.

    Parameters (via `render_prompt_template_view`)
    ----------------------------------------------
    platform_choices : List[str]
        All selectable platforms (enum string values).
    selected_platform : str
        Currently selected platform value.
    template_name_choices : List[str]
        Template names for the selected platform (without `.json`).
    selected_template : Optional[Dict]
        The currently selected template converted to a view dict, or `None`.
        Expected keys when present:
            - name, description, system_prompt, user_prompt, last_updated
            - placeholders_required (List[str])
            - placeholders_optional (List[str])
    on_platform_changed : Callable[[str], tuple[List[str], Optional[Dict]]]
        Controller callback. Given a platform string, returns:
            (template_names_for_platform, first_template_or_rules_dict)
        The second item may be a full template dict or a "rules-only" dict
        containing `placeholders_required`/`placeholders_optional`.
    on_template_changed : Callable[[str, str], Optional[Dict]]
        Controller callback. Given (platform_str, template_name), returns
        the selected template as a view dict (or None).
    on_save_clicked : Optional[Callable[[Dict, bool], Dict]]
        Controller callback. Given (template_dict, overwrite=True) returns
        `{"ok": bool, "message": str, "saved": Optional[Dict]}`.
    on_delete_clicked : Optional[Callable[[str, str], Dict]]
        Controller callback. Given (platform_str, template_name) returns
        `{"ok": bool, "message": str}`.

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
        platform_choices: List[str],
        selected_platform: str,
        template_name_choices: List[str],
        selected_template: Optional[Dict],
        on_platform_changed: Callable[[str], tuple[List[str], Optional[Dict]]],
        on_template_changed: Callable[[str, str], Optional[Dict]],
        on_save_clicked: Optional[Callable[[Dict, bool], Dict]] = None,
        on_delete_clicked: Optional[Callable[[str, str], Dict]] = None,
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
        def _tpl_to_fields(tpl: Optional[Dict]):
            """Return tuple of fields to populate textboxes.
               Note: required/optional placeholders come from controller/service,
               not from the template payload itself.
            """
            if not tpl:
                return ("", "", "", "", "-")
            return (
                tpl.get("name", ""),
                tpl.get("description", "") or "",
                tpl.get("system_prompt", "") or "",
                tpl.get("user_prompt", "") or "",
                tpl.get("last_updated", "-"),
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
        initial_names = [CREATE_SENTINEL] + list(template_name_choices or [])
        initial_selected_name = (
            selected_template["name"] if selected_template else CREATE_SENTINEL
        )
        init_name, init_desc, init_system, init_user, init_lastupd = _tpl_to_fields(selected_template)

        # ================================================================
        # LAYOUT
        # ================================================================
        with gr.Column():

            # ---------------- HEADER: Platform / Template selectors ----------------
            with gr.Row():
                platform_dd = gr.Dropdown(
                    label="Platform",
                    choices=platform_choices,
                    value=(
                        selected_platform
                        if selected_platform in platform_choices
                        else (platform_choices[0] if platform_choices else None)
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
                        value="\n".join(selected_template.get("placeholders_required", [])) if selected_template else "",
                        lines=18,
                        interactive=False,
                    )
                    opt_ph_tb = gr.Textbox(
                        label="Optional Placeholders (read-only)",
                        value="\n".join(selected_template.get("placeholders_optional", [])) if selected_template else "",
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
            names, tpl_or_rules = on_platform_changed(plat)
            choices = [CREATE_SENTINEL] + (names or [])

            nm, ds, sp, up, lu = _tpl_to_fields(tpl_or_rules)
            req = "\n".join((tpl_or_rules or {}).get("placeholders_required", []) or [])
            opt = "\n".join((tpl_or_rules or {}).get("placeholders_optional", []) or [])

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
                _, tpl_rules = on_platform_changed(plat)  # <- reuse existing callback
                req = "\n".join((tpl_rules or {}).get("placeholders_required", []) or [])
                opt = "\n".join((tpl_rules or {}).get("placeholders_optional", []) or [])
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
            tpl = on_template_changed(plat, tpl_name)
            nm, ds, sp, up, lu = _tpl_to_fields(tpl)
            req = "\n".join(tpl.get("placeholders_required", []) or [])
            opt = "\n".join(tpl.get("placeholders_optional", []) or [])
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
            """Send payload to controller; controller responds with 'saved' dict including placeholders."""
            if on_save_clicked is None:
                gr.Info("Save not wired.")
                return (gr.update(),) * 9

            payload = _fields_to_dict(plat, nm, ds, sp, up, lu)
            status = on_save_clicked(payload, True)
            if not status.get("ok"):
                gr.Warning(status.get("message", "Save failed."))
                return (gr.update(),) * 9

            saved = status.get("saved") or {}
            # refresh list of names for this platform
            names, _ = on_platform_changed(plat)
            choices = [CREATE_SENTINEL] + names
            new_value = saved.get("name") or tpl_name_sel or CREATE_SENTINEL

            nm2, ds2, sp2, up2, lu2 = _tpl_to_fields(saved)
            req2 = "\n".join(saved.get("placeholders_required", []) or [])
            opt2 = "\n".join(saved.get("placeholders_optional", []) or [])
            gr.Success(status.get("message", "Saved."))
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
                    gr.update(),
                    *(_clear_fields()),
                    gr.update(choices=[CREATE_SENTINEL], value=CREATE_SENTINEL),
                    gr.update(interactive=False),
                )

            if not tpl_name or tpl_name == CREATE_SENTINEL:
                gr.Warning("No template selected to delete.")
                return (
                    gr.update(),
                    *(_clear_fields()),
                    gr.update(choices=[CREATE_SENTINEL], value=CREATE_SENTINEL),
                    gr.update(interactive=False),
                )

            status = on_delete_clicked(plat, tpl_name)
            if not status.get("ok"):
                gr.Warning(status.get("message", "Delete failed."))
                return (gr.update(),) * 8

            names, _ = on_platform_changed(plat)
            choices = [CREATE_SENTINEL] + names
            gr.Success(status.get("message", "Deleted."))
            return (
                gr.update(choices=choices, value=CREATE_SENTINEL),  # template_dd
                *(_clear_fields()),
                gr.update(interactive=False),
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
