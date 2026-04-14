import requests, json, time, random, re

API = 'https://api.siliconflow.com/v1/chat/completions'
KEY = 'sk-ndeyxbhhteivzpwlecvyolnffqxngklhxpbctvxoznpuczbz'
MODEL = 'Qwen/Qwen2.5-7B-Instruct'

HIRA_ROMA = {
    'あ':'a','い':'i','う':'u','え':'e','お':'o',
    'か':'ka','き':'ki','く':'ku','け':'ke','こ':'ko',
    'さ':'sa','し':'shi','す':'su','せ':'se','そ':'so',
    'た':'ta','ち':'chi','つ':'tsu','て':'te','と':'to',
    'な':'na','に':'ni','ぬ':'nu','ね':'ne','の':'no',
    'は':'ha','ひ':'hi','ふ':'fu','へ':'he','ほ':'ho',
    'ま':'ma','み':'mi','む':'mu','め':'me','も':'mo',
    'や':'ya','ゆ':'yu','よ':'yo',
    'ら':'ra','り':'ri','る':'ru','れ':'re','ろ':'ro',
    'わ':'wa','を':'wo','ん':'n',
    'が':'ga','ぎ':'gi','ぐ':'gu','げ':'ge','ご':'go',
    'ざ':'za','じ':'ji','ず':'zu','ぜ':'ze','ぞ':'zo',
    'だ':'da','ぢ':'di','づ':'du','で':'de','ど':'do',
    'ば':'ba','び':'bi','ぶ':'bu','べ':'be','ぼ':'bo',
    'ぱ':'pa','ぴ':'pi','ぷ':'pu','ぺ':'pe','ぽ':'po',
    'きゃ':'kya','きゅ':'kyu','きょ':'kyo',
    'しゃ':'sha','しゅ':'shu','しょ':'sho',
    'ちゃ':'cha','ちゅ':'chu','ちょ':'cho',
    'にゃ':'nya','にゅ':'nyu','にょ':'nyo',
    'ひゃ':'hya','ひゅ':'hyu','ひょ':'hyo',
    'みゃ':'mya','みゅ':'myu','みょ':'myo',
    'りゃ':'rya','りゅ':'ryu','りょ':'ryo',
    'うぃ':'wi','うぇ':'we','いぇ':'ye',
    'ぁ':'a','ぃ':'i','ぅ':'u','ぇ':'e','ぉ':'o',
    'っ':'xtu','ゃ':'ya','ゅ':'yu','ょ':'yo',
    'ー':'-','・':''
}

def h2r(h):
    r, i = '', 0
    while i < len(h):
        m = False
        for l in [3,2,1]:
            if i+l <= len(h) and h[i:i+l] in HIRA_ROMA:
                r += HIRA_ROMA[h[i:i+l]]; i += l; m = True; break
        if not m: i += 1
    return r

CATS = ['日常生活', '仕事', '学校', '旅行', '健康', '天気', '映画', '音楽', '料理', 'スポーツ', 'ゲーム', 'ファッション', '経済', '政治', '文化']
GRM = ['〜つつある', '〜ない限り', '〜そばから', '〜が早いか', '〜やいなや', '〜た途端', '〜わけがない', '〜べき', '〜ごとき', '〜ごとく', '〜めながら', '〜にもかかわらず']

def gen_one():
    cat = random.choice(CATS)
    gr = random.choice(GRM)
    prompt = f'''Generate 1 N1 Japanese sentence. Output ONLY a JSON object.

Grammar: {gr}, Category: {cat}

Format:
{{"id":1,"character":"{cat}","source":"N1日本語","category":"{cat}","tense":"Present","japanese":"日本語の句子15-25字","explanation":[{{"word":"單字","mean":"意思","pos":"詞性","note":""}},{{"word":"整句","mean":"完整翻譯","pos":"句子","note":"情境"}}]}}

JSON:'''
    try:
        r = requests.post(API, headers={'Authorization':f'Bearer {KEY}','Content-Type':'application/json'},
            json={'model':MODEL,'messages':[{'role':'user','content':prompt}],'max_tokens':200,'temperature':0.8}, timeout=15)
        text = r.json()['choices'][0]['message']['content'].strip()
        start = text.find('{')
        end = text.rfind('}') + 1
        if start < 0: return None
        raw = text[start:end]
        raw = re.sub(r',\s*}', '}', raw)
        raw = re.sub(r',\s*]', ']', raw)
        return json.loads(raw)
    except:
        return None

def get_furigana(sentence):
    prompt = f'''For this Japanese sentence, output ONLY a JSON array of [kanji, hiragana, romaji] per character. Each character = 1 entry. No text.

Sentence: {sentence}
Output:'''
    try:
        r = requests.post(API, headers={'Authorization':f'Bearer {KEY}','Content-Type':'application/json'},
            json={'model':MODEL,'messages':[{'role':'user','content':prompt}],'max_tokens':300,'temperature':0.2}, timeout=15)
        text = r.json()['choices'][0]['message']['content'].strip()
        start = text.find('[')
        end = text.rfind(']') + 1
        if start < 0: return None
        raw = text[start:end]
        raw = re.sub(r',\s*}', '}', raw)
        raw = re.sub(r',\s*]', ']', raw)
        seq = json.loads(raw)
        result = []
        for entry in seq:
            if isinstance(entry, list) and len(entry) >= 2:
                kanji = entry[0]
                hira = entry[1]
                roma = entry[2] if len(entry) >= 3 and entry[2] else h2r(hira)
                result.append([kanji, hira, roma])
        return result
    except:
        return None

# Load existing
existing_jp = set()
try:
    with open('n1-data.json') as f:
        d = json.load(f)
    sentences = d['sentences']
    print(f'Loaded {len(sentences)} existing')
except:
    sentences = []

done_jp = set(s.get('japanese','') for s in sentences)
start_id = max((s.get('id',0) for s in sentences), default=0) + 1
count = len(sentences)
print(f'Target: 200 sentences, starting id={start_id}')

PUNCT = re.compile(r'[。、？？　 ]')

for i in range(300):
    tries = 0
    while tries < 5:
        item = gen_one()
        if not item:
            tries += 1
            time.sleep(1)
            continue
        jp = item.get('japanese','')
        if not jp or jp in done_jp:
            tries += 1
            continue
        
        seq = get_furigana(jp)
        if not seq or len(seq) < 5:
            tries += 1
            time.sleep(1)
            continue
        
        j_clean = PUNCT.sub('', jp)
        s_clean = PUNCT.sub('', ''.join([e[0] for e in seq]))
        if j_clean != s_clean:
            tries += 1
            time.sleep(1)
            continue
        
        for e in seq:
            if len(e) < 3 or not e[2]:
                e.append(h2r(e[1]))
        
        item['id'] = start_id
        item['sequence'] = seq
        sentences.append(item)
        done_jp.add(jp)
        start_id += 1
        count += 1
        break
    
    if count % 20 == 0:
        with open('n1-data.json', 'w') as f:
            json.dump({'sentences': sentences}, f, ensure_ascii=False, indent=2)
        print(f'[{count}] saved')
    time.sleep(0.3)

with open('n1-data.json', 'w') as f:
    json.dump({'sentences': sentences}, f, ensure_ascii=False, indent=2)
print(f'FINAL: {len(sentences)} sentences')
