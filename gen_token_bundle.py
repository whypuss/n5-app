#!/usr/bin/env python3
"""
Generate a pre-tokenized bundle for Kokoro TTS on Android.
Converts Chinese text → phonemes → token IDs, saves as JSON.
"""
import json
import re
import espeakng_loader
from phonemizer.backend.espeak.wrapper import EspeakWrapper
import phonemizer
import sys
import os

# Setup espeak
EspeakWrapper.set_data_path(espeakng_loader.get_data_path())
EspeakWrapper.set_library(espeakng_loader.get_library_path())

# Load Kokoro vocab
CONFIG_PATH = os.path.join(os.path.dirname(espeakng_loader.__file__), '..', 'kokoro_onnx', 'config.json')
with open(CONFIG_PATH) as f:
    vocab = json.load(f)['vocab']


def phonemize_cmn(text: str) -> str:
    """Convert Chinese text to phonemes using Mandarin (cmn)."""
    ph = phonemizer.phonemize(text, 'cmn', preserve_punctuation=True, with_stress=True)
    # Strip language tags like (en), (cmn) and tone numbers
    ph = re.sub(r'\([^)]+\)', '', ph)
    ph = re.sub(r'[0-9]', '', ph)  # Remove tone numbers
    # Keep only vocab characters
    return ''.join(c for c in ph if c in vocab or c.strip() == '')


def phonemize_en(text: str) -> str:
    """Convert English text to phonemes."""
    ph = phonemizer.phonemize(text, 'en-us', preserve_punctuation=True, with_stress=True)
    ph = re.sub(r'\([^)]+\)', '', ph)
    return ''.join(c for c in ph if c in vocab or c.strip() == '')


def text_to_tokens(text: str, lang: str = 'cmn') -> list[int]:
    """Convert text to Kokoro token IDs."""
    ph = phonemize_cmn(text) if lang == 'cmn' else phonemize_en(text)
    tokens = [vocab[c] for c in ph if c in vocab and c.strip() != '']
    return tokens


