#!/usr/bin/env python3
"""Generate Hunter x Hunter Japanese learning sentences"""
import json, urllib.request, urllib.error, re, pykakasi

kks = pykakasi.kakasi()

NVAPI_KEY = "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"

def call_nvidia(prompt, max_tokens=1500):
    url = "https://integrate.api.nvidia.com/v1/chat/completions"
    data = {
        "model": "meta/llama-3.2-11b-vision-instruct",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.7
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode(),
        headers={"Authorization": f"Bearer {NVAPI_KEY}", "Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.load(resp)["choices"][0]["message"]["content"]

def to_sequence(japanese):
    """Convert Japanese text to sequence array using pykakasi"""
    result = kks.convert(japanese)
    sequence = []
    for item in result:
        original = item['orig']
        hira = item['hira']
        roma = item['roma'].lower()
        
        # Split romaji into parts (one per original char conceptually)
        # For simplicity, put full romaji if single kanji/hira, else split
        if len(original) == 1:
            roma_parts = [roma]
        else:
            # Split romaji by spaces if available, else by char count
            roma_parts = roma.split(' ')
            if len(roma_parts) != len(original):
                roma_parts = [roma]
        
        sequence.append([original, hira, ' '.join(roma_parts[:len(original)]) if roma_parts else roma])
    
    return sequence

# Hunter x Hunter sentences - 20 sentences with characters and their iconic quotes
hunter_sentences_base = [
    # Gon Freecss
    {"character": "Gon Freecss", "char_jp": "ゴン", "source": "HUNTER × HUNTER", "category": "Determination",
     "japanese": "必ずキートに会える。そう約束する。", "translation": "我一定會見到基特。這是我約定好的。"},
    {"character": "Gon Freecss", "char_jp": "ゴン", "source": "HUNTER × HUNTER", "category": "Determination",
     "japanese": "俺はハンターになる！", "translation": "我要成為獵人！"},
    {"character": "Gon Freecss", "char_jp": "ゴン", "source": "HUNTER × HUNTER", "category": "Emotion",
     "japanese": "この気持ちを忘れるものか！", "translation": "我怎麼會忘記這種感覺！"},
    
    # Killua Zoldyck
    {"character": "Killua Zoldyck", "char_jp": "キルア", "source": "HUNTER × HUNTER", "category": "Friendship",
     "japanese": "ゴンは俺の親友だ。", "translation": "Gon是我的好朋友。"},
    {"character": "Killua Zoldyck", "char_jp": "キルア", "source": "HUNTER × HUNTER", "category": "Emotion",
     "japanese": "久しぶりだな、Gon。", "translation": "好久不見了，Gon。"},
    {"character": "Killua Zoldyck", "char_jp": "キルア", "source": "HUNTER × HUNTER", "category": "Personality",
     "japanese": "俺は殺戮人形じゃない！", "translation": "我不是殺人機器！"},
    
    # Kurapika
    {"character": "Kurapika", "char_jp": "クラピカ", "source": "HUNTER × HUNTER", "category": "Vengeance",
     "japanese": " Network旅団を許さない。", "translation": "我不會饒恕幻影旅團。"},
    {"character": "Kurapika", "char_jp": "クラピカ", "source": "HUNTER × HUNTER", "category": "Identity",
     "japanese": "私はクラナチ族です。", "translation": "我是庫拉皮卡族。"},
    {"character": "Kurapika", "char_jp": "クラピカ", "source": "HUNTER × HUNTER", "category": "Determination",
     "japanese": "復讐は必ず成る。", "translation": "復仇一定會完成。"},
    
    # Leorio Paradinight
    {"character": "Leorio Paradinight", "char_jp": "レオリオ", "source": "HUNTER × HUNTER", "category": "Dream",
     "japanese": "俺は医者になる。絶対に。", "translation": "我要成為醫生。絕對要。"},
    {"character": "Leorio Paradinight", "char_jp": "レオリオ", "source": "HUNTER × HUNTER", "category": "Friendship",
     "japanese": "みんなが無事なら、それでいい。", "translation": "只要大家都平安就好。"},
    {"character": "Leorio Paradinight", "char_jp": "レオリオ", "source": "HUNTER × HUNTER", "category": "Personality",
     "japanese": "金か命か。選べ。", "translation": "要錢還是要命。選一個。"},
    
    # Hisoka Morow
    {"character": "Hisoka Morow", "char_jp": "ヒソカ", "source": "HUNTER × HUNTER", "category": "Battle",
     "japanese": "僕と戦いたい？もいいだろう。", "translation": "你想和我戰鬥嗎？也好啊。"},
    {"character": "Hisoka Morow", "char_jp": "ヒソカ", "source": "HUNTER × HUNTER", "category": "Battle",
     "japanese": "面白いのは、お前の方だ。", "translation": "有趣的是你才對。"},
    {"character": "Hisoka Morow", "char_jp": "ヒソカ", "source": "HUNTER × HUNTER", "category": "Personality",
     "japanese": "命は賭けだ。不然退け。", "translation": "生命就是一場賭注。不然就滾。"},
    
    # Chrollo Lucilfer
    {"character": "Chrollo Lucilfer", "char_jp": "クロロ", "source": "HUNTER × HUNTER", "category": "Leadership",
     "japanese": "全員、集まれ。計画を変更する。", "translation": "全員集合。我要改變計劃。"},
    {"character": "Chrollo Lucilfer", "char_jp": "クロロ", "source": "HUNTER × HUNTER", "category": "Philosophy",
     "japanese": "信用できるものは、自分だけだ。", "translation": "唯一能信任的只有自己。"},
    
    # Gon & Killua together
    {"character": "Gon & Killua", "char_jp": "ゴン＆キルア", "source": "HUNTER × HUNTER", "category": "Friendship",
     "japanese": "一緒に進めば、どこでも行ける。", "translation": "只要一起前進，哪裡都能去。"},
    {"character": "Gon & Killua", "char_jp": "ゴン＆キルア", "source": "HUNTER × HUNTER", "category": "Adventure",
     "japanese": "次の試練にようこそ。", "translation": "歡迎來到下一個試煉。"},
]

print(f"Total base sentences: {len(hunter_sentences_base)}")

# Generate sequence for each and fix any encoding issues
def fix_text(text):
    """Fix Japanese text encoding"""
    if isinstance(text, bytes):
        text = text.decode('utf-8', errors='replace')
    return text

fixed = []
for s in hunter_sentences_base:
    s2 = {}
    for k, v in s.items():
        if isinstance(v, str):
            s2[k] = fix_text(v)
        else:
            s2[k] = v
    fixed.append(s2)

hunter_sentences_base = fixed

# Print first few to check
for s in hunter_sentences_base[:3]:
    print(f"  {s['character']}: {s['japanese']}")
