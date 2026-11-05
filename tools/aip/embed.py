# Write the rebuilt PLD / PCD / CHX and the AIRAC dates back into the app's HTML.
import json, os, re, datetime
p = os.environ['HTML']; W = os.environ['WORK']; h = open(p, encoding='utf-8').read()
def put(name, txt):
    global h
    i = h.index('const ' + name + '=') + len(name) + 7
    o, e = json.JSONDecoder().raw_decode(h[i:]); h = h[:i] + txt + h[i + e:]
put('PLD', open(os.path.join(W, 'pl_compact.json')).read())
put('PCD', open(os.path.join(W, 'pc_compact.json')).read())
if os.path.exists(os.path.join(W, 'charts_idx.json')): put('CHX', open(os.path.join(W, 'charts_idx.json')).read())
eff = os.environ.get('AIRAC_EFF')
if eff:
    nxt = (datetime.date.fromisoformat(eff) + datetime.timedelta(days=28)).isoformat()
    h = re.sub(r"const AIRAC_EFF='[\d-]+', AIRAC_NEXT='[\d-]+';", f"const AIRAC_EFF='{eff}', AIRAC_NEXT='{nxt}';", h)
open(p, 'w', encoding='utf-8').write(h); print('embedded', eff or '')
