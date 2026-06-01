# whisper-base-japanese-hef

**Hailo-10H NPU で日本語の音声認識** — OpenAI `whisper-base` を日本語のキャリブレーション
データで再コンパイルし、Raspberry Pi 5 + **AI HAT+ 2（Hailo-10H）** 上で**日本語**を
完全オフラインで文字起こしできるようにした HEF と推論アプリです。

```
$ python3 -m app.app_hailo_whisper --hw-arch hailo10h --variant base
🎤 ...
おはようございます。今日もよろしくお願いします。
```

---

## 動作要件

| 項目 | 内容 |
|---|---|
| ボード | Raspberry Pi 5 + **AI HAT+ 2（Hailo-10H）** |
| OS | Raspberry Pi OS（Bookworm, 64-bit） |
| ランタイム | **HailoRT 5.x** + PCIe ドライバ（[Hailo Developer Zone](https://hailo.ai/developer-zone/) から入手） |
| Python | 3.11（システム） |

NPU が認識されているか確認:
```bash
hailortcli fw-control identify     # -> Device Architecture: HAILO10H
```

## インストール

```bash
git clone https://github.com/kobesoft-inc/whisper-base-japanese-hef.git
cd whisper-base-japanese-hef

# システムの PyHailoRT を継承する venv（HailoRT 同梱の Python バインディングを使う）
python3 -m venv --system-site-packages whisper_env
source whisper_env/bin/activate
pip install -r requirements.txt

# 音声処理用のシステムライブラリ
sudo apt install -y ffmpeg libportaudio2

# トークン埋め込みアセット（約102MB）を生成（openai/whisper-base から取得）
python3 prepare_assets.py
```

## 使い方

```bash
source whisper_env/bin/activate

# マイク入力（録音してから文字起こし）
python3 -m app.app_hailo_whisper --hw-arch hailo10h --variant base

# 直前の録音を再利用（録音し直さない）
python3 -m app.app_hailo_whisper --hw-arch hailo10h --variant base --reuse-audio
```

日本語の文字起こしは**設定済み**です（デコーダに `<|ja|><|transcribe|>` を与えています）。
追加のフラグ指定は不要です。

### 特定語彙を強める（任意）

プロンプトでデコーダを特定の語にバイアスできます:

```bash
WHISPER_PROMPT="神戸 ハイロ ラズベリーパイ 人工知能" \
  python3 -m app.app_hailo_whisper --hw-arch hailo10h --variant base
```

> `whisper-base`（74M の小型モデル）ではプロンプトの追従は弱めです。固定の用語集が
> ある場合は、後処理での置換辞書のほうが確実です。

## 精度の目安

`whisper-base` は小型（74M）です。

- **日常会話レベルの日本語 → 良好**（ほぼ正確）。
- **固有名詞・専門用語 → 誤りが出やすい**（例: 神戸→校部）。モデルサイズの限界です。
- レイテンシ（Pi 5 + Hailo-10H）: 短い発話で約 1〜2 秒（初回のみ読み込みに約 10 秒）。

## ファイル構成

```
app/
  app_hailo_whisper.py        # CLI エントリポイント
  hailo_whisper_pipeline.py   # NPU 推論
  whisper_hef_registry.py     # HEF パス
  hefs/h10h/base/             # 日本語キャリブ済み HEF（encoder 10s / decoder seq-64）
  decoder_assets/base/...     # onnx_add_input（同梱）/ token_embedding（prepare_assets.py で生成）
common/                       # 音声の前/後処理
prepare_assets.py
requirements.txt
```

## クレジット / ライセンス

MIT。[OpenAI Whisper](https://github.com/openai/whisper)、
[Hailo Application Code Examples](https://github.com/hailo-ai/Hailo-Application-Code-Examples)、
[hailocs/hailo-whisper](https://github.com/hailocs/hailo-whisper) を基にしています。
キャリブレーションデータ: [ReazonSpeech](https://huggingface.co/datasets/reazon-research/reazonspeech)。
詳細は [LICENSE](LICENSE) を参照してください。
