# One-off: fetch outlines of Japan's main lakes from OpenStreetMap (Overpass API), simplify them and write lakes.js
# (window.JPLAKES = [{n: name, c: [[ [lon,lat], ... ]]}]). Data © OpenStreetMap contributors (ODbL).
import json, math, sys, time, urllib.request, urllib.parse
NAMES = """琵琶湖 猪苗代湖 田沢湖 十和田湖 霞ヶ浦 西浦 北浦 浜名湖 宍道湖 中海 諏訪湖 洞爺湖 支笏湖 屈斜路湖 阿寒湖 摩周湖 サロマ湖 能取湖 風蓮湖 網走湖 濤沸湖
小川原湖 十三湖 八郎湖 中禅寺湖 河口湖 山中湖 本栖湖 西湖 精進湖 芦ノ湖 印旛沼 手賀沼 野尻湖 木崎湖 青木湖 奥只見湖 田子倉湖 池田湖 湖山池 東郷池 北潟湖 三方湖 水月湖 久美浜湾 加茂湖 福島潟 鳥屋野潟 檜原湖 秋元湖 小野川湖 沼沢湖 宇曽利山湖 大沼 クッチャロ湖 朱鞠内湖 金山湖 かなやま湖 大雪湖 シューパロ湖 早明浦ダム 黒部湖 御母衣湖 奈良井ダム 丹沢湖 相模湖 津久井湖 奥多摩湖 榛名湖 赤城大沼 丸沼 菅沼 湯ノ湖 佐鳴湖 一碧湖""".split()
RX = '^(' + '|'.join(NAMES) + ')$'
Q = f'[out:json][timeout:240][bbox:24,122,46,146];(way["natural"="water"]["name"~"{RX}"];relation["natural"="water"]["name"~"{RX}"];way["water"="reservoir"]["name"~"{RX}"];relation["water"="reservoir"]["name"~"{RX}"];);out geom;'
def fetch():
    for url in ['https://overpass-api.de/api/interpreter', 'https://overpass.kumi.systems/api/interpreter', 'https://maps.mail.ru/osm/tools/overpass/api/interpreter']:
        try:
            req = urllib.request.Request(url, data=urllib.parse.urlencode({'data': Q}).encode(), headers={'User-Agent': 'ifr-briefing-lakes/1.0'})
            with urllib.request.urlopen(req, timeout=240) as r:
                return json.loads(r.read())
        except Exception as e:
            print(url, e, file=sys.stderr); time.sleep(5)
    sys.exit('overpass failed')
def stitch(ways):
    rings, segs = [], [w[:] for w in ways if len(w) > 1]
    while segs:
        cur = segs.pop(0)
        changed = True
        while changed and cur[0] != cur[-1]:
            changed = False
            for i, s in enumerate(segs):
                if s[0] == cur[-1]: cur += s[1:]
                elif s[-1] == cur[-1]: cur += s[::-1][1:]
                elif s[-1] == cur[0]: cur = s + cur[1:]
                elif s[0] == cur[0]: cur = s[::-1] + cur[1:]
                else: continue
                segs.pop(i); changed = True; break
        if len(cur) >= 4: rings.append(cur)
    return rings
def dp(pts, eps):
    if len(pts) < 3: return pts
    a, b = pts[0], pts[-1]; dx, dy = b[0]-a[0], b[1]-a[1]; L = math.hypot(dx, dy); mi, md = 0, -1
    for i in range(1, len(pts)-1):
        p = pts[i]; d = abs(dy*p[0]-dx*p[1]+b[0]*a[1]-b[1]*a[0])/L if L else math.hypot(p[0]-a[0], p[1]-a[1])
        if d > md: md, mi = d, i
    return dp(pts[:mi+1], eps)[:-1] + dp(pts[mi:], eps) if md > eps else [a, b]
def area(r): return abs(sum(r[i][0]*r[i-1][1]-r[i-1][0]*r[i][1] for i in range(len(r))))/2
sys.setrecursionlimit(100000)
d = fetch(); by = {}
open('lakes_debug.txt','w').write(f"elements={len(d.get('elements',[]))} remark={d.get('remark')}\n")
for e in d.get('elements', []):
    n = e.get('tags', {}).get('name')
    if e['type'] == 'way' and 'geometry' in e:
        rings = [[(g['lon'], g['lat']) for g in e['geometry']]]
    elif e['type'] == 'relation':
        rings = stitch([[(g['lon'], g['lat']) for g in m.get('geometry', [])] for m in e.get('members', []) if m.get('type') == 'way' and m.get('role') in ('outer', '')])
    else: continue
    for r in rings:
        if r[0] != r[-1] or area(r) < 2e-5: continue
        h = len(r)//2; s = dp(r[:h+1], 0.002)[:-1] + dp(r[h:], 0.002)
        if len(s) >= 4: by.setdefault(n, []).append([[round(x, 4), round(y, 4)] for x, y in s])
out = [{'n': n, 'c': rs} for n, rs in by.items()]
open(sys.argv[1] if len(sys.argv) > 1 else 'lakes.js', 'w').write('window.JPLAKES=' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';')
print(len(out), 'lakes:', ' '.join(sorted(by)))
open('lakes_debug.txt','a').write(f"{len(out)} lakes: {' '.join(sorted(by))}\n")
