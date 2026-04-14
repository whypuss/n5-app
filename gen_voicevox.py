#!/usr/bin/env python3
"""
Generate audio files using VOICEVOX API (port 50021).
Supports speed control and multiple speakers.
"""

import asyncio
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# VOICEVOX settings
BASE_URL = "http://localhost:50021"

# Speakers: (name, speaker_id)
# Female:  ずんだもん=3, 四国めたん=2, 春日部つむぎ=8, 雨晴はう=10
# Male:    玄野武宏=11, 白上虎太郎=12, 青山龍星=13
SPEAKERS = {
    "female": 3,   # ずんだもん ノーマル
    "male": 11,    # 玄野武宏 ノーマル
}

DEFAULT_SPEAKER = "female"  # which to use for single-file output
SPEED_SCALE = 1.0          # adjustable: 0.5=slow, 2.0=fast

AUDIO_DIR = Path(__file__).parent / "site" / "audio"
CHUNK_SIZE = 20
CONCURRENT = 8

def clean_text(text: str) -> str:
    """Remove ruby annotations and clean text for TTS"""
    text = text.strip()
    text = re.sub(r'<[^>]+>', '', text)        # remove <...>
    text = re.sub(r'【[^】]*】', '', text)     # remove 【...】
    text = re.sub(r'\[[^\]]*\]', '', text)     # remove [...]
    text = re.sub(r'（[^）]*）', '', text)     # remove （...）
    text = re.sub(r'\([^)]*\)', '', text)      # remove (...)
    text = re.sub(r'[\u3000\xa0]+', ' ', text) # remove special spaces
    text = re.sub(r'\s+', ' ', text)           # collapse whitespace
    return text.strip()

def url_encode_text(text: str) -> str:
    return urllib.parse.quote(text, safe='')

def generate_audio(text: str, speaker_id: int, speed: float, output_path: str) -> dict:
    """Generate audio using VOICEVOX API. Returns dict with ok status."""
    try:
        clean = clean_text(text)
        if not clean:
            return {"ok": False, "path": output_path, "error": "empty after cleaning"}

        # Step 1: audio_query
        encoded_text = url_encode_text(clean)
        query_url = f"{BASE_URL}/audio_query?text={encoded_text}&speaker={speaker_id}"

        req = urllib.request.Request(query_url, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        with urllib.request.urlopen(req, timeout=15) as resp:
            query = json.loads(resp.read())

        # Adjust speed
        query["speedScale"] = speed

        # Step 2: synthesis
        synth_url = f"{BASE_URL}/synthesis?speaker={speaker_id}"
        body = json.dumps(query).encode("utf-8")
        req2 = urllib.request.Request(synth_url, data=body, method="POST")
        req2.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req2, timeout=15) as resp2:
            audio_data = resp2.read()

        with open(output_path, "wb") as f:
            f.write(audio_data)

        return {"ok": True, "path": output_path, "text": clean[:40]}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")[:100]
        return {"ok": False, "path": output_path, "error": f"HTTP {e.code}: {err_body}"}
    except Exception as e:
        return {"ok": False, "path": output_path, "error": str(e)[:80]}

def generate_audio_task(args):
    """Wrapper for thread pool"""
    idx, text, speaker_id, speed, output_path = args
    return generate_audio(text, speaker_id, speed, output_path)

def main():
    base = Path(__file__).parent

    n5_path = base / "n5-v2-data.json"
    n1_path = base / "n1-data.json"

    if not n5_path.exists():
        print(f"ERROR: {n5_path} not found")
        sys.exit(1)
    if not n1_path.exists():
        print(f"ERROR: {n1_path} not found")
        sys.exit(1)

    n5_raw = json.loads(n5_path.read_text())
    n1_raw = json.loads(n1_path.read_text())

    n5_data = n5_raw["sentences"] if isinstance(n5_raw, dict) else n5_raw
    n1_data = n1_raw["sentences"] if isinstance(n1_raw, dict) else n1_raw

    # Prepare output dirs
    n5_audio = AUDIO_DIR / "n5"
    n1_audio = AUDIO_DIR / "n1"
    n5_audio.mkdir(parents=True, exist_ok=True)
    n1_audio.mkdir(parents=True, exist_ok=True)

    print(f"VOICEVOX Audio Generator")
    print(f"  Female: ずんだもん (ID={SPEAKERS['female']})")
    print(f"  Male:   玄野武宏 (ID={SPEAKERS['male']})")
    print(f"  Speed:  {SPEED_SCALE}")
    print(f"N5 items: {len(n5_data)}, N1 items: {len(n1_data)}")

    # Check API
    try:
        with urllib.request.urlopen(f"{BASE_URL}/version", timeout=5) as r:
            print(f"  API version: {r.read().decode()}\n")
    except Exception as e:
        print(f"ERROR: Cannot connect to VOICEVOX API at {BASE_URL}: {e}")
        sys.exit(1)

    # Build task list for N5 (female voice)
    print("=== N5 Audio (ずんだもん) ===")
    n5_tasks = []
    for d in n5_data:
        if not d.get("japanese"):
            continue
        idx = str(d["id"])
        n5_tasks.append((
            idx,
            d["japanese"],
            SPEAKERS["female"],
            SPEED_SCALE,
            str(n5_audio / f"{idx}.mp3")
        ))

    n5_ok, n5_fail = 0, 0
    with ThreadPoolExecutor(max_workers=CONCURRENT) as executor:
        results = list(executor.map(generate_audio_task, n5_tasks))

    for r in results:
        if r["ok"]:
            n5_ok += 1
        else:
            n5_fail += 1
            print(f"  FAIL [{r['path'].split('/')[-1]}] {r['error']}", flush=True)

    print(f"N5 done: {n5_ok} ok, {n5_fail} failed")

    # Build task list for N1 (male voice)
    print("\n=== N1 Audio (玄野武宏) ===")
    n1_tasks = []
    for d in n1_data:
        if not d.get("japanese"):
            continue
        idx = str(d["id"])
        n1_tasks.append((
            idx,
            d["japanese"],
            SPEAKERS["male"],
            SPEED_SCALE,
            str(n1_audio / f"{idx}.mp3")
        ))

    n1_ok, n1_fail = 0, 0
    with ThreadPoolExecutor(max_workers=CONCURRENT) as executor:
        results = list(executor.map(generate_audio_task, n1_tasks))

    for r in results:
        if r["ok"]:
            n1_ok += 1
        else:
            n1_fail += 1
            print(f"  FAIL [{r['path'].split('/')[-1]}] {r['error']}", flush=True)

    print(f"N1 done: {n1_ok} ok, {n1_fail} failed")
    print(f"\n=== Summary ===")
    print(f"N5: {n5_ok} ok, {n5_fail} failed")
    print(f"N1: {n1_ok} ok, {n1_fail} failed")

if __name__ == "__main__":
    main()
