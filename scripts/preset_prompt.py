"""
forge-neo-preset-prompt

Automatically loads user-defined Prompt templates (Positive/Negative)
when the UI Preset (PresetArch) is changed.

Settings are saved in preset_prompts.json in the extension folder.
config.json (main settings) is never modified.

Settings UI: "Preset Prompt" tab in WebUI
"""

import json
import os

import gradio as gr

from modules import script_callbacks, shared

# ── File paths ───────────────────────────────────────────────────────────────

_EXT_DIR       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SETTINGS_FILE = os.path.join(_EXT_DIR, "preset_prompts.json")
_RECENT_FILE   = os.path.join(_EXT_DIR, "recent_prompts.json")

# ── Session state ─────────────────────────────────────────────────────────────
# _clipboard: kept current by .change() hooks registered in _attach_handlers().
#             copy button reads from here with inputs=[] (no cross-Blocks refs).
# _recent:    per-arch snapshot for auto-save/restore.

_clipboard: dict = {}
_recent:    dict = {}

# ── Copy button label constant ────────────────────────────────────────────────

_COPY_LABEL = "↓ Copy current prompts to template"

# ── Settings I/O ─────────────────────────────────────────────────────────────

def _read() -> dict:
    try:
        with open(_SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"[preset-prompt] Failed to read settings: {e}")
        return {}