def generate_demo_bundle() -> dict:
    """Generate bundle with demo podcast phrases."""
    entries = []

    # === PayMe Podcast 完整腳本 ===
    # Speaker: 0=xiaoni(女), 5=default_man(男)
    entries.append({"text": "各位 PayMe 用戶請注意，匯豐銀行最近發出了重要通知。從 5 月 14 號開始，電子支付平台將實施新的安全規定。", "speaker": "default_man", "tokens": text_to_tokens("各位 PayMe 用戶請注意，匯豐銀行最近發出了重要通知。從 5 月 14 號開始，電子支付平台將實施新的安全規定。", "cmn")})
    entries.append({"text": "沒錯，大家千萬不要掉以輕心！如果你在 App 裡收到要求驗證身份的通知，一定要盡快處理。", "speaker": "xiaoni", "tokens": text_to_tokens("沒錯，大家千萬不要掉以輕心！如果你在 App 裡收到要求驗證身份的通知，一定要盡快處理。", "cmn")})
    entries.append({"text": "具體來說，部分用戶必須上傳香港身份證進行認證，才能繼續使用 PayMe 的各項功能。", "speaker": "default_man", "tokens": text_to_tokens("具體來說，部分用戶必須上傳香港身份證進行認證，才能繼續使用 PayMe 的各項功能。", "cmn")})
    entries.append({"text": "如果超過期限還沒完成驗證，會發生什麼事呢？", "speaker": "xiaoni", "tokens": text_to_tokens("如果超過期限還沒完成驗證，會發生什麼事呢？", "cmn")})

    # === 完整 Podcast 腳本（用於測試）===
    entries.append({"text": "你好，歡迎收聽本期節目。首先，我們來看第一點。其次，是關於...最後，我想補充一點。感謝大家的收聽，我們下次再見。", "speaker": "xiaoni", "tokens": text_to_tokens("你好，歡迎收聽本期節目。首先，我們來看第一點。其次，是關於...最後，我想補充一點。感謝大家的收聽，我們下次再見。", "cmn")})

    # === 通用开场白 ===
    entries.append({"text": "你好，歡迎收聽本期節目。", "speaker": "xiaoni", "tokens": text_to_tokens("你好，歡迎收聽本期節目。", "cmn")})
    entries.append({"text": "大家好，歡迎來到 podcast。", "speaker": "xiaoni", "tokens": text_to_tokens("大家好，歡迎來到 podcast。", "cmn")})
    entries.append({"text": "今天的主題是...", "speaker": "xiaoni", "tokens": text_to_tokens("今天的主題是...", "cmn")})
    entries.append({"text": "讓我們開始吧。", "speaker": "xiaoni", "tokens": text_to_tokens("讓我們開始吧。", "cmn")})
    entries.append({"text": "感謝大家的收聽。", "speaker": "xiaoni", "tokens": text_to_tokens("感謝大家的收聽。", "cmn")})
    entries.append({"text": "我們下次再見。", "speaker": "xiaoni", "tokens": text_to_tokens("我們下次再見。", "cmn")})

    # === 常規描述 ===
    entries.append({"text": "這是一個很重要的話題。", "speaker": "xiaoni", "tokens": text_to_tokens("這是一個很重要的話題。", "cmn")})
    entries.append({"text": "讓我來介紹一下背景。", "speaker": "xiaoni", "tokens": text_to_tokens("讓我來介紹一下背景。", "cmn")})
    entries.append({"text": "首先，我們來看第一點。", "speaker": "xiaoni", "tokens": text_to_tokens("首先，我們來看第一點。", "cmn")})
    entries.append({"text": "其次，是關於...", "speaker": "xiaoni", "tokens": text_to_tokens("其次，是關於...", "cmn")})
    entries.append({"text": "最後，我想補充一點。", "speaker": "xiaoni", "tokens": text_to_tokens("最後，我想補充一點。", "cmn")})
    entries.append({"text": "總結來說，這個問題可以這樣看。", "speaker": "xiaoni", "tokens": text_to_tokens("總結來說，這個問題可以這樣看。", "cmn")})

    # === 日期時間 ===
    entries.append({"text": "今天是2024年1月1日。", "speaker": "xiaoni", "tokens": text_to_tokens("今天是2024年1月1日。", "cmn")})
    entries.append({"text": "最近發生了很多事情。", "speaker": "xiaoni", "tokens": text_to_tokens("最近發生了很多事情。", "cmn")})
    entries.append({"text": "這個消息引起了广泛关注。", "speaker": "xiaoni", "tokens": text_to_tokens("這個消息引起了广泛关注。", "cmn")})

    # === Podcast 對話格式 ===
    entries.append({"text": "[主播]: 大家好，歡迎收聽。", "speaker": "xiaoni", "tokens": text_to_tokens("大家好，歡迎收聽。", "cmn")})
    entries.append({"text": "[嘉賓]: 謝謝邀請，很高興來到這裡。", "speaker": "xiaoni", "tokens": text_to_tokens("謝謝邀請，很高興來到這裡。", "cmn")})
    entries.append({"text": "[主播]: 讓我們開始今天的話題。", "speaker": "xiaoni", "tokens": text_to_tokens("讓我們開始今天的話題。", "cmn")})
    entries.append({"text": "[嘉賓]: 好的，我準備好了。", "speaker": "xiaoni", "tokens": text_to_tokens("好的，我準備好了。", "cmn")})

    # === 英文短句（測試用）===
    entries.append({"text": "Welcome back to the show.", "speaker": "bella", "tokens": text_to_tokens("Welcome back to the show.", "en")})
    entries.append({"text": "This is absolutely fascinating.", "speaker": "bella", "tokens": text_to_tokens("This is absolutely fascinating.", "en")})
    entries.append({"text": "Let's dive right in.", "speaker": "bella", "tokens": text_to_tokens("Let's dive right in.", "en")})
    entries.append({"text": "Thanks for tuning in.", "speaker": "bella", "tokens": text_to_tokens("Thanks for tuning in.", "en")})

    # Filter out entries with no tokens
    entries = [e for e in entries if len(e["tokens"]) > 0]

    return {
        "version": 1,
        "vocab_size": len(vocab),
        "total_entries": len(entries),
        "entries": entries
    }


if __name__ == "__main__":
    bundle = generate_demo_bundle()
    output_path = sys.argv[1] if len(sys.argv) > 1 else "token_bundle.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(bundle, f, ensure_ascii=False, indent=2)
    print(f"Generated {bundle['total_entries']} entries → {output_path}")
    print(f"Vocab size: {bundle['vocab_size']}")
