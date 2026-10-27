# Fetch the latest METAR and TAF for Japanese aerodromes from the NOAA Aviation Weather Center Data API
# (it relays the reports issued by JMA) and write a compact wx.json for the IFR briefing app.
import json, time, urllib.request, urllib.parse, sys
IDS = """RJAA RJAF RJAH RJAK RJAM RJAN RJAW RJAZ RJBB RJBD RJBE RJBK RJBT RJCA RJCB RJCC
RJCH RJCJ RJCK RJCM RJCN RJCO RJCR RJCT RJCW RJDA RJDB RJDC RJDK RJDM RJDO RJDT
RJDU RJEB RJEC RJEO RJER RJFA RJFC RJFE RJFF RJFG RJFK RJFM RJFN RJFO RJFR RJFS
RJFT RJFU RJFY RJFZ RJGG RJKA RJKB RJKI RJKN RJNA RJNF RJNG RJNH RJNK RJNO RJNS
RJNT RJNW RJNY RJOA RJOB RJOC RJOE RJOF RJOH RJOI RJOK RJOM RJOO RJOR RJOS RJOT
RJOW RJOY RJOZ RJSA RJSC RJSD RJSF RJSH RJSI RJSK RJSM RJSN RJSO RJSR RJSS RJST
RJSU RJSY RJTA RJTC RJTE RJTF RJTH RJTJ RJTK RJTL RJTO RJTQ RJTT RJTU RJTY ROAH
RODN ROIG ROKJ ROKR ROMD ROMY RORA RORE RORH RORK RORS RORT RORY ROTM ROYN""".split()
UA = {'User-Agent': 'ifr-briefing-wx/1.0 (github.com/realbon1-max/IFR)'}
def get(kind, extra=''):
    q = urllib.parse.urlencode({'ids': ','.join(IDS), 'format': 'json'}) + extra
    req = urllib.request.Request(f'https://aviationweather.gov/api/data/{kind}?{q}', headers=UA)
    for k in range(3):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                b = r.read()
                return json.loads(b) if b.strip() else []
        except Exception as e:
            print(kind, 'retry', e, file=sys.stderr); time.sleep(5 * (k + 1))
    return None
m = get('metar'); time.sleep(2); t = get('taf')
if m is None and t is None: sys.exit('no data')
out = {'t': int(time.time()), 'src': 'NOAA Aviation Weather Center（気象庁発表の METAR/TAF を中継）', 'metar': [], 'taf': []}
for x in m or []:
    out['metar'].append({'id': x.get('icaoId'), 'name': x.get('name'), 'lat': x.get('lat'), 'lon': x.get('lon'), 'elev': x.get('elev'),
                         'obs': x.get('obsTime'), 'raw': x.get('rawOb')})
for x in t or []:
    out['taf'].append({'id': x.get('icaoId'), 'name': x.get('name'), 'lat': x.get('lat'), 'lon': x.get('lon'),
                       'issue': x.get('issueTime'), 'raw': x.get('rawTAF')})
json.dump(out, open(sys.argv[1] if len(sys.argv) > 1 else 'wx.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('metar', len(out['metar']), 'taf', len(out['taf']))
