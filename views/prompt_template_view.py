# views/prompt_template_view.py
from __future__ import annotations
from typing import Callable, Dict, List, Optional
import gradio as gr

CREATE_SENTINEL = "➕ Create new template…"


class PromptTemplateView:
    def render_prompt_template_view(
        self,
        *,
        platform_choices: List[str],
        selected_platform: str,
        template_name_choices: List[str],
        selected_template: Optional[Dict],
        on_platform_changed: Callable[[str], tuple[List[str], Optional[Dict]]],
        on_template_changed: Callable[[str, str], Optional[Dict]],
        on_save_clicked: Optional[Callable[[str, Dict, bool], Dict]] = None,
        on_delete_clicked: Optional[Callable[[str, str], Dict]] = None,  # <-- NEW
    ) -> None:

        def _tpl_to_fields(tpl: Optional[Dict]):
            if not tpl:
                return ("", "", "", "", "", "-")
            req_vars_text = "\n".join(tpl.get("required_variables", []) or [])
            return (
                tpl.get("name", ""),
                tpl.get("description", "") or "",
                tpl.get("system_prompt", "") or "",
                tpl.get("user_prompt_template", "") or "",
                req_vars_text,
                tpl.get("last_updated", "-"),
            )

        def _fields_to_dict(plat, nm, ds, sp, up, rv_text, lu) -> Dict:
            reqs = [v.strip() for v in (rv_text or "").splitlines() if v.strip()]
            return {
                "platform": plat,
                "name": (nm or "").strip(),
                "version": "",
                "description": ds or "",
                "system_prompt": sp or "",
                "user_prompt_template": up or "",
                "required_variables": reqs,
                "last_updated": lu if lu and lu != "-" else "",
            }

        initial_names = [CREATE_SENTINEL] + list(template_name_choices or [])
        initial_selected_name = (
            selected_template["name"] if selected_template else CREATE_SENTINEL
        )
        init_name, init_desc, init_system, init_user, init_reqvars, init_lastupd = (
            _tpl_to_fields(selected_template)
        )

        with gr.Column():
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

            gr.Markdown("---")

            with gr.Row():
                with gr.Column(scale=3):
                    name_tb = gr.Textbox(
                        label="Name", value=init_name, interactive=True
                    )
                    desc_tb = gr.Textbox(
                        label="Description", value=init_desc, lines=2, interactive=True
                    )
                    system_tb = gr.Textbox(
                        label="System Prompt",
                        value=init_system,
                        lines=6,
                        interactive=True,
                    )
                    user_tb = gr.Textbox(
                        label="User Prompt",
                        value=init_user,
                        lines=32,
                        interactive=True
                    )

                with gr.Column(scale=1):
                    reqvars_tb = gr.Textbox(
                        label="Required Variables (one per line) (read-only)",
                        value=init_reqvars,
                        lines=47,
                        interactive=False,
                    )
                    lastupd_tb = gr.Textbox(
                    label="Last Updated (read-only)",
                    value=init_lastupd,
                    interactive=False,
                    scale=3,
                    )

            with gr.Row():
                save_btn = gr.Button("Save", variant="primary", scale=1)
                delete_btn = gr.Button("Delete", variant="stop", scale=1)  # <-- NEW

        # -------- events --------

        def _clear_fields():
            return (
                gr.update(value=""),
                gr.update(value=""),
                gr.update(value=""),
                gr.update(value=""),
                gr.update(value=""),
                gr.update(value="-"),
            )

        def _handle_platform_change(plat: str):
            names, tpl = on_platform_changed(plat)
            choices = [CREATE_SENTINEL] + names
            value = tpl.get("name") if tpl else CREATE_SENTINEL
            if tpl:
                nm, ds, sp, up, rv, lu = _tpl_to_fields(tpl)
            else:
                nm, ds, sp, up, rv, lu = ("", "", "", "", "", "-")
            # Enable delete only if not creating new
            del_enabled = value != CREATE_SENTINEL
            return (
                gr.update(choices=choices, value=value),
                gr.update(value=nm),
                gr.update(value=ds),
                gr.update(value=sp),
                gr.update(value=up),
                gr.update(value=rv),
                gr.update(value=lu),
                gr.update(interactive=del_enabled),  # delete_btn
            )

        platform_dd.change(
            fn=_handle_platform_change,
            inputs=[platform_dd],
            outputs=[
                template_dd,
                name_tb,
                desc_tb,
                system_tb,
                user_tb,
                reqvars_tb,
                lastupd_tb,
                delete_btn,
            ],
        )

        def _handle_template_change(plat: str, tpl_name: str):
            if tpl_name == CREATE_SENTINEL:
                del_enabled = False
                return (*_clear_fields(), gr.update(interactive=del_enabled))
            tpl = on_template_changed(plat, tpl_name)
            nm, ds, sp, up, rv, lu = _tpl_to_fields(tpl)
            del_enabled = True
            return (
                gr.update(value=nm),
                gr.update(value=ds),
                gr.update(value=sp),
                gr.update(value=up),
                gr.update(value=rv),
                gr.update(value=lu),
                gr.update(interactive=del_enabled),
            )

        template_dd.change(
            fn=_handle_template_change,
            inputs=[platform_dd, template_dd],
            outputs=[
                name_tb,
                desc_tb,
                system_tb,
                user_tb,
                reqvars_tb,
                lastupd_tb,
                delete_btn,
            ],
        )

        def _handle_save(plat, tpl_name_sel, nm, ds, sp, up, rv, lu):
            if on_save_clicked is None:
                gr.Info("Save not wired.")
                return (
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                )
            payload = _fields_to_dict(plat, nm, ds, sp, up, rv, lu)
            status = on_save_clicked(plat, payload, True)
            if not status.get("ok"):
                gr.Warning(status.get("message", "Save failed."))
                return (
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                )
            saved = status.get("saved") or {}
            names, _ = on_platform_changed(plat)  # refresh list
            choices = [CREATE_SENTINEL] + names
            new_value = saved.get("name") or tpl_name_sel or CREATE_SENTINEL
            nm2, ds2, sp2, up2, rv2, lu2 = _tpl_to_fields(saved)
            gr.Success(status.get("message", "Saved."))
            del_enabled = new_value != CREATE_SENTINEL
            return (
                gr.update(choices=choices, value=new_value),  # template_dd
                gr.update(value=nm2),
                gr.update(value=ds2),
                gr.update(value=sp2),
                gr.update(value=up2),
                gr.update(value=rv2),
                gr.update(value=lu2),
                gr.update(interactive=del_enabled),  # delete_btn
            )

        save_btn.click(
            fn=_handle_save,
            inputs=[
                platform_dd,
                template_dd,
                name_tb,
                desc_tb,
                system_tb,
                user_tb,
                reqvars_tb,
                lastupd_tb,
            ],
            outputs=[
                template_dd,
                name_tb,
                desc_tb,
                system_tb,
                user_tb,
                reqvars_tb,
                lastupd_tb,
                delete_btn,
            ],
        )

        # -------- DELETE (NEW) --------
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
                # Do not change fields if failed
                return (
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                )

            # Refresh names; reset selection to "Create new…"; clear fields; disable delete
            names, _ = on_platform_changed(plat)
            choices = [CREATE_SENTINEL] + names
            gr.Success(status.get("message", "Deleted."))
            return (
                gr.update(choices=choices, value=CREATE_SENTINEL),  # template_dd
                *(_clear_fields()),  # fields
                gr.update(interactive=False),  # delete_btn
            )

        delete_btn.click(
            fn=_handle_delete,
            inputs=[platform_dd, template_dd],
            outputs=[
                template_dd,
                name_tb,
                desc_tb,
                system_tb,
                user_tb,
                reqvars_tb,
                lastupd_tb,
                delete_btn,
            ],
        )
