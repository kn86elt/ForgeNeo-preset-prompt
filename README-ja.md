# ForgeNeo-preset-prompt

[Stable Diffusion WebUI Forge Neo](https://github.com/lllyasviel/stable-diffusion-webui-forge) 向け拡張機能。**UI Preset**（モデルアーキテクチャ）を切り替えた際に、対応するプロンプトテンプレートを自動的にロードします。

---

## 機能

- UI Preset ドロップダウン（SD / XL / Flux / Wan …）の切り替えに連動
- プリセットごとに txt2img の **Positive / Negative プロンプト**テンプレートを設定可能
- フィールドごとの **Apply チェックボックス** — オフにすると、そのフィールドは切り替え時に上書きされない
- **↓ Copy prompts from txt2img** — txt2img の現在のプロンプトをワンクリックでテンプレートにコピー
- **Auto-save & restore** — プリセットを離れるときに現在のプロンプトを自動保存し、戻ったときに復元。スナップショットがない場合はテンプレートにフォールバック
- **Persist recent prompts** — 自動保存バッファをファイルに書き出し、Forge Neo 再起動後も保持
- **有効/無効トグル** — 設定を失わずにテンプレートの適用を一時停止できる
- 設定は拡張フォルダ内の `preset_prompts.json` に保存。`config.json` は一切変更しない

---

## インストール

### 方法 1 — Extensions タブからインストール（推奨）

1. Forge Neo WebUI を起動
2. **Extensions** → **Install from URL** を開く
3. 以下の URL を入力して **Install** をクリック:
   ```
   https://github.com/kn86elt/ForgeNeo-preset-prompt
   ```
4. **Installed** タブに移動し、**Apply and restart UI** をクリック

### 方法 2 — 手動配置

リポジトリをクローン（またはダウンロードして解凍）し、Forge Neo の `extensions/` フォルダに配置:

```
<Forge Neo インストールフォルダ>/
└── extensions/
    └── ForgeNeo-preset-prompt/
        └── scripts/
            └── preset_prompt.py
```

その後 Forge Neo を再起動してください。

---

## 使い方

### 基本的な流れ

1. Forge Neo を起動 — 上部タブに **Preset Prompt** タブが表示される
2. 設定したい **UI Preset** をドロップダウンで選択
3. **Positive Prompt** / **Negative Prompt** テンプレートフィールドを入力
4. **Apply** チェックボックスで、プリセット切り替え時に上書きするフィールドを制御  
   （オフにするとそのフィールドは現在の値を維持）
5. **Save Template** をクリックして保存
6. UI Preset を切り替えると自動的にテンプレートが適用される

### txt2img からのコピー

**↓ Copy prompts from txt2img** ボタンを押すと、現在の txt2img のプロンプトが選択中のプリセットのテンプレートフィールドにコピーされます。必要に応じて編集後に保存してください。

### プリセット切り替え時の適用 ON/OFF

プリセットセレクターの下にあるチェックボックスでテンプレートの適用を有効/無効にできます。オフにするとプリセット切り替え時にプロンプトが上書きされなくなります。この設定は自動保存されて再起動後も維持されます。

### Global Settings

**⚙ Global Settings** アコーディオンを展開:

| 設定 | 説明 |
|---|---|
| Auto-save & restore prompts on preset switch | プリセットを離れるとき現在のプロンプトを自動保存し、戻ったときに復元。スナップショットがなければテンプレートを適用。 |
| Persist recent prompts across restarts | 自動保存バッファを `recent_prompts.json` に書き出し、Forge Neo 再起動後も保持する。 |

---

## 設定ファイル

| ファイル | 内容 |
|---|---|
| `preset_prompts.json` | テンプレートおよびグローバル設定 |
| `recent_prompts.json` | 自動保存バッファ（Persist 有効時のみ生成） |

どちらも拡張フォルダ内に保存されます。`config.json` / `ui-config.json` は変更しません。

`preset_prompts.json` の例:

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

## 対応アーキテクチャ

`PresetArch` に定義されているすべてのアーキテクチャに対応:

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

## 互換性

| 状況 | 動作 |
|---|---|
| 拡張未導入 | Forge Neo 本体に影響なし。`preset_prompts.json` が存在しないだけ |
| 拡張を削除 | JSON ファイルは残るが `config.json` は無傷 |
| Forge Neo 本体の更新 | `forge_main_entry()` のシグネチャが変わった場合のみ要修正 |
