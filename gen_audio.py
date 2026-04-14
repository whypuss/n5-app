#!/usr/bin/env python3
"""
Generate audio files for N5/N1/N2 using VOICEVOX API.
Usage:
  python3 gen_audio.py --level n5 --voice f   # N5 female (already done)
  python3 gen_audio.py --level n5 --voice m   # N5 male (missing)
  python3 gen_audio.py --level n1 --voice f   # N1 female (missing)
  python3 gen_audio.py --level n1 --voice m   # N1 male (already done)
  python3 gen_audio.py --level n2 --voice f   # N2 female (missing)
  python3 gen_audio.py --level n2 --voice m   # N2 male (missing)
  python3 gen_audio.py --level n2 --voice both  # N2 both voices
"""

import argparse
import asyncio
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "http://localhost:50021"

# Speakers
SPEAKERS = {
    "f": 3,    # ずんだもん (female)
    "m": 11,   # 玄野武宏 (male)
}

SPEED_SCALE = 1.0
CONCURRENT = 8

def clean_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'【[^】]*】', '', text)
    text = re.sub(r'\[[^\]]*\]', '', text)
    text = re.sub(r'（[^）]*）', '', text)
    text = re.sub(r'\([^)]*\)', '', text)
    text = re.sub(r'[\u3000\xa0]+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def url_encode_text(text: str) -> str:
    return urllib.parse.quote(text, safe='')

def generate_audio(text: str, speaker_id: int, speed: float, output_path: str) -> dict:
    try:
        clean = clean_text(text)
        if not clean:
            return {"ok": False, "path": output_path, "error": "empty after cleaning"}

        encoded_text = url_encode_text(clean)
        query_url = f"{BASE_URL}/audio_query?text={encoded_text}&speaker={speaker_id}"

        req = urllib.request.Request(query_url, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        with urllib.request.urlopen(req, timeout=20) as resp:
            query = json.loads(resp.read())

        query["speedScale"] = speed

        synth_url = f"{BASE_URL}/synthesis?speaker={speaker_id}"
        body = json.dumps(query).encode("utf-8")
        req2 = urllib.request.Request(synth_url, data=body, method="POST")
        req2.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req2, timeout=20) as resp2:
            audio_data = resp2.read()

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(audio_data)

        return {"ok": True, "path": output_path}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")[:100]
        return {"ok": False, "path": output_path, "error": f"HTTP {e.code}: {err_body}"}
    except Exception as e:
        return {"ok": False, "path": output_path, "error": str(e)[:80]}

def generate_audio_task(args):
    return generate_audio(*args)

def main():
    parser = argparse.ArgumentParser(description="Generate VOICEVOX audio for N5/N1/N2")
    parser.add_argument("--level", required=True, choices=["n5", "n1", "n2"], help="JLPT level")
    parser.add_argument("--voice", required=True, help="Voice: f (female), m (male), both")
    parser.add_argument("--resume", action="store_true", help="Skip already-existing files")
    args = parser.parse_args()

    base = Path(__file__).parent

    # Data files
    data_files = {
        "n5": base / "n5-v2-data.json",
        "n1": base / "n1-data.json",
        "n2": base / "n2-data.json",
    }
    data_path = data_files[args.level]
    if not data_path.exists():
        print(f"ERROR: {data_path} not found")
        sys.exit(1)

    raw = json.loads(data_path.read_text())
    data = raw["sentences"] if isinstance(raw, dict) else raw

    voices = ["f", "m"] if args.voice == "both" else [args.voice]

    speaker_name = {3: "ずんだもん(f)", 11: "玄野武宏(m)"}

    # Check API
    try:
        with urllib.request.urlopen(f"{BASE_URL}/version", timeout=5) as r:
            version = r.read().decode()
        print(f"VOICEVOX API OK: v{version}")
    except Exception as e:
        print(f"ERROR: Cannot connect to VOICEVOX at {BASE_URL}: {e}")
        sys.exit(1)

    for voice in voices:
        speaker_id = SPEAKERS[voice]
        audio_dir = base / "site" / "audio" / args.level / voice
        audio_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n=== {args.level.upper()} {speaker_name[speaker_id]} → {audio_dir} ===")
        print(f"Total sentences: {len(data)}")

        tasks = []
        for d in data:
            if not d.get("japanese"):
                continue
            idx = str(d["id"])
            out_path = str(audio_dir / f"{idx}.mp3")

            if args.resume and Path(out_path).exists():
                continue

            tasks.append((
                d["japanese"],
                speaker_id,
                SPEED_SCALE,
                out_path,
            ))

        if not tasks:
            print(f"All files already exist (or no sentences found).")
            continue

        print(f"Generating {len(tasks)} audio files...")

        ok, fail = 0, 0
        with ThreadPoolExecutor(max_workers=CONCURRENT) as executor:
            results = list(executor.map(generate_audio_task, tasks))

        for r in results:
            if r["ok"]:
                ok += 1
            else:
                fail += 1
                print(f"  FAIL [{Path(r['path']).name}] {r['error']}", flush=True)

        print(f"Done: {ok} ok, {fail} failed")

    print("\n=== All done ===")

if __name__ == "__main__":
    main()
