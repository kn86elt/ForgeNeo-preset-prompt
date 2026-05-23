# forge-neo-preset-prompt

Stable Diffusion WebUI Forge Neo 向け拡張機能。  
**UI Preset（モデルアーキテクチャ）を切り替えた際に、対応する Prompt テンプレートと Style を自動的にロードします。**

---

## 機能

- UI Preset ドロップダウン（SD / XL / Flux / Wan …）の切り替えに連動
- txt2img・img2img それぞれに独立した Positive / Negative Prompt テンプレートを設定可能
- Style（`styles.csv` に登録済みのスタイル名）の自動選択に対応
- フィールドごとにチェックボックスで適用/スキップを個別制御
- 設定は拡張フォルダ内の `preset_prompts.json` に保存（本体の `config.json` は無変更）

## 動作フロー

```
UI Preset ドロップダウンを変更
  │
  ├─ [既存の Forge Neo 処理]
  │    sampler / scheduler / steps / CFG / width / height を更新
  │
  └─ [この拡張の処理]
       ├─ Apply Positive Prompt が ON → txt2img / img2img の Positive Prompt を上書き
       ├─ Apply Negative Prompt が ON → txt2img / img2img の Negative Prompt を上書き
       └─ Apply Styles が ON        → txt2img / img2img の Style ドロップダウンを更新
```

チェックオフのフィールドは **現在の値を保持**します。  
チェックオンかつテキストが空欄の場合は **空欄に上書き**します（Negative Prompt クリアに活用できます）。

---

## インストール

拡張フォルダへのコピー（シンボリックリンク or 直接コピー）:

```
ForgeNeo/extensions/forge-neo-preset-prompt/
    scripts/
        preset_prompt.py   ← このリポジトリの scripts/preset_prompt.py
    preset_prompts.json    ← 初回 Save 時に自動生成
```

Forge Neo を再起動すると有効になります。

### シンボリックリンクでの運用（推奨）

```bat
mklink /D "C:\usr\sd\ForgeNeo\extensions\forge-neo-preset-prompt" "C:\usr\sd\forge-neo-preset"
```

---

## 設定方法

1. Forge Neo を起動し、上部タブから **"Preset Prompt"** を選択
2. 編集したい **UI Preset**（sd / xl / flux …）をドロップダウンで選択  
   → 選択と同時に保存済みの値がロードされます
3. 各フィールドを設定:

   | セクション | 項目 | 説明 |
   |---|---|---|
   | txt2img | Apply Positive Prompt | チェックオンで Positive Prompt を適用 |
   | txt2img | Apply Negative Prompt | チェックオンで Negative Prompt を適用 |
   | txt2img | Positive / Negative Prompt | テンプレートテキスト |
   | img2img | 同上 | img2img タブ用（txt2img とは独立） |
   | Styles | Apply Styles | チェックオンで Style ドロップダウンを更新 |
   | Styles | txt2img / img2img Styles | 適用するスタイル名（複数選択可） |

4. **"Save"** ボタンで保存  
5. UI Preset を切り替えるたびに自動適用されます

> **Refresh Styles ボタン**: `styles.csv` を再読み込みしてドロップダウンの選択肢を更新します。

---

## 設定ファイル

設定は拡張フォルダ直下の `preset_prompts.json` に保存されます。  
本体の `config.json` / `ui-config.json` は変更しません。

```json
{
  "sd": {
    "t2i_apply_prompt": true,
    "t2i_prompt": "masterpiece, best quality",
    "t2i_apply_neg_prompt": true,
    "t2i_neg_prompt": "worst quality, low quality",
    "i2i_apply_prompt": false,
    "i2i_prompt": "",
    "i2i_apply_neg_prompt": false,
    "i2i_neg_prompt": "",
    "apply_styles": false,
    "t2i_styles": [],
    "i2i_styles": []
  },
  "flux": {
    "t2i_apply_prompt": false,
    "t2i_prompt": "",
    "t2i_apply_neg_prompt": true,
    "t2i_neg_prompt": "",
    "i2i_apply_prompt": false,
    "i2i_prompt": "",
    "i2i_apply_neg_prompt": false,
    "i2i_neg_prompt": "",
    "apply_styles": true,
    "t2i_styles": ["My Flux Style"],
    "i2i_styles": []
  }
}
```

---

## 互換性

| 状況 | 動作 |
|---|---|
| 拡張未導入 | `preset_prompts.json` が存在しないだけ。Forge Neo 本体に影響なし |
| 拡張を削除 | `preset_prompts.json` がフォルダごと残るが `config.json` は無傷 |
| Forge Neo 本体の更新 | `forge_main_entry()` のシグネチャが変わった場合のみ要修正 |

---

## 対応アーキテクチャ

`PresetArch` に定義されているすべてのアーキテクチャに対応します:

| キー | モデル |
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

## 技術メモ

- `modules_forge.main_entry.forge_main_entry` をモンキーパッチして、プリセット変更イベントハンドラを Gradio の `gr.Blocks` コンテキスト内に追加登録
- プロンプトコンポーネントは `infotext_utils.paste_fields` の `api` 属性（`"prompt"` / `"negative_prompt"` / `"styles"`）で取得
- ページ初回ロード時も `Context.root_block.load()` により現在のプリセット値を適用
