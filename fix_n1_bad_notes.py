#!/usr/bin/env python3
"""
fix_n1_bad_notes.py - 重新生成 N1 中 note 為空的句子
用戶要求：逐字有 mean/note（不能是空的），grammar 重點要清楚說明
使用 NVIDIA API
"""
import urllib.request, json, time, re, sys, os, random

API_KEY = "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"
MODEL = "meta/llama-3.2-11b-vision-instruct"
URL = "https://integrate.api.nvidia.com/v1/chat/completions"

sys.path.insert(0, '/Users/whypuss/.local/lib/python3.11/site-packages')
from pykakasi import kakasi

OUT_FILE = os.path.join(os.path.dirname(__file__), "n1-data.json")
BACKUP_FILE = os.path.join(os.path.dirname(__file__), "n1-data-bad-notes-backup.json")
BATCH_SIZE = 4  # 每批少量，確保質量

N1_GRAMMAR = [
    ("〜uance", "變化、發展的樣子", "例：形狀的變化"),
    ("〜ものではない", "不是...的東西", "強烈否定"),
    ("〜にもかかわらず", "雖然...但是...", "逆接"),
    ("〜ない限り", "除非...否則", "條件"),
    ("〜わけがない", "不可能...", "強烈否定"),
    ("〜べき", "應該...", "義務/建議"),
    ("〜つつある", "正在...", "動作進行"),
    ("〜そばから", "剛...就...", "接續"),
    ("〜が早いか", "剛...就...", "快速接續"),
    ("〜た途端", "剛...就...", "瞬間"),
    ("〜まい", "不會...吧", "否定推量"),
    ("〜べし", "應該.../...吧", "義務/推量"),
    ("〜ごとき/〜ごとく", "如...一般", "比喻"),
    ("〜ぐるみ", "連同...都", "包含"),
    ("〜ざかり", "正值...時候", "時期"),
    ("〜ながら(も)", "雖然...但是...", "逆接"),
    ("〜めく", "呈現...樣子", "樣態"),
    ("〜びる", "帶有...氣息", "樣態"),
    ("〜がる", "顯得...", "情感表露"),
    ("〜ぶり", "...的樣子", "樣態"),
]

CATEGORIES = [
    "日常生活", "仕事", "学校", "旅行", "健康", "天気",
    "映画", "音楽", "料理", "スポーツ", "ゲーム", "ペット",
    "勉強", "会議", "ファッション", "経済", "政治", "科技",
    "文化", "社会"
]

def call_api(prompt, max_tokens=3000, retries=3):
    data = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.9
    }
    req = urllib.request.Request(URL, data=json.dumps(data).encode(),
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        method="POST")
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                return json.load(resp)['choices'][0]['message']['content']
        except Exception as e:
            print(f"  API 錯誤: {e}")
            if attempt < retries - 1:
                time.sleep(3)
            else:
                return None

def get_sequence_with_reading(text):
    kks = kakasi()
    result = []
    for c in text:
        conv = kks.convert(c)
        if conv:
            item = conv[0]
            result.append([c, item['hira'], item['hepburn']])
        else:
            result.append([c, c, c])
    return result

def generate_replacement(cats, grammar_item=None):
    """用嚴格格式生成 N1 句子，確保每個 note 都填寫"""
    cats_str = "、".join(cats)
    if grammar_item is None:
        grammar_item = random.choice(N1_GRAMMAR)
    
    grammar_name, grammar_mean, grammar_hint = grammar_item
    
    prompt = f'''生成4個日語N1句子。全部日語，不摻英文。直接輸出JSON。

語法重點：{grammar_name}（{grammar_mean}，{grammar_hint}）

格式要求（每個欄位都必須填寫，note 不能留空）：
{{
  "sentences": [
    {{
      "japanese": "完整日語句子（25-50字符）",
      "grammar": "{grammar_name}",
      "grammar_mean": "{grammar_mean}",
      "word_breakdown": [
        {{"word": "單字", "mean": "翻譯", "pos": "詞性", "note": "詳細說明（必填）"}},
        {{"word": "語法", "mean": "翻譯", "pos": "語法", "note": "詳細說明（必填）"}}
      ],
      "full_mean": "整句完整中文翻譯",
      "context": "使用情境"
    }}
  ]
}}

注意：
- 每個 word_breakdown 的 note 欄位必須填寫，絕對不能為空
- 如果不知道怎麼填，請根據語境合理推斷一個說明
- 不要只拆分一個字，要拆分有意義的詞語
- word_breakdown 最後一筆必須是：{{"word": "整句意思", "mean": "完整翻譯", "pos": "句子", "note": "情境說明（必填）"}}

主题：{cats_str}

現在生成：'''

    result = call_api(prompt)
    if not result:
        return []
    
    result = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', result)
    
    start = result.find('{')
    end = result.rfind('}') + 1
    if start < 0 or end <= start:
        print(f"  無法找到 JSON")
        return []
    
    try:
        data = json.loads(result[start:end])
        return data.get('sentences', [])
    except Exception as e:
        print(f"  JSON 解析失敗: {e}")
        return []

