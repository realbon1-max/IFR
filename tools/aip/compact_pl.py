import os
import json,re,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from clean import dec,clean_ma
PL=json.load(open('pl.json'));CO=json.load(open('co.json'));MA=json.load(open('ma2.json'))
DB=json.load(open(os.environ['WORK']+'/db.json'))
out={}
for apt,L in PL.items():
    for x in L:
        segs=[]
        for s in x['s']:
            n=(s['n'] or '');n=re.sub(r'\s*(RNP ?1|RNAV ?1|RNP APCH)$','',n).strip()
            if x['k']=='APP': n=re.sub(r'^\w{4} / [A-Z\-\. ]+? (?=(RNP|RNAV|ILS|LOC|VOR|NDB|GLS|TACAN))','',n)
            l=s['l'];
            if l: l=re.sub(r'\s*(RNP ?1|RNAV ?1)$','',l).strip()
            g=[[v if v is not None else '' for v in leg] for leg in s['g']]
            for leg in g:
                if leg[1] and not re.fullmatch(r'[A-Z][A-Z0-9]{1,6}',leg[1]): leg[1]=''
            for leg in g:
                while leg and leg[-1]=='': leg.pop()
            segs.append([n,l or '',g])
        d=[dec(t).replace('Û','°').replace('˚','°') for t in x['d']]
        d=[t for t in d if len(t)>5 and len(re.findall(r'\b[a-z]{2,}\b',t))>=2]
        ma=''
        if x['k']=='APP':
            for k,v in MA.items():
                if k.startswith(apt) and v and v[0] and re.sub(r'\s','',k).find(re.sub(r'\s','',x['f']))>=0: ma=v[0];break
        h=[[hh[0],hh[1] or '']+[r for r in hh[2]][:5] for hh in x['h']]
        out.setdefault(apt,[]).append([x['k'],x['f'],segs,d,h,ma])
# approaches without tables: still list (MA text) for every IAC file
seen={(a,x[1]) for a,L in out.items() for x in L}
import os
for k,v in MA.items():
    apt=k[:4];m=re.match(r'\w{4}__\s*IAC\s*\((.*)\)\S*_\d{8}\.pdf$',k.replace('＊',''))
    if not m: continue
    f=m.group(1)
    if (apt,f) in seen: continue
    if v and v[0]: out.setdefault(apt,[]).append(['APP',f,[],[],[],v[0]])
ST=re.compile(r'^(Climb|Turn|Direct|From|To|At|Proceed|Continue|Cross|Fly|Track|When|After|Straight|Immediately|Climbing|Via|Upon|Execute|Make|Maintain)\b')
for a,L in out.items():
    for x in L:
        if x[5] and not ST.match(x[5]): x[5]='?'+x[5]
pc={a:{k:[round(v[0],5),round(v[1],5)] for k,v in d.items()} for a,d in CO.items()}
import math
NAVF=json.load(open(os.environ['WORK']+'/nav.json'))['F']
def pos(a,f): return pc.get(a,{}).get(f) or (NAVF[f][:2] if f in NAVF else None)
def gcd(p,q):
    la1,lo1,la2,lo2=map(math.radians,[p[0],p[1],q[0],q[1]]);return 3440.065*2*math.asin(math.sqrt(math.sin((la2-la1)/2)**2+math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2))
drop=0
for a,L in out.items():
    for x in L:
        for sg in x[2]:
            g=sg[2]
            for i in range(1,len(g)):
                if g[i][0]!='TF' or len(g[i])<5 or not g[i][4] or not g[i][1] or not g[i-1][1]: continue
                p,q=pos(a,g[i-1][1]),pos(a,g[i][1])
                try: t=abs(float(g[i][4]))
                except: continue
                if p and q and abs(gcd(p,q)-t)>max(0.6,t*0.06):
                    for f in (g[i][1],g[i-1][1]):
                        if f in pc.get(a,{}) and f not in NAVF: pc[a].pop(f);drop+=1;break
print('dropped',drop)
DF=json.load(open('dmefix.json'));add=0
for fn,L in DF.items():
    a=fn[:4];A=DB.get(a)
    m=re.search(r'RWY\s?(\d{2}[LRC]?)',fn)
    if not A or not m: continue
    rw=[r for r in A['rw'] if r['id']==m.group(1) and r.get('t') and r.get('b') is not None]
    if not rw: continue
    rw=rw[0];t=rw['t'];ob=math.radians((rw['b']+180)%360);k=math.cos(math.radians(t[0]))
    ux,uy=math.sin(ob),math.cos(ob)
    for name,role,d,nav in L:
        if name in NAVF or name in pc.get(a,{}) or nav not in NAVF: continue
        if role not in ('IF','FAF','MAPt','SDF','FAP',''): continue
        n=NAVF[nav];nx=(n[1]-t[1])*60*k;ny=(n[0]-t[0])*60
        al=nx*ux+ny*uy;xt=-nx*uy+ny*ux
        if abs(xt)>1.5 or d<abs(xt): continue
        sdist=al+math.sqrt(d*d-xt*xt)
        if sdist<0 or sdist>25: continue
        pc.setdefault(a,{})[name]=[round(t[0]+sdist*uy/60,5),round(t[1]+sdist*ux/(60*k),5)];add+=1
print('dme fixes added',add)
s=json.dumps(out,ensure_ascii=False,separators=(',',':'));c=json.dumps(pc,separators=(',',':'))
open('pl_compact.json','w').write(s);open('pc_compact.json','w').write(c)
print(len(s),len(c),sum(len(v) for v in out.values()))
