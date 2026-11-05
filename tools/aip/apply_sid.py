import os
import json,re,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from sid_text import build
p=os.environ['HTML'];h=open(p).read()
def grab(name):
    i=h.index('const '+name+'=')+len(name)+7;o,e=json.JSONDecoder().raw_decode(h[i:]);return o,i,i+e
DB,i0,i1=grab('DB')
PL=json.load(open(os.environ['WORK']+'/pl_compact.json'));NV=json.load(open(os.environ['WORK']+'/nav.json'))['F']
PC,j0,j1=None,None,None
PC=json.load(open(os.environ['WORK']+'/pc_compact.json'))
chg=[]
for apt,L in PL.items():
    A=DB.get(apt)
    if not A: continue
    mv=A.get('mv') or 0
    for x in L:
        if x[0]!='SID' or any(s[2] for s in x[2]): continue
        com=[t for t in x[3] if t.startswith('...') or t.startswith('From')]
        if not com: continue
        r=build(' '.join(com),NV,mv,PC.get(apt,{}))
        if not r: continue
        names=[n for n,_ in r]
        if '  ' in x[1] or len(set(names))<len(names): continue
        if any('/' in n and n.split('/')[0][:-3]==n.split('/')[1][:-3] for n in names): continue
        s=next((s for s in A['sid'] if s[0]==x[1]),None)
        if not s: continue
        # runways named in the AIP text but missing from the data: clone the closest main entry
        rwt=[]
        for t in x[3]:
            m=re.match(r'^RWY ?(\d{2}[LRC]?(?: ?[/&,] ?\d{2}[LRC]?)*) ?:',t)
            if m:
                ids=[q.strip() for q in re.split(r'[/&,]',m.group(1))];ids=[q if len(q)>=2 else q for q in ids]
                tr=re.search(r'turn (left|right)',t);rwt.append((ids,'L' if tr and tr.group(1)=='left' else 'R' if tr else None))
        have=set(r for e in s[2] if not e[5] for r in (e[0] or []))
        mains=[e for e in s[2] if not e[5]]
        for ids,tr in rwt:
            miss=[q for q in ids if q not in have]
            if miss and mains:
                base=json.loads(json.dumps(mains[0]));base[0]=miss;base[4]=tr;base[2]=None;base[6]=None
                if len(base)>8 and isinstance(base[8],list) and base[8]: base[8][0]=tr
                s[2].insert(len(mains),base);mains.append(base);have.update(miss);chg.append((apt,x[1],'add RWY',miss))
        for e in s[2]:
            if e[5]: continue
            f=e[1] or []
            if not f or names[-1]!=f[-1]: continue
            it=iter(names)
            if not all(any(n==q for n in it) for q in f): continue
            if len(names)<=len(f): continue
            # keep runway-specific leading fixes not in names (e.g. turn DME points) before the first common one
            first=names[0];lead=[q for q in f if q not in names]
            e[1]=lead+names
            if len(e)>8 and isinstance(e[8],list): e[8]=(e[8]+[None]*len(e[1]))[:len(e[1])]
            if len(e)>9 and isinstance(e[9],list): e[9]=(e[9]+[0]*len(e[1]))[:len(e[1])]
            for n,q in r:
                if n not in NV: PC.setdefault(apt,{})[n]=q
            chg.append((apt,x[1],f,e[1]))
h=h[:i0]+json.dumps(DB,ensure_ascii=False,separators=(',',':'))+h[i1:]
i=h.index('const PCD=')+10;o,e=json.JSONDecoder().raw_decode(h[i:]);h=h[:i]+json.dumps(PC,separators=(',',':'))+h[i+e:]
open(p,'w').write(h);json.dump(PC,open(os.environ['WORK']+'/pc_compact.json','w'),separators=(',',':'))
print(len(chg));[print(c) for c in chg[:40]]
