# Extract the data the parsers need (DB, NAV) and the current procedure data (PLD, PCD, CHX) from the app's HTML.
import json, os, sys
h = open(os.environ['HTML'], encoding='utf-8').read(); W = os.environ['WORK']; os.makedirs(W, exist_ok=True)
def grab(name):
    i = h.index('const ' + name + '=') + len(name) + 7
    o, e = json.JSONDecoder().raw_decode(h[i:]); return o
for name, fn in [('DB', 'db.json'), ('NAV', 'nav.json'), ('PLD', 'pld_old.json'), ('PCD', 'pcd_old.json'), ('CHX', 'chx_old.json')]:
    try: json.dump(grab(name), open(os.path.join(W, fn), 'w'), ensure_ascii=False)
    except ValueError: print('missing', name, file=sys.stderr)
print('prep ok')
