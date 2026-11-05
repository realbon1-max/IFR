# Write the rebuilt PLD / PCD / CHX and the AIRAC dates back into the app's HTML.
import json, os, re, datetime
p = os.environ['HTML']; W = os.environ['WORK']; h = open(p, encoding='utf-8').read()
def put(name, txt):
    global h
    i = h.index('const ' + name + '=') + len(name) + 7
    o, e = json.JSONDecoder().raw_decode(h[i:]); h = h[:i] + txt + h[i + e:]
put('PLD', open(os.path.join(W, 'pl_compact.json')).read())
# keep coordinates added by later steps (radial/DME points from conventional approaches) that the coding tables do not produce
pc = json.load(open(os.path.join(W, 'pc_compact.json'))); old = json.load(open(os.path.join(W, 'pcd_old.json'))) if os.path.exists(os.path.join(W, 'pcd_old.json')) else {}
for a, d in old.items():
    for f, q in d.items():
        if f not in pc.get(a, {}) and re.match(r'^([A-Z]{2,3}\d{6}|[A-Z]{3}\d{3}/[A-Z]{3}\d{3})$', f): pc.setdefault(a, {})[f] = q
json.dump(pc, open(os.path.join(W, 'pc_compact.json'), 'w'), separators=(',', ':'))
put('PCD', json.dumps(pc, separators=(',', ':')))
if os.path.exists(os.path.join(W, 'charts_idx.json')): put('CHX', open(os.path.join(W, 'charts_idx.json')).read())
eff = os.environ.get('AIRAC_EFF')
if eff:
    nxt = (datetime.date.fromisoformat(eff) + datetime.timedelta(days=28)).isoformat()
    h = re.sub(r"const AIRAC_EFF='[\d-]+', AIRAC_NEXT='[\d-]+';", f"const AIRAC_EFF='{eff}', AIRAC_NEXT='{nxt}';", h)
open(p, 'w', encoding='utf-8').write(h); print('embedded', eff or '')
