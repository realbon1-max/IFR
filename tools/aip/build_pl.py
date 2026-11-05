import os
import json,re,os,collections
R=json.load(open(os.environ['WORK']+'/ct_raw.json'))
DB=json.load(open(os.environ['WORK']+'/db.json'));NAV=json.load(open(os.environ['WORK']+'/nav.json'))
TXT=os.environ['AIP_TXT']+'/'
KEYW=re.compile(r'(Climb|climb|turn |Turn |direct|proceed|intercept|Cross|cross |via |hold|Hold |Expect|From |at or above|at or below|HDG|continue|Maintain|maintain|DEPARTURE|ARRIVAL|TRANSITION|MISSED APPROACH|Contact|until|track|radial)')
def desc(fn):
    try: L=[re.sub(r'\s{2,}',' ',l).strip() for l in open(TXT+fn[:-4]+'.txt',errors='ignore')]
    except: return []
    out=[];on=False
    for l in L:
        if not l: continue
        if re.match(r'^(Note|OBST|CHANGE|Civil Aviation|AIP Japan|\*\s*MUST)',l): on=False;continue
        if re.match(r'^Serial',l): on=False;continue
        low=len(re.findall(r'\b[a-z]{2,}\b',l))
        isname=re.fullmatch(r'[A-Z0-9 ]+(DEPARTURE|ARRIVAL|TRANSITION)( \(.*\))?',l) is not None
        isrwy=re.match(r'^RWY ?\d{2}[LRC]?( ?[/&,] ?\d{2}[LRC]?)* ?:',l) is not None
        ma=l.startswith('MISSED APPROACH')
        if isname or isrwy or ma: on=True;out.append(l);continue
        if on and (low>=2 or KEYW.search(l)) and len(l)>6 and not re.search(r'\d{6}\.\d',l): out.append(l);continue
        if on and low==0: on=False
    # merge continuation lines
    M=[]
    for l in out:
        if M and not (re.fullmatch(r'[A-Z0-9 ]+(DEPARTURE|ARRIVAL|TRANSITION)( \(.*\))?',l) or re.match(r'^RWY ?\d{2}',l) or l.startswith('MISSED') or l.startswith('From ') or l.startswith('Cross') or l.startswith('*') or l.startswith('In case')) and not M[-1].endswith('.'):
            M[-1]+=' '+l
        else: M.append(l)
    seen=set();res=[]
    for m in M:
        if m in seen: continue
        seen.add(m);res.append(m)
    return res[:40]
def cl(v):
    return None if v in (None,'','-') else v
PL={};CO={};bad=0
for p,r in sorted(R.items()):
    fn=os.path.basename(p);apt=fn[:4]
    m=re.match(r'\w{4}__\s*(SID ?- ?[Ii]nstrument|SID|STAR|IAC)\s*(?:\((.*?)\)?|(-\d+))?\s*_\d{8}\.pdf$',fn.replace('＊',''))
    if not m: print('?',fn);continue
    kind='SID' if m.group(1).startswith('SID') else 'STAR' if m.group(1)=='STAR' else 'APP'
    short=(m.group(2) or '').strip()
    for k,v in r.get('coords',{}).items():
        if k in ('NM','DME','VOR','NDB','ARP','FAF','IAF','IF','MAPT','MAHF') or not re.search(r'[A-Z]{2}',k): continue
        A=DB.get(apt);import math
        if k in NAV['F'] and not k.startswith('RW') and math.hypot((NAV['F'][k][0]-v[0])*60,(NAV['F'][k][1]-v[1])*48)>1: continue
        if v[2]=='S':
            if k in NAV['F'] and not k.startswith('RW'): continue
            if A and A.get('p') and math.hypot((A['p'][0]-v[0])*60,(A['p'][1]-v[1])*48)>60: continue
        CO.setdefault(apt,{})[k]=v[:2]
    procs=[];cur=None
    for t in r.get('tables',[]):
        labs=t['labels'];pname=None;seg=None
        for l in labs:
            if re.search(r'(DEPARTURE|ARRIVAL)\b',l) and 'TRANSITION' not in l: pname=re.sub(r'\s+',' ',l)
            elif 'TRANSITION' in l: seg=re.sub(r'\s+',' ',l)
            elif re.match(r'RWY',l): seg=re.sub(r'\s+','',l)
            elif kind=='APP': pname=l.split('  ')[-1]
        if pname: cur=pname
        legs=[]
        for g in t['legs']:
            legs.append([g['pt'],g['fix'],1 if g['fo'] else 0,cl(g['crs']),cl(g['dist']),cl(g['turn']),cl(g['alt']),cl(g['spd']),cl(g['vpa']),g.get('ctr'),cl(g.get('r')),cl(g['crsT'])])
        procs.append({'n':cur,'l':seg,'g':legs})
    d=desc(fn)
    holds=[[h['fix'],h['crs'],h['rest']] for h in r.get('holds',[])]
    if not procs and not d: continue
    PL.setdefault(apt,[]).append({'k':kind,'f':short,'s':procs,'d':d,'h':holds})
json.dump(PL,open(os.environ['WORK']+'/pl.json','w'),ensure_ascii=False)
json.dump(CO,open(os.environ['WORK']+'/co.json','w'),ensure_ascii=False)
# stats + match to DB
F=NAV['F'];miss=collections.Counter();dif=[]
for k,v in [(k,v) for a in CO.values() for k,v in a.items() if not k.startswith('RW')]:
    if k in F:
        import math
        d=math.hypot((F[k][0]-v[0])*60,(F[k][1]-v[1])*60*math.cos(math.radians(v[0])))
        if d>0.3: dif.append((k,round(d,2)))
    else: miss['new']+=1
print('apts',len(PL),'procs',sum(len(v) for v in PL.values()),'coords',sum(len(a) for a in CO.values()),dict(miss),'diff>0.3NM',len(dif),sorted(dif,key=lambda x:-x[1])[:15])
um=0
for apt,L in PL.items():
    names=set(s[0] for s in DB.get(apt,{}).get('sid',[]))|set(s[0] for s in DB.get(apt,{}).get('star',[]))|set(x['n'] for x in DB.get(apt,{}).get('iac',[]))
    for x in L:
        if x['f'] not in names: um+=1; 
        if x['f'] not in names and um<25: print('unmatched',apt,x['k'],repr(x['f']))
print('unmatched',um)
