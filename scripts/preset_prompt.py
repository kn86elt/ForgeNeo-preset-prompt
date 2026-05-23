"""
forge-neo-preset-prompt

Automatically loads user-defined Prompt templates (Positive/Negative) and Styles
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

    # shared.opts.forge_preset is the actual current value; ui_forge_preset.value
    # is a lambda (value=lambda: shared.opts.forge_preset), not a plain string.
    try:
        current_preset = shared.opts.forge_preset
        if current_preset not in arch_names:
            current_preset = arch_names[0]
    except Exception:
        current_preset = arch_names[0]

    with gr.Blocks(analytics_enabled=False) as tab:
        gr.Markdown("## Preset Prompt\nConfigure Prompt / Style applied when switching UI Presets.")

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
            copy_btn = gr.Button("↓ Copy current prompts & styles to template", variant="secondary")
        copy_status = gr.Markdown("")

        gr.Markdown("### txt2img")
        with gr.Row():
            t2i_ap  = gr.Checkbox(label="Apply Positive Prompt", value=True)
            t2i_anp = gr.Checkbox(label="Apply Negative Prompt", value=True)
        with gr.Row():
            t2i_p  = gr.Textbox(label="Positive Prompt", lines=3, scale=1)
            t2i_np = gr.Textbox(label="Negative Prompt", lines=3, scale=1)

        gr.Markdown("### img2img")
        with gr.Row():
            i2i_ap  = gr.Checkbox(label="Apply Positive Prompt", value=True)
            i2i_anp = gr.Checkbox(label="Apply Negative Prompt", value=True)
        with gr.Row():
            i2i_p  = gr.Textbox(label="Positive Prompt", lines=3, scale=1)
            i2i_np = gr.Textbox(label="Negative Prompt", lines=3, scale=1)

        gr.Markdown("### Styles")
        with gr.Row():
            apply_st    = gr.Checkbox(label="Apply Styles on preset switch")
            refresh_btn = gr.Button("↻ Refresh Styles", scale=0)
        with gr.Row():
            t2i_st = gr.Dropdown(
                label="txt2img Styles",
                choices=list(shared.prompt_styles.styles),
                multiselect=True,
                scale=1,
            )
            i2i_st = gr.Dropdown(
                label="img2img Styles",
                choices=list(shared.prompt_styles.styles),
                multiselect=True,
                scale=1,
            )

        with gr.Row():
            save_btn = gr.Button("Save Template", variant="primary")
        status = gr.Markdown("")

        fields = [t2i_ap, t2i_anp, t2i_p, t2i_np,
                  i2i_ap, i2i_anp, i2i_p, i2i_np,
                  apply_st, t2i_st, i2i_st]

        # ── Event handlers ───────────────────────────────────────────────────

        def _load_arch(preset):
            s = _arch(preset)
            valid = set(shared.prompt_styles.styles)
            return [
                s.get("t2i_apply_prompt",    True),
                s.get("t2i_apply_neg_prompt", True),
                s.get("t2i_prompt",          ""),
                s.get("t2i_neg_prompt",       ""),
                s.get("i2i_apply_prompt",    True),
                s.get("i2i_apply_neg_prompt", True),
                s.get("i2i_prompt",          ""),
                s.get("i2i_neg_prompt",       ""),
                s.get("apply_styles",         False),
                [x for x in s.get("t2i_styles", []) if x in valid],
                [x for x in s.get("i2i_styles", []) if x in valid],
            ]

        def _save_arch(preset, tap, tanp, tp, tnp, iap, ianp, ip, inp, ast, ts, is_):
            data = _read()
            data[preset] = {
                "t2i_apply_prompt":    tap,
                "t2i_apply_neg_prompt": tanp,
                "t2i_prompt":          tp,
                "t2i_neg_prompt":      tnp,
                "i2i_apply_prompt":    iap,
                "i2i_apply_neg_prompt": ianp,
                "i2i_prompt":          ip,
                "i2i_neg_prompt":      inp,
                "apply_styles":        ast,
                "t2i_styles":          ts,
                "i2i_styles":          is_,
            }
            _write(data)
            return f"Saved template for `{preset}`."

        def _save_global(auto_save, persist_recent):
            data = _read()
            data["auto_save"]      = auto_save
            data["persist_recent"] = persist_recent
            _write(data)
            return "Global settings saved."

        def _refresh_styles():
            shared.prompt_styles.reload()
            choices = list(shared.prompt_styles.styles)
            return gr.update(choices=choices), gr.update(choices=choices)

        # Copy: reads from _clipboard (maintained by _attach_handlers).
        # inputs=[] avoids any cross-Blocks component reference.
        def _do_copy():
            valid = set(shared.prompt_styles.styles)
            return [
                _clipboard.get("t2i_prompt", ""),
                _clipboard.get("t2i_neg",    ""),
                _clipboard.get("i2i_prompt", ""),
                _clipboard.get("i2i_neg",    ""),
                [x for x in _clipboard.get("t2i_styles", []) if x in valid],
                [x for x in _clipboard.get("i2i_styles", []) if x in valid],
                "Copied.",
            ]

        arch_dd.change(fn=_load_arch, inputs=[arch_dd], outputs=fields, show_progress=False)
        tab.load(fn=_load_arch, inputs=[arch_dd], outputs=fields, show_progress=False)

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
        refresh_btn.click(fn=_refresh_styles, outputs=[t2i_st, i2i_st], show_progress=False)

        copy_btn.click(
            fn=_do_copy,
            inputs=[],
            outputs=[t2i_p, t2i_np, i2i_p, i2i_np, t2i_st, i2i_st, copy_status],
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
    t2i_styles = _get_comp("txt2img", "styles")
    i2i_prompt = _get_comp("img2img", "prompt")
    i2i_neg    = _get_comp("img2img", "negative_prompt")
    i2i_styles = _get_comp("img2img", "styles")

    missing = [name for name, comp in [
        ("txt2img/prompt",  t2i_prompt),
        ("txt2img/neg",     t2i_neg),
        ("txt2img/styles",  t2i_styles),
        ("img2img/prompt",  i2i_prompt),
        ("img2img/neg",     i2i_neg),
        ("img2img/styles",  i2i_styles),
    ] if comp is None]
    if missing:
        print(f"[preset-prompt] WARNING: components not found: {missing}")
        return

    # Keep _clipboard current so the copy button can read without Gradio inputs.
    def _update_clipboard(t2p, t2n, i2p, i2n, t2s, i2s):
        _clipboard.update({
            "t2i_prompt": t2p or "",
            "t2i_neg":    t2n or "",
            "i2i_prompt": i2p or "",
            "i2i_neg":    i2n or "",
            "t2i_styles": t2s or [],
            "i2i_styles": i2s or [],
        })

    _cb_inputs = [t2i_prompt, t2i_neg, i2i_prompt, i2i_neg, t2i_styles, i2i_styles]
    for comp in _cb_inputs:
        comp.change(
            fn=_update_clipboard,
            inputs=_cb_inputs,
            outputs=[],
            queue=False,
            show_progress=False,
        )

    prev_preset_state = gr.State(value=None)

    prompt_inputs  = [t2i_prompt, t2i_neg, i2i_prompt, i2i_neg, t2i_styles, i2i_styles]
    prompt_outputs = [t2i_prompt, t2i_neg, i2i_prompt, i2i_neg, t2i_styles, i2i_styles]

    def _apply_template(preset):
        s = _arch(preset)

        def _apply(apply_key, value_key):
            if not s.get(apply_key, False):
                return gr.skip()
            return gr.update(value=s.get(value_key, ""))

        if s.get("apply_styles", False):
            valid = set(shared.prompt_styles.styles)
            st2i = gr.update(value=[x for x in s.get("t2i_styles", []) if x in valid])
            si2i = gr.update(value=[x for x in s.get("i2i_styles", []) if x in valid])
        else:
            st2i = gr.skip()
            si2i = gr.skip()

        return [
            _apply("t2i_apply_prompt",    "t2i_prompt"),
            _apply("t2i_apply_neg_prompt", "t2i_neg_prompt"),
            _apply("i2i_apply_prompt",    "i2i_prompt"),
            _apply("i2i_apply_neg_prompt", "i2i_neg_prompt"),
            st2i,
            si2i,
        ]

    def _restore_recent(preset):
        r = _recent[preset]
        valid = set(shared.prompt_styles.styles)
        return [
            gr.update(value=r.get("t2i_prompt",     "")),
            gr.update(value=r.get("t2i_neg_prompt", "")),
            gr.update(value=r.get("i2i_prompt",     "")),
            gr.update(value=r.get("i2i_neg_prompt", "")),
            gr.update(value=[x for x in r.get("t2i_styles", []) if x in valid]),
            gr.update(value=[x for x in r.get("i2i_styles", []) if x in valid]),
        ]

    def _load(new_preset, prev_preset,
              cur_t2i_p, cur_t2i_np, cur_i2i_p, cur_i2i_np,
              cur_t2i_st, cur_i2i_st):
        gs = _global_settings()

        # Also keep clipboard current (covers page-load and preset-switch moments)
        _update_clipboard(cur_t2i_p, cur_t2i_np, cur_i2i_p, cur_i2i_np,
                          cur_t2i_st, cur_i2i_st)

        if gs["auto_save"] and prev_preset is not None:
            snapshot = {
                "t2i_prompt":     cur_t2i_p,
                "t2i_neg_prompt": cur_t2i_np,
                "i2i_prompt":     cur_i2i_p,
                "i2i_neg_prompt": cur_i2i_np,
                "t2i_styles":     cur_t2i_st or [],
                "i2i_styles":     cur_i2i_st or [],
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