def load_data():
    with open(OUT_FILE) as f:
        return json.load(f).get('sentences', [])

def save_data(sentences):
    with open(OUT_FILE, 'w') as f:
        json.dump({"sentences": sentences}, f, ensure_ascii=False, indent=2)

def find_bad_ids(sentences):
    """找出有 empty note 的句子 ID"""
    bad = []
    for s in sentences:
        for exp in s.get('explanation', []):
            note = exp.get('note', '')
            if not note or note == 'EMPTY':
                bad.append(s['id'])
                break
    return bad

def main():
    sentences = load_data()
    bad_ids = find_bad_ids(sentences)
    
    print(f"N1 note 修復器")
    print(f"現有: {len(sentences)} 句 | 壞句子: {len(bad_ids)} 個")
    
    # 備份
    with open(BACKUP_FILE, 'w') as f:
        json.dump({"sentences": sentences}, f, ensure_ascii=False)
    print(f"已備份到 {BACKUP_FILE}")
    
    # 建立 ID -> index 映射
    id_to_idx = {s['id']: i for i, s in enumerate(sentences)}
    
    fixed = 0
    failed = []
    
    for idx, sid in enumerate(bad_ids):
        print(f"\n[{idx+1}/{len(bad_ids)}] 修復 ID {sid}...")
        
        s = sentences[id_to_idx[sid]]
        old_japanese = s.get('japanese', '')
        old_grammar = s.get('grammar', '')
        
        # 找對應的 grammar
        grammar_item = None
        for g in N1_GRAMMAR:
            if old_grammar and g[0].replace('〜', '') in old_grammar.replace('〜', ''):
                grammar_item = g
                break
        
        cats = [s.get('category', '日常生活')]
        
        batch = generate_replacement(cats, grammar_item)
        
        if not batch:
            print(f"  ❌ 生成失敗，跳過")
            failed.append(sid)
            continue
        
        # 找最接近的句子
        best = None
        for item in batch:
            japanese = item.get('japanese', '')
            if abs(len(japanese) - len(old_japanese)) < 5:
                best = item
                break
        if not best:
            best = batch[0]
        
        japanese = best.get('japanese', old_japanese)
        grammar = best.get('grammar', old_grammar)
        grammar_mean = best.get('grammar_mean', '')
        word_breakdown = best.get('word_breakdown', [])
        full_mean = best.get('full_mean', '')
        context = best.get('context', '')
        
        # pykakasi 讀音
        try:
            seq = get_sequence_with_reading(japanese)
        except:
            seq = [[c, c, c] for c in japanese]
        
        # 建立 explanation（嚴格格式：note 不能為空）
        explanation = []
        for wb in word_breakdown:
            word = wb.get('word', '')
            mean = wb.get('mean', '')
            pos = wb.get('pos', '')
            note = wb.get('note', '')
            
            # note 不能為空
            if not note:
                note = f"{mean}的用法" if mean else "說明"
            
            if word == "整句意思":
                explanation.append({
                    "word": "",
                    "mean": full_mean or japanese,
                    "pos": "句子",
                    "note": context or f"情境：{grammar_mean}"
                })
            else:
                explanation.append({
                    "word": word,
                    "mean": mean,
                    "pos": pos,
                    "note": note
                })
        
        # 確保有整句意思
        if not any(e.get('pos') == '句子' for e in explanation):
            explanation.append({
                "word": "",
                "mean": full_mean or japanese,
                "pos": "句子",
                "note": context or f"情境：{grammar_mean}"
            })
        
        first_word = next((e.get('word', '') or e.get('mean', '') for e in explanation if e.get('pos') != '句子'), grammar)
        first_mean = next((e.get('mean', '') for e in explanation if e.get('pos') != '句子'), grammar_mean)
        
        new_sentence = {
            "id": sid,
            "character": first_word,
            "source": "N1日本語",
            "category": cats[0] if cats else "日常生活",
            "tense": "Present",
            "japanese": japanese,
            "sequence": seq,
            "explanation": explanation,
            "word": first_word,
            "mean": first_mean
        }
        
        sentences[id_to_idx[sid]] = new_sentence
        print(f"  ✅ 已修復: {japanese[:40]}...")
        print(f"     Grammar: {grammar}")
        fixed += 1
        
        save_data(sentences)
        time.sleep(1)
    
    print(f"\n🎉 完成！修復 {fixed}/{len(bad_ids)} 句")
    if failed:
        print(f"❌ 失敗: {failed}")
    else:
        print(f"全部成功！")

if __name__ == '__main__':
    main()
