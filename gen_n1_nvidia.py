#!/usr/bin/env python3
"""
gen_n1_nvidia.py - 用 NVIDIA API 生成 N1 日語學習句子
完全對齊 N2 格式：逐字拆解 + 完整說明
Usage: python3 gen_n1_nvidia.py [--resume] [--target 500]
"""
import urllib.request, json, time, re, sys, os, random

API_KEY = "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"
MODEL = "meta/llama-3.1-405b-instruct"
URL = "https://integrate.api.nvidia.com/v1/chat/completions"

from pykakasi import kakasi

OUT_FILE = os.path.join(os.path.dirname(__file__), "n1-data.json")
PROGRESS_FILE = os.path.join(os.path.dirname(__file__), ".n1-progress")
BATCH_SIZE = 8
TARGET = 1000

CATEGORIES = [
    "日常生活", "仕事", "学校", "旅行", "健康", "天気",
    "映画", "音楽", "料理", "スポーツ", "ゲーム", "ペット",
    "勉強", "会議", "ファッション", "経済", "政治", "科技",
    "文化", "社会"
]

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

def call_api(prompt, max_tokens=3000):
    data = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.9
    }
    req = urllib.request.Request(URL, data=json.dumps(data).encode(),
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return json.load(resp)['choices'][0]['message']['content']
    except Exception as e:
        print(f"API 錯誤: {e}")
        return None

def get_sequence_with_reading(text):
    """逐字取得讀音"""
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

def get_sequence_fallback(text):
    result = []
    for c in text:
        if c in '、。，！？…～「」『』（）':
            result.append([c, c, c])
        elif '\u3040' <= c <= '\u309f':
            result.append([c, c, c])
        elif '\u30a0' <= c <= '\u30ff':
            result.append([c, c, c])
        elif '\u4e00' <= c <= '\u9fff':
            result.append([c, c, c])
        else:
            result.append([c, c, c])
    return result

def generate_batch(cats, batch_num):
    """用 LLM 生成一批 N1 句子，每句要有逐字說明"""
    cats_str = "、".join(cats)
    grammars = random.sample(N1_GRAMMAR, 4)
    grammar_list = "\n".join([f'- {g[0]}：{g[1]}（{g[2]}）' for g in grammars])
    
    prompt = f'''生成{BATCH_SIZE}個日語N1句子。全部日語，不摻英文。直接輸出JSON。

語法要求（每句用其中一個）：
{grammar_list}

格式（每個欄位都必須填寫，不能留空）：
{{
  "sentences": [
    {{
      "japanese": "完整日語句子（25-50字符）",
      "grammar": "使用的N1語法名稱",
      "grammar_mean": "這個語法的中文意思",
      "word_breakdown": [
        {{"word": "單字1", "mean": "翻譯", "pos": "詞性", "note": "說明"}},
        {{"word": "單字2", "mean": "翻譯", "pos": "詞性", "note": "說明"}}
      ],
      "full_mean": "整句完整中文翻譯",
      "context": "使用情境說明"
    }}
  ]
}}

注意：
- word_breakdown 的每個 entry 要對應句子中的實際詞語或重要單字
- word_breakdown 最後一筆必須是：{{"word": "整句意思", "mean": "完整翻譯", "pos": "句子", "note": "情境"}}
- 不要只拆分一個字，要拆分有意義的詞語

主题：{cats_str}

現在生成：'''

    result = call_api(prompt)
    if not result:
        return []
    
    result = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', result)
    
    start = result.find('{')
    end = result.rfind('}') + 1
    if start < 0 or end <= start:
        print(f"無法找到 JSON")
        return []
    
    try:
        data = json.loads(result[start:end])
        return data.get('sentences', [])
    except Exception as e:
        print(f"JSON 解析失敗: {e}")
        print(f"內容: {result[start:start+500]}")
        return []

def check_garbled(text):
    if re.search(r'[А-я\u0600-\u06FF]', text):
        return True
    en_chars = len(re.findall(r'[a-zA-Z]', text))
    total = len(re.sub(r'[\s\u0000-\u001F\u007F-\u009F]', '', text))
    if total > 0 and en_chars / total > 0.15:
        return True
    return False

def load_existing():
    if os.path.exists(OUT_FILE):
        with open(OUT_FILE) as f:
            return json.load(f).get('sentences', [])
    return []

def save_data(sentences):
    with open(OUT_FILE, 'w') as f:
        json.dump({"sentences": sentences}, f, ensure_ascii=False, indent=2)

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return int(f.read().strip())
    return 0

def save_progress(n):
    with open(PROGRESS_FILE, 'w') as f:
        f.write(str(n))

def main():
    sentences = load_existing()
    start_progress = load_progress()
    
    print(f"N1 句子生成器（NVIDIA API + N2格式 + 逐字說明）")
    print(f"現有: {len(sentences)} 句 | 目標: {TARGET} 句")
    
    if start_progress > 0:
        print(f"從 #{start_progress} 繼續...")
    
    batch_num = (len(sentences) // BATCH_SIZE) + 1
    
    while len(sentences) < TARGET:
        cats = random.sample(CATEGORIES, min(5, len(CATEGORIES)))
        
        print(f"\n第 {batch_num} 批（目前 {len(sentences)}/{TARGET}）...")
        batch = generate_batch(cats, batch_num)
        
        if not batch:
            print("  重試中（等3秒）...")
            time.sleep(3)
            continue
        
        valid_count = 0
        for item in batch:
            japanese = item.get('japanese', '')
            
            if not japanese or len(japanese) < 10:
                continue
            if check_garbled(japanese):
                continue
            
            grammar = item.get('grammar', '')
            grammar_mean = item.get('grammar_mean', '')
            word_breakdown = item.get('word_breakdown', [])
            full_mean = item.get('full_mean', '')
            context = item.get('context', '')
            
            # pykakasi 取得讀音
            try:
                seq = get_sequence_with_reading(japanese)
            except:
                seq = get_sequence_fallback(japanese)
            
            # 建立 explanation（N2格式）
            explanation = []
            
            # 加入單字說明（來自 LLM 的 word_breakdown）
            for wb in word_breakdown:
                explanation.append({
                    "word": wb.get('word', ''),
                    "mean": wb.get('mean', ''),
                    "pos": wb.get('pos', ''),
                    "note": wb.get('note', '')
                })
            
            # 確保有整句意思
            if not any(e.get('pos') == '句子' for e in explanation):
                explanation.append({
                    "word": "",
                    "mean": full_mean or japanese,
                    "pos": "句子",
                    "note": context or f"情境：{grammar_mean}"
                })
            
            # 找出第一個「單字」當重點詞（取第一個非句子的 entry）
            first_word = next((e.get('word', '') for e in explanation if e.get('pos') != '句子' and e.get('word', '')), grammar)
            first_mean = next((e.get('mean', '') for e in explanation if e.get('pos') != '句子' and e.get('mean', '')), grammar_mean)
            
            sentence = {
                "id": len(sentences) + 1,
                "character": first_word or grammar,
                "source": "N1日本語",
                "category": cats[0] if cats else "日常生活",
                "tense": "Present",
                "japanese": japanese,
                "sequence": seq,
                "explanation": explanation,
                "word": first_word or grammar,
                "mean": first_mean or grammar_mean
            }
            
            sentences.append(sentence)
            valid_count += 1
        
        save_data(sentences)
        save_progress(len(sentences))
        print(f"  ✅ 本批 {valid_count}/{len(batch)} 句，累計 {len(sentences)} 句")
        
        batch_num += 1
        time.sleep(1)
    
    save_data(sentences)
    print(f"\n🎉 完成！共 {len(sentences)} 句 N1 句子已保存")

if __name__ == '__main__':
    main()
