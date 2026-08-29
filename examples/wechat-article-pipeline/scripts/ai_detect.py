import re, sys, os

STRUCTURE_WORDS = [r'首先', r'其次', r'最后', r'第一', r'第二', r'第三', r'首先来说', r'首先需要', r'接下来', r'然后']
AI_CLICHES = [r'值得一提的是', r'值得注意的是', r'需要指出的是', r'不可忽视的是', r'不容忽视的是', r'不可否认', r'众所周知', r'毋庸置疑', r'显而易见', r'在当今', r'在当下', r'在这个信息爆炸的时代', r'在数字化转型的浪潮中', r'在人工智能飞速发展的今天', r'随着科技的不断发展', r'随着AI技术的不断进步']
ADJECTIVE_STACKING = [r'显著提升', r'显著提高', r'显著增强', r'极大提升', r'极大提高', r'极大增强', r'有效促进', r'有效提升', r'有效提高', r'深刻影响', r'深远影响', r'充分发挥', r'充分利用', r'完美解决', r'完美契合', r'强大的', r'强大的功能']
CONNECTIVES = [r'此外', r'同时', r'因此', r'然而', r'但是', r'另外', r'而且', r'并且', r'况且', r'总而言之', r'综上所述']
END_PATTERNS = [r'相信.*一定会', r'让我们.*一起', r'总之，.*重要', r'综上所述', r'在未来的发展中', r'相信在不久的将来']
ANTITHESIS_PATTERN = r'(不仅能|不但能|既).{5,30}，.{5,30}(还能|而且|更能)'

def find_matches(text, patterns):
    matches = []
    for pattern in patterns:
        for m in re.finditer(pattern, text):
            matches.append({'pattern': pattern, 'match': m.group(), 'position': m.start()})
    return matches

def estimate_paragraph_uniformity(text):
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    lengths = [len(p) for p in paragraphs if len(p) > 20]
    if len(lengths) < 3:
        return 0
    avg = sum(lengths) / len(lengths)
    std_dev = (sum((l - avg) ** 2 for l in lengths) / len(lengths)) ** 0.5
    ratio = std_dev / avg if avg > 0 else 0
    if ratio < 0.3: return 0.8
    elif ratio < 0.5: return 0.4
    elif ratio < 0.7: return 0.2
    return 0

def estimate_first_person_ratio(text):
    fp = len(re.findall(r'我[^们]|我自己|我个人', text))
    tp = len(re.findall(r'他[^们]|她[^们]|它[^们]|用户|开发者', text))
    total = fp + tp
    if total == 0: return 0.5
    ratio = fp / total
    if ratio < 0.05: return 0.7
    elif ratio < 0.15: return 0.3
    elif ratio < 0.6: return 0.0
    return 0.1

def analyze(text, verbose=True):
    total, max_penalty, issues = 0, 110, []

    s = find_matches(text, STRUCTURE_WORDS)
    sc = min(len(s) * 5, 20)
    total += sc
    if verbose and s: issues.append(f"[结构] {len(s)}处")

    c = find_matches(text, AI_CLICHES)
    cc = min(len(c) * 10, 30)
    total += cc
    if verbose and c: issues.append(f"[套话] {len(c)}处")

    a = find_matches(text, ADJECTIVE_STACKING)
    ac = min(len(a) * 5, 20)
    total += ac
    if verbose and a: issues.append(f"[形容词] {len(a)}处")

    conn = find_matches(text, CONNECTIVES)
    expected = (len(text) / 500) * 3
    conn_p = max(0, (len(conn) - expected) * 3)
    conn_s = min(conn_p, 15)
    total += conn_s

    total += estimate_paragraph_uniformity(text) * 10
    total += estimate_first_person_ratio(text) * 5

    at = find_matches(text, [ANTITHESIS_PATTERN])
    total += min(len(at) * 3, 5)

    end = find_matches(text[-500:], END_PATTERNS) if len(text) > 500 else []
    total += min(len(end) * 3, 5)

    pct = round((total / max_penalty) * 100)
    grade = 'A ✅' if pct <= 20 else 'B ⚠️' if pct <= 40 else 'C ❌' if pct <= 60 else 'D 🚫'
    return {'concentration': pct, 'grade': grade, 'issues': issues}

if __name__ == '__main__':
    text = open(sys.argv[1]).read() if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]) else sys.argv[2] if len(sys.argv) > 2 else ''
    r = analyze(text)
    print(f"AI浓度: {r['concentration']}% | {r['grade']}")
    for i in r['issues']: print(f"  {i}")
