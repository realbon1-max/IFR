# Manual corrections applied after each AIP rebuild (idempotent).
# RJSA: one chart carries two SIDs (IWAKI SEVEN p1 / AOMORI REVERSAL THREE p2) -> split into two procedures.
import json, os, math
p = os.environ['HTML']; h = open(p, encoding='utf-8').read()
def get(name):
    i = h.index('const ' + name + '=') + len(name) + 7
    o, e = json.JSONDecoder().raw_decode(h[i:]); return o, i, i + e
def put(name, obj):
    global h
    o, i, j = get(name); h = h[:i] + json.dumps(obj, ensure_ascii=False, separators=(',', ':')) + h[j:]
def dest(p, brg, nm):
    R = math.pi / 180; d = nm / 3440.065; b = brg * R; la = p[0] * R; lo = p[1] * R
    la2 = math.asin(math.sin(la) * math.cos(d) + math.cos(la) * math.sin(d) * math.cos(b))
    lo2 = lo + math.atan2(math.sin(b) * math.sin(d) * math.cos(la), math.cos(d) - math.sin(la) * math.sin(la2))
    return [round(la2 / R, 5), round(lo2 / R, 5)]
OLD = 'IWAKI  AOMORI REVERSAL'
nav, _, _ = get('NAV'); F = nav['F']
mre, hwe, gonou = F['MRE'][:2], F['HWE'][:2], F['GONOU'][:2]
if 'MRE331008' not in F: F['MRE331008'] = dest(mre, 331 - 9, 8.0) + [4]
if 'HWE208063' not in F:
    # along the HWE R208 track that ends at GONOU (D85.9 HWE)
    lat1, lon1 = math.radians(hwe[0]), math.radians(hwe[1]); lat2, lon2 = math.radians(gonou[0]), math.radians(gonou[1])
    brg = (math.degrees(math.atan2(math.sin(lon2 - lon1) * math.cos(lat2), math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(lon2 - lon1))) + 360) % 360
    F['HWE208063'] = dest(hwe, brg, 63.0) + [4]
put('NAV', nav)
db, _, _ = get('DB'); A = db['RJSA']
if any(s[0] == OLD for s in A['sid']):
    k = next(i for i, s in enumerate(A['sid']) if s[0] == OLD)
    iw = ['IWAKI', 0, [
        [['06'], ['MRE331008', 'MRE331012', 'HWE208063', 'GONOU'], 1100, None, 'L', 0, None, 'IWAKI SEVEN DEPARTURE', ['L', None, 'L', None]],
        [['24'], ['GONOU'], 1200, None, None, 0, None, 'IWAKI SEVEN DEPARTURE', [None]],
        [[], ['GONOU', 'UWE'], None, None, None, 1, None, 'YUWA TRANSITION'],
        [[], ['GONOU', 'NYUDO'], None, None, None, 1, None, 'NYUDO TRANSITION']],
        ['IWAKI SEVEN DEPARTURE'], {'MRE331008': ['+', 3600, None], 'HWE208063': ['+', 7000, None], 'GONOU': ['+', 9000, None], 'NYUDO': ['+', 21000, None]}]
    ar = ['AOMORI REVERSAL', 0, [
        [['06'], ['MRE331008', 'MRE331010', 'MRE'], 1100, None, 'L', 0, None, 'AOMORI REVERSAL THREE DEPARTURE', ['L', None, 'L']],
        [['24'], ['MRE331008', 'MRE331010', 'MRE'], 1200, None, 'R', 0, None, 'AOMORI REVERSAL THREE DEPARTURE', ['R', None, 'L']]],
        ['AOMORI REVERSAL THREE DEPARTURE'], {'MRE331008': ['+', 3600, None], 'MRE': ['+', 6500, None]}]
    A['sid'][k:k + 1] = [iw, ar]
    put('DB', db)
chx, _, _ = get('CHX')
L = chx.get('RJSA', [])
for i, c in enumerate(L):
    if c[0] == 'SID' and c[1] == OLD and len(c[2]) >= 2:
        L[i:i + 1] = [['SID', 'IWAKI', [c[2][0]]], ['SID', 'AOMORI REVERSAL', c[2][1:]]]; put('CHX', chx); break
pld, _, _ = get('PLD')
L = pld.get('RJSA', [])
for i, c in enumerate(L):
    if c[0] == 'SID' and c[1] == OLD:
        txt = c[3] if len(c) > 3 else []
        cut = next((j for j, t in enumerate(txt) if 'HDG 286' in t), len(txt))
        a = list(c); b = list(c); a[1] = 'IWAKI'; b[1] = 'AOMORI REVERSAL'
        if len(c) > 3: a[3] = txt[:cut]; b[3] = txt[cut:]
        L[i:i + 1] = [a, b]; put('PLD', pld); break
open(p, 'w', encoding='utf-8').write(h); print('fixups ok')