def _write(data: dict):
    with open(_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _arch(preset: str) -> dict:
    return _read().get(preset, {})


def _global_settings() -> dict:
    data = _read()
    return {
        "auto_save":      data.get("auto_save",      False),
        "persist_recent": data.get("persist_recent", False),
    }


# ── Recent prompts I/O ───────────────────────────────────────────────────────

def _read_recent() -> dict:
    try:
        with open(_RECENT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"[preset-prompt] Failed to read recent prompts: {e}")
        return {}


def _write_recent(data: dict):
    try:
        with open(_RECENT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[preset-prompt] Failed to write recent prompts: {e}")


def _init_recent():
    global _recent
    if _global_settings()["persist_recent"]:
        _recent = _read_recent()


_init_recent()


# ── 1. Settings tab ──────────────────────────────────────────────────────────

def _make_tab():
    from modules_forge.presets import PresetArch

    arch_names = [a.name for a in PresetArch]
    gs = _global_settings()

    try:
        current_preset = shared.opts.forge_preset
        if current_preset not in arch_names:
            current_preset = arch_names[0]
    except Exception:
        current_preset = arch_names[0]

    with gr.Blocks(analytics_enabled=False) as tab:
        gr.Markdown("## Preset Prompt\nConfigure Prompt applied when switching UI Presets.")

        # ── Global settings ──────────────────────────────────────────────────
        gr.Markdown("### Global Settings")
        with gr.Row():
            auto_save_cb = gr.Checkbox(
                label="Auto-save & restore prompts on preset switch",
                value=gs["auto_save"],
            )
            persist_cb = gr.Checkbox(
                label="Persist recent prompts across restarts",
                value=gs["persist_recent"],
            )
        with gr.Row():
            save_global_btn = gr.Button("Save Global Settings", variant="secondary", scale=0)
        global_status = gr.Markdown("")

        gr.Markdown("---")

        # ── Per-preset templates ─────────────────────────────────────────────
        gr.Markdown("### Per-Preset Templates")
        with gr.Row():
            arch_dd = gr.Dropdown(
                label="UI Preset",
                choices=arch_names,
                value=current_preset,
                scale=2,
            )
        with gr.Row():
            copy_btn = gr.Button(_COPY_LABEL, variant="secondary")

        gr.Markdown("### txt2img")
        with gr.Row():
            t2i_ap  = gr.Checkbox(label="Apply Positive Prompt", value=True)
            t2i_anp = gr.Checkbox(label="Apply Negative Prompt", value=True)
        with gr.Row():
            t2i_p  = gr.Textbox(label="Positive Prompt", lines=3, scale=1)
            t2i_np = gr.Textbox(label="Negative Prompt", lines=3, scale=1)

        with gr.Row():
            save_btn = gr.Button("Save Template", variant="primary")
        status = gr.Markdown("")

        # fields: the 4 template inputs (no styles)
        fields = [t2i_ap, t2i_anp, t2i_p, t2i_np]

        # ── Event handlers ───────────────────────────────────────────────────

        def _load_arch(preset):
            s = _arch(preset)
            return [
                s.get("t2i_apply_prompt",    True),
                s.get("t2i_apply_neg_prompt", True),
                s.get("t2i_prompt",          ""),
                s.get("t2i_neg_prompt",       ""),
                gr.update(value=_COPY_LABEL),   # reset copy_btn label
            ]

        # tab.load reads shared.opts at browser-request time (more reliable than
        # the static value= which is evaluated at server-startup time).
        def _load_current():
            try:
                preset = shared.opts.forge_preset
                if preset not in arch_names:
                    preset = arch_names[0]
            except Exception:
                preset = arch_names[0]
            s = _arch(preset)
            return [
                preset,
                s.get("t2i_apply_prompt",    True),
                s.get("t2i_apply_neg_prompt", True),
                s.get("t2i_prompt",          ""),
                s.get("t2i_neg_prompt",       ""),
                gr.update(value=_COPY_LABEL),
            ]

        def _save_arch(preset, tap, tanp, tp, tnp):
            data = _read()
            data[preset] = {
                "t2i_apply_prompt":    tap,
                "t2i_apply_neg_prompt": tanp,
                "t2i_prompt":          tp,
                "t2i_neg_prompt":      tnp,
            }
            _write(data)
            return f"Saved template for `{preset}`."

        def _save_global(auto_save, persist_recent):
            data = _read()
            data["auto_save"]      = auto_save
            data["persist_recent"] = persist_recent
            _write(data)
            return "Global settings saved."

        # Copy: reads from _clipboard (maintained by _attach_handlers).
        # inputs=[] avoids any cross-Blocks component reference.
        def _do_copy():
            return [
                _clipboard.get("t2i_prompt", ""),
                _clipboard.get("t2i_neg",    ""),
                gr.update(value="✓ Copied"),
            ]

        arch_dd.change(
            fn=_load_arch,
            inputs=[arch_dd],
            outputs=fields + [copy_btn],
            show_progress=False,
        )
        tab.load(
            fn=_load_current,
            outputs=[arch_dd] + fields + [copy_btn],
            show_progress=False,
        )

        save_btn.click(
            fn=_save_arch,
            inputs=[arch_dd] + fields,
            outputs=[status],
            show_progress=False,
        )
        save_global_btn.click(
            fn=_save_global,
            inputs=[auto_save_cb, persist_cb],
            outputs=[global_status],
            show_progress=False,
        )

        copy_btn.click(
            fn=_do_copy,
            inputs=[],
            outputs=[t2i_p, t2i_np, copy_btn],
            show_progress=False,
        )

    return tab


script_callbacks.on_ui_tabs(
    lambda: [(_make_tab(), "Preset Prompt", "preset_prompt")]
)


# ── 2. Monkey-patch forge_main_entry ─────────────────────────────────────────
# forge_main_entry() is called inside gr.Blocks context in ui.py:912,
# so we can register Gradio event handlers from within our wrapper.

import modules_forge.main_entry as _me  # noqa: E402

_orig_forge_main_entry = _me.forge_main_entry


def _patched_forge_main_entry():
    _orig_forge_main_entry()
    _attach_handlers()


_me.forge_main_entry = _patched_forge_main_entry


# ── 3. Register Gradio handlers ───────────────────────────────────────────────

def _attach_handlers():
    from gradio.context import Context

    from modules.infotext_utils import paste_fields
    from modules_forge.main_entry import ui_forge_preset

    def _get_comp(tab, api):
        fields = paste_fields.get(tab, {}).get("fields", [])
        return next((f.component for f in fields if f.api == api), None)

    t2i_prompt = _get_comp("txt2img", "prompt")
    t2i_neg    = _get_comp("txt2img", "negative_prompt")

    missing = [name for name, comp in [
        ("txt2img/prompt", t2i_prompt),
        ("txt2img/neg",    t2i_neg),
    ] if comp is None]
    if missing:
        print(f"[preset-prompt] WARNING: components not found: {missing}")
        return

    # Keep _clipboard current so the copy button can read without Gradio inputs.
    def _update_clipboard(t2p, t2n):
        _clipboard.update({
            "t2i_prompt": t2p or "",
            "t2i_neg":    t2n or "",
        })

    _cb_inputs = [t2i_prompt, t2i_neg]
    for comp in _cb_inputs:
        comp.change(
            fn=_update_clipboard,
            inputs=_cb_inputs,
            outputs=[],
            queue=False,
            show_progress=False,
        )

    prev_preset_state = gr.State(value=None)

    prompt_inputs  = [t2i_prompt, t2i_neg]
    prompt_outputs = [t2i_prompt, t2i_neg]

    def _apply_template(preset):
        s = _arch(preset)

        def _apply(apply_key, value_key):
            if not s.get(apply_key, False):
                return gr.skip()
            return gr.update(value=s.get(value_key, ""))

        return [
            _apply("t2i_apply_prompt",    "t2i_prompt"),
            _apply("t2i_apply_neg_prompt", "t2i_neg_prompt"),
        ]

    def _restore_recent(preset):
        r = _recent[preset]
        return [
            gr.update(value=r.get("t2i_prompt",     "")),
            gr.update(value=r.get("t2i_neg_prompt", "")),
        ]

    def _load(new_preset, prev_preset, cur_t2i_p, cur_t2i_np):
        gs = _global_settings()

        # Also keep clipboard current (covers page-load and preset-switch moments)
        _update_clipboard(cur_t2i_p, cur_t2i_np)

        if gs["auto_save"] and prev_preset is not None:
            snapshot = {
                "t2i_prompt":     cur_t2i_p,
                "t2i_neg_prompt": cur_t2i_np,
            }
            _recent[prev_preset] = snapshot
            if gs["persist_recent"]:
                rec = _read_recent()
                rec[prev_preset] = snapshot
                _write_recent(rec)

        if gs["auto_save"] and new_preset in _recent:
            result = _restore_recent(new_preset)
        else:
            result = _apply_template(new_preset)

        return result + [new_preset]

    all_inputs  = [ui_forge_preset, prev_preset_state] + prompt_inputs
    all_outputs = prompt_outputs + [prev_preset_state]

    ui_forge_preset.change(
        fn=_load,
        inputs=all_inputs,
        outputs=all_outputs,
        queue=False,
        show_progress=False,
    )

    Context.root_block.load(
        fn=_load,
        inputs=all_inputs,
        outputs=all_outputs,
        queue=False,
        show_progress=False,
    )
