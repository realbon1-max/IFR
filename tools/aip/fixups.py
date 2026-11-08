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

# Base turns read from the charts: nav, turn-initiation DME, outbound and inbound courses (MAG).
import re as _re
h = open(p, encoding='utf-8').read()
BT = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bt_chart.json')))
db, _, _ = get('DB'); ns = lambda s: _re.sub(r'\s+', '', s).upper(); n = 0
for k, v in BT.items():
    if k.startswith('_'): continue
    a, nm = k.split('|', 1)
    for q in db.get(a, {}).get('iac', []):
        if ns(q['n']) == ns(nm): q['bt'] = [v[0], v[1]]; q['btc'] = [v[2], v[3]]; n += 1
put('DB', db); open(p, 'w', encoding='utf-8').write(h); print('base turns from charts', n)

# Approaches whose fix roles are empty: take them (and coordinates) from the conventional-approach data (CVD).
h = open(p, encoding='utf-8').read()
db, _, _ = get('DB'); cvd, _, _ = get('CVD'); pcd, _, _ = get('PCD'); nav, _, _ = get('NAV'); F = nav['F']; nr = nc = 0
for a, A in db.items():
    for q in A.get('iac', []):
        V = cvd.get(a, {}).get(q['n'])
        if not V or not V[0]: continue
        for f in V[0]:
            nm, role, la, lo = f[0], f[1], f[2], f[3]
            if nm == 'MAPt' or la is None: continue
            if nm not in F and nm not in pcd.get(a, {}): pcd.setdefault(a, {})[nm] = [la, lo]; nc += 1
        R = q.get('r') or {}
        if not any(R.get(k) for k in ('IAF', 'IF', 'FAF', 'FAP')):
            R = {}
            for f in V[0]:
                if f[1] in ('IAF', 'IF', 'FAF', 'FAP') and f[0] != 'MAPt': R.setdefault(f[1], []).append(f[0])
            if R: q['r'] = R; nr += 1
            alts = q.setdefault('alts', {})
            for f in V[0]:
                if f[5] and f[0] not in alts and f[0] != 'MAPt': alts[f[0]] = f[5]
put('DB', db); put('PCD', pcd); open(p, 'w', encoding='utf-8').write(h); print('roles from CVD', nr, 'coords added', nc)

# Approach paths read from the charts (apx_chart.json): coordinates for the fixes and the drawn polyline.
import math as _m
h = open(p, encoding='utf-8').read()
APX = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'apx_chart.json')))
db, _, _ = get('DB'); pcd, _, _ = get('PCD'); nav, _, _ = get('NAV'); F = nav['F']
def _brg(a, b):
    la1, lo1, la2, lo2 = map(_m.radians, (a[0], a[1], b[0], b[1]))
    return (_m.degrees(_m.atan2(_m.sin(lo2 - lo1) * _m.cos(la2), _m.cos(la1) * _m.sin(la2) - _m.sin(la1) * _m.cos(la2) * _m.cos(lo2 - lo1))) + 360) % 360
def _dist(a, b):
    la1, lo1, la2, lo2 = map(_m.radians, (a[0], a[1], b[0], b[1]))
    return 3440.065 * 2 * _m.asin(_m.sqrt(_m.sin((la2 - la1) / 2) ** 2 + _m.cos(la1) * _m.cos(la2) * _m.sin((lo2 - lo1) / 2) ** 2))
n = 0
for k, v in APX.items():
    if k.startswith('_'): continue
    a, nm = k.split('|', 1)
    A = db.get(a)
    if not A: print('no apt', k); continue
    q = next((q for q in A['iac'] if ns(q['n']) == ns(nm)), None)
    if not q: print('no iac', k); continue
    mv = A.get('mv', -8) or -8; P = {}
    def pos(f):
        if f in P: return P[f]
        d = v['fix'].get(f)
        if d is None:
            c = F.get(f) or pcd.get(a, {}).get(f); P[f] = [c[0], c[1]] if c else None; return P[f]
        t = d[0]
        if t == 'L': r = [d[1], d[2]]
        elif t == 'R': c = F[d[1]]; r = dest([c[0], c[1]], (d[2] + mv) % 360, d[3])
        elif t == 'T':
            rw = next(x for x in A['rw'] if x['id'] == d[1]); r = dest(rw.get('t') or A['p'], (d[2] + mv) % 360, d[3])
        elif t == 'F': r = dest(pos(d[1]), (d[2] + mv) % 360, d[3])
        P[f] = r; return r
    pts = []; toks = v['path']
    for i, t in enumerate(toks):
        if t == 'THR':
            rw = next((x for x in A['rw'] if x['id'] == q.get('rw')), None); pts.append(rw.get('t') or A['p'] if rw else A['p']); continue
        if t.startswith('ARC:'):
            _, nv, d = t.split(':'); c = [F[nv][0], F[nv][1]]; p0 = pts[-1]; p1 = pos(toks[i + 1]); R = _dist(c, p0)
            b0 = _brg(c, p0); b1 = _brg(c, p1); sw = (b1 - b0) % 360 if d == 'R' else -((b0 - b1) % 360)
            for j in range(1, 24): pts.append(dest(c, (b0 + sw * j / 24) % 360, R))
            continue
        pts.append(pos(t))
    for f in v['fix']:
        if f not in F: pcd.setdefault(a, {})[f] = [round(x, 5) for x in pos(f)]
    q['cpl'] = [[round(x[0], 5), round(x[1], 5)] for x in pts]
    q['r'] = {}
    for f, r in v.get('roles', {}).items(): q['r'].setdefault(r, []).append(f)
    if v.get('fc') is not None: q['fc'] = v['fc']
    q.pop('bt', None); q.pop('btc', None); n += 1
put('DB', db); put('PCD', pcd); open(p, 'w', encoding='utf-8').write(h); print('chart paths', n)
