# whisper-base-japanese-hef

**Hailo-10H NPU で日本語の音声認識** — OpenAI `whisper-base` を日本語のキャリブレーション
データで再コンパイルし、Raspberry Pi 5 + **AI HAT+ 2（Hailo-10H）** 上で**日本語**を
完全オフラインで文字起こしできるようにしたものです。

```
$ python3 -m app.app_hailo_whisper --hw-arch hailo10h --variant base
🎤 ...
おはようございます。今日もよろしくお願いします。
```

公開されている Hailo 向け whisper HEF は英語音声でキャリブレーションされており、日本語では
出力が崩壊します。本リポジトリは**日本語（ReazonSpeech）でキャリブレーションした HEF**と、
NPU 上で日本語が正しく出力されるようにした推論パイプラインを同梱しています。

---

## 動作要件

| 項目 | 内容 |
|---|---|
| ボード | Raspberry Pi 5 + **AI HAT+ 2（Hailo-10H）** |
| OS | Raspberry Pi OS（Bookworm, 64-bit） |
| ランタイム | **HailoRT 5.x** + PCIe ドライバ（[Hailo Developer Zone](https://hailo.ai/developer-zone/) から入手） |
| Python | 3.11（システム） |

まず NPU が認識されているか確認します:
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

# トークン埋め込みアセット（約102MB）を生成
#   openai/whisper-base から取得。サイズが大きいため git には含めていません。
python3 prepare_assets.py
```

## 実行

```bash
source whisper_env/bin/activate

# マイク入力（録音してから文字起こし）
python3 -m app.app_hailo_whisper --hw-arch hailo10h --variant base

# 直前の録音を再利用（録音し直さない）
python3 -m app.app_hailo_whisper --hw-arch hailo10h --variant base --reuse-audio
```

日本語の文字起こしは**設定済み**です（デコーダに `<|ja|><|transcribe|>` を与えています）。
フラグ指定は不要です。

### 特定語彙を強める（任意）

プロンプトでデコーダを特定の語にバイアスできます:

```bash
WHISPER_PROMPT="神戸 ハイロ ラズベリーパイ 人工知能" \
  python3 -m app.app_hailo_whisper --hw-arch hailo10h --variant base
```

> 注意: `whisper-base`（74M の小型モデル）ではプロンプトの追従は弱く不安定です。
> 固定の用語集がある場合は、後処理での置換辞書のほうが確実です。

## 精度について

`whisper-base` は小型（74M）です。目安:

- **日常会話レベルの日本語 → 良好**（ほぼ正確）。
- **固有名詞・専門用語 → 誤りが出やすい**（例: 神戸→校部）。これは量子化ではなく
  モデルサイズの限界です。

さらに高精度が必要な場合は、より大きいモデル（whisper-small/medium や kotoba-whisper）
が必要で、別途の（より大規模な）Hailo 移植作業になります。

Pi 5 + Hailo-10H でのレイテンシ: 短い発話で約 1〜2 秒（初回のみモデル/ランタイム読み込みに
約 10 秒）。

## 仕組み

```
マイク ─► mel ─► [encoder.hef]──► 音声特徴量 ──┐
                                              ├─► 貪欲デコード ─► テキスト
host トークン埋め込み(npy) ─► [decoder.hef]◄──┘   (seq 64 / 10秒窓)
```

日本語が正しく出力されるための重要な 2 点（Hailo 標準サンプルには無い変更）:

1. **デコーダに日本語転写プレフィックスを与える** `[<|sot|>, <|ja|>, <|transcribe|>,
   <|notimestamps|>]`。標準パイプラインは `<|sot|>` のみで自動判定するため、たまに
   英語へ翻訳してしまいます。
2. **host 側のトークン埋め込みに位置埋め込みを加算する**（`app/hailo_whisper_pipeline.py`
   の `add_embed=True`）。デコーダはこれを前提に校正されており、加算なし（標準の
   `add_embed=False`）だと即座に `<|endoftext|>` を出して本文が空になります。

## ファイル構成

```
app/
  app_hailo_whisper.py        # CLI エントリポイント
  hailo_whisper_pipeline.py   # NPU 推論（JAプレフィックス + add_embed=True + WHISPER_PROMPT）
  whisper_hef_registry.py     # HEF パス
  hefs/h10h/base/             # 日本語キャリブ済み HEF（encoder 10s / decoder seq-64）
  decoder_assets/base/...     # onnx_add_input（同梱）/ token_embedding（prepare_assets.py で生成）
common/                       # 音声の前/後処理
prepare_assets.py
requirements.txt
```

## HEF を自分でビルドするには

本リポジトリの HEF は、Hailo Dataflow Compiler 5.3.0 を用いて `openai/whisper-base` から、
日本語の ReazonSpeech 約 3000 クリップでキャリブレーション（入力 10 秒 / デコーダ 64 トークン）
して生成しています。再現可能な変換パイプライン一式（EC2/RunPod の GPU スクリプト、
キャリブデータ取得、変換、トラブルシュート記録）は開発用リポジトリ
**whisper-base-japanese-hef-dev** にあります。

## クレジット / ライセンス

MIT。[OpenAI Whisper](https://github.com/openai/whisper)、
[Hailo Application Code Examples](https://github.com/hailo-ai/Hailo-Application-Code-Examples)、
[hailocs/hailo-whisper](https://github.com/hailocs/hailo-whisper) を基にしています。
キャリブレーションデータ: [ReazonSpeech](https://huggingface.co/datasets/reazon-research/reazonspeech)。
詳細は [LICENSE](LICENSE) を参照してください。
