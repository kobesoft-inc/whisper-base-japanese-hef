#!/usr/bin/env python3
"""Generate the decoder token-embedding asset required at inference.

The on-host token embedding is just OpenAI whisper-base's decoder token
embedding matrix (51865 x 512). It is large (~102 MB) so it is NOT shipped in
git — this script regenerates it locally from `openai/whisper-base`.

Run once after install:
    python3 prepare_assets.py
"""
import os
import numpy as np
from transformers import WhisperForConditionalGeneration

OUT = "app/decoder_assets/base/decoder_tokenization/token_embedding_weight_base.npy"

os.makedirs(os.path.dirname(OUT), exist_ok=True)
print("Downloading openai/whisper-base and extracting the token embedding...")
m = WhisperForConditionalGeneration.from_pretrained("openai/whisper-base")
emb = m.model.decoder.embed_tokens.weight.detach().cpu().numpy().astype("float32")
np.save(OUT, emb)
print(f"Saved {OUT}  shape={emb.shape}")
