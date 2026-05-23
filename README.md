# ForgeNeo-preset-prompt

A [Stable Diffusion WebUI Forge Neo](https://github.com/lllyasviel/stable-diffusion-webui-forge) extension that automatically loads user-defined prompt templates when the **UI Preset** (model architecture) is switched.

[日本語版 README はこちら](README-ja.md)

---

## Features

- Triggered by the **UI Preset** dropdown (SD / XL / Flux / Wan …)
- Per-preset **Positive** and **Negative** prompt templates for txt2img
- Per-field **Apply** checkboxes — uncheck to keep the current value unchanged
- **Copy prompts from txt2img** — one-click snapshot of the current prompts into the template editor
- **Auto-save & restore** — pushes current prompts when leaving a preset and restores them on return; falls back to the saved template if no snapshot exists
- **Persist recent prompts** — optionally writes the auto-save buffer to disk so it survives restarts
- **Enable / disable** toggle — temporarily suspend template loading without losing your configuration
- Settings are stored in `preset_prompts.json` inside the extension folder; `config.json` is never touched

---

## Installation

### Method 1 — Extensions tab (recommended)

1. Open Forge Neo WebUI
2. Go to **Extensions** → **Install from URL**
3. Enter the URL and click **Install**:
   ```
   https://github.com/kn86elt/ForgeNeo-preset-prompt
   ```
4. Go to the **Installed** tab and click **Apply and restart UI**

### Method 2 — Manual placement

Clone (or download and unzip) the repository into the `extensions/` folder of your Forge Neo installation:

```
<ForgeNeo root>/
└── extensions/
    └── ForgeNeo-preset-prompt/
        └── scripts/
            └── preset_prompt.py
```

Then restart Forge Neo.

---

## Usage

### Basic workflow

1. Open Forge Neo — the **Preset Prompt** tab appears in the top navigation bar
2. Select the **UI Preset** you want to configure
3. Fill in the **Positive Prompt** and/or **Negative Prompt** template fields
4. Use the **Apply** checkboxes to control which fields are overwritten on preset switch  
   (unchecked = that field is left as-is when switching)
5. Click **Save Template**
6. Switch UI Presets — the template loads automatically

### Copy prompts from txt2img

Click **↓ Copy prompts from txt2img** to copy the current txt2img prompts into the template editor for the selected preset. Adjust if needed, then save.

### Apply template on preset switch

The checkbox below the preset selector enables or disables template loading. Uncheck to temporarily stop overwriting prompts when switching presets. The setting is saved automatically and persists across restarts.

### Global Settings

Click the **⚙ Global Settings** accordion to expand:

| Setting | Description |
|---|---|
| Auto-save & restore prompts on preset switch | Saves current prompts when leaving a preset and restores them when returning. Falls back to the saved template when no snapshot exists. |
| Persist recent prompts across restarts | Writes the auto-save buffer to `recent_prompts.json` so it survives Forge Neo restarts. |

---

## Settings files

| File | Contents |
|---|---|
| `preset_prompts.json` | Templates and global settings |
| `recent_prompts.json` | Auto-save buffer (only when Persist is enabled) |

Both files are stored inside the extension folder. `config.json` and `ui-config.json` are never modified.

Example `preset_prompts.json`:

```json
{
  "auto_save": false,
  "persist_recent": false,
  "enable": true,
  "sd": {
    "t2i_apply_prompt": true,
    "t2i_apply_neg_prompt": true,
    "t2i_prompt": "masterpiece, best quality",
    "t2i_neg_prompt": "worst quality, low quality"
  },
  "flux": {
    "t2i_apply_prompt": false,
    "t2i_apply_neg_prompt": true,
    "t2i_prompt": "",
    "t2i_neg_prompt": ""
  }
}
```

---

## Supported architectures

All architectures defined in `PresetArch`:

| Key | Model |
|---|---|
| `sd` | Stable Diffusion 1.x |
| `xl` | SDXL |
| `flux` | Flux.1 |
| `klein` | Flux.2 |
| `qwen` | Qwen-Image |
| `lumina` | Lumina-Image-2.0 |
| `zit` | Z-Image-Turbo |
| `wan` | Wan2.2 |
| `anima` | Anima |
| `ernie` | Ernie-Image |

---

## Compatibility

| Situation | Behavior |
|---|---|
| Extension not installed | No effect on Forge Neo — `preset_prompts.json` simply does not exist |
| Extension removed | JSON files remain in the old folder but `config.json` is untouched |
| Forge Neo update | Only affected if `forge_main_entry()` signature changes |
