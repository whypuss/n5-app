#!/usr/bin/env python3
"""Regenerate all audio files using edge-tts (Microsoft Neural TTS)"""

import asyncio
import json
import os
import re
import sys
from pathlib import Path

import warnings
warnings.filterwarnings("ignore")

import edge_tts

VOICE = "ja-JP-NanamiNeural"
AUDIO_DIR = Path(__file__).parent / "site" / "audio"
CHUNK_SIZE = 20
CONCURRENT = 10

def clean_text(text: str) -> str:
    """Remove ruby annotations and clean text"""
    text = text.strip()
    # Remove common annotation patterns like 【...】
    text = re.sub(r'【[^】]*】', '', text)
    # Remove <...> tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove patterns like (meaning) - sometimes seen
    text = re.sub(r'\([^)]*\)', '', text)
    text = text.strip()
    return text if text else text

async def generate_one(text: str, output_path: str, semaphore: asyncio.Semaphore) -> dict:
    async with semaphore:
        try:
            clean = clean_text(text)
            if not clean:
                return {"ok": False, "path": output_path, "error": "empty after cleaning"}

            comm = edge_tts.Communicate(clean, VOICE)
            await comm.save(output_path)

            return {"ok": True, "path": output_path, "text": clean[:40]}
        except Exception as e:
            return {"ok": False, "path": output_path, "error": str(e)[:80]}

async def main():
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

    # Handle both dict-with-sentences and raw list formats
    n5_data = n5_raw["sentences"] if isinstance(n5_raw, dict) else n5_raw
    n1_data = n1_raw["sentences"] if isinstance(n1_raw, dict) else n1_raw

    # Prepare output dirs
    n5_audio = AUDIO_DIR / "n5"
    n1_audio = AUDIO_DIR / "n1"
    n5_audio.mkdir(parents=True, exist_ok=True)
    n1_audio.mkdir(parents=True, exist_ok=True)

    print(f"N5 items: {len(n5_data)}, N1 items: {len(n1_data)}")

    semaphore = asyncio.Semaphore(CONCURRENT)

    # Process N5
    print("\n=== N5 Audio (edge-tts) ===")
    n5_items = [(str(d["id"]), d["japanese"]) for d in n5_data if d.get("japanese")]
    n5_ok = 0
    n5_fail = 0

    for i in range(0, len(n5_items), CHUNK_SIZE):
        chunk = n5_items[i:i+CHUNK_SIZE]
        tasks = []
        for idx, text in chunk:
            filename = f"{idx}.mp3"
            out_path = n5_audio / filename
            tasks.append(generate_one(text, str(out_path), semaphore))

        results = await asyncio.gather(*tasks)
        for r in results:
            if r["ok"]:
                n5_ok += 1
            else:
                n5_fail += 1
                print(f"  FAIL [{r['path'].split('/')[-1]}] {r['error']}", flush=True)
        print(f"  Progress: {min(i+CHUNK_SIZE, len(n5_items))}/{len(n5_items)}  ok={n5_ok} fail={n5_fail}", flush=True)

    print(f"N5 done: {n5_ok} ok, {n5_fail} failed")

    # Process N1
    print("\n=== N1 Audio (edge-tts) ===")
    n1_items = [(str(d["id"]), d["japanese"]) for d in n1_data if d.get("japanese")]
    n1_ok = 0
    n1_fail = 0

    for i in range(0, len(n1_items), CHUNK_SIZE):
        chunk = n1_items[i:i+CHUNK_SIZE]
        tasks = []
        for idx, text in chunk:
            filename = f"{idx}.mp3"
            out_path = n1_audio / filename
            tasks.append(generate_one(text, str(out_path), semaphore))

        results = await asyncio.gather(*tasks)
        for r in results:
            if r["ok"]:
                n1_ok += 1
            else:
                n1_fail += 1
                print(f"  FAIL [{r['path'].split('/')[-1]}] {r['error']}", flush=True)
        print(f"  Progress: {min(i+CHUNK_SIZE, len(n1_items))}/{len(n1_items)}  ok={n1_ok} fail={n1_fail}", flush=True)

    print(f"\n=== Summary ===")
    print(f"N5: {n5_ok} ok, {n5_fail} failed")
    print(f"N1: {n1_ok} ok, {n1_fail} failed")

if __name__ == "__main__":
    asyncio.run(main())
