import os
import re,json,os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from clean import dec
TXT=os.environ['AIP_TXT']+'/'
def ma2(fn):
    try: L=open(TXT+fn[:-4]+'.txt',errors='ignore').read().split('\n')
    except: return ''
    for i,l in enumerate(L):
        c=l.find('MISSED APPROACH')
        if c<0: continue
        out=[]
        for l2 in L[i+1:i+14]:
            seg=l2[max(0,c-3):c+48]
            seg=re.split(r'\s{3,}',seg.strip())[0] if seg.strip() else ''
            if re.match(r'^(MINIMA|CAT\b|Missed APCH|DME to|NM to)',seg): break
            if seg: out.append(seg)
        t=dec(' '.join(out)).replace('Û','°').replace('˚','°')
        t=re.sub(r'\s+',' ',t)
        m=re.search(r'^(.*?Contact [A-Z ]+?(APP|RADIO|TOWER|CONTROL|RADAR|DEPARTURE|INFORMATION)\b\.?)',t)
        if m: t=m.group(1)
        return t.strip()
    return ''
if __name__=='__main__':
    R=json.load(open('ma.json'));START=re.compile(r'^(Climb|Turn|Direct|From|To|At|Proceed|Continue|Cross|Fly|Track|When|After|Straight|Immediately|Climbing|Via|Upon|Execute|Make|Maintain)\b')
    from clean import clean_ma
    n=0;out={}
    for k,v in R.items():
        a=clean_ma(v[0]) if v and v[0] else ''
        b=ma2(k)
        sa=bool(START.match(a));sb=bool(START.match(b))
        best=b if (sb and not sa) or (sb and sa and len(b)>len(a)+8 and 'Contact' in b) else a
        if best!=a: n+=1
        out[k]=[best]
    json.dump(out,open('ma2.json','w'),ensure_ascii=False);print('replaced',n)
    for k in out:
        if 'RJAF__IAC (VOR' in k or 'RJDT__IAC (VOR RWY14' in k or 'RJSS__IAC (VOR RWY30' in k: print(k,out[k])
