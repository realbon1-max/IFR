import os
import pdfplumber,re,json,os,sys
from multiprocessing import Pool
root=os.environ['AIP_ROOT']
def ma(path):
    res=[]
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages[:1]:
            W=page.extract_words(x_tolerance=1.2,y_tolerance=2)
            for i,w in enumerate(W):
                if w['text']=='MISSED' and i+1<len(W) and W[i+1]['text'].startswith('APPROACH'):
                    import subprocess
                    sc=150/72
                    X=int((w['x0']-34)*sc);Y=int(w['bottom']*sc);Wd=int(272*sc);H=int(110*sc)
                    t=subprocess.run(['pdftotext','-r','150','-f',str(page.page_number),'-l',str(page.page_number),'-x',str(X),'-y',str(Y),'-W',str(Wd),'-H',str(H),'-layout',path,'-'],capture_output=True,text=True).stdout
                    L=[re.sub(r'\s{2,}','  ',l).strip() for l in t.split('\n')]
                    out=[]
                    for l in L:
                        if not l: 
                            if out and out[-1]!='': out.append('')
                            continue
                        if re.match(r'^(MINIMA|CAT\b|Missed APCH climb|DME to|NM to|ALT)',l): break
                        out.append(l.split('  ')[0])
                    txt=' '.join(x for x in out if x)
                    txt=re.sub(r'\s+',' ',txt).replace('\x9d','°').replace('(cid:157)','°').strip()
                    m=re.search(r'^(.*?Contact [A-Z ]+?(APP|RADIO|TOWER|CONTROL|RADAR|DEPARTURE|INFORMATION)\b\.?)',txt)
                    if m: txt=m.group(1)
                    else:
                        m=re.search(r'^(.*?\bhold(?: at [0-9]+FT)?\.)',txt)
                        if m: txt=m.group(1)
                    res.append(txt);break
                    x0=w['x0']-4;y=w['bottom'];lines={}
                    cand=[v for v in W if v['top']>y-1 and v['top']<y+120 and x0<=v['x0']<x0+230]
                    for v in sorted(cand,key=lambda v:(v['top'],v['x0'])):
                        k=round(v['top']/3)
                        lines.setdefault(k,[]).append(v)
                    txt=[];last=None
                    for k in sorted(lines):
                        ws=sorted(lines[k],key=lambda v:v['x0'])
                        # stop if gap
                        if last is not None and ws[0]['top']-last>30: break
                        t=' '.join(v['text'] for v in ws)
                        if re.match(r'^(MINIMA|CAT\b|Missed APCH climb|DME to|NM to)',t): break
                        if not re.search(r'[a-z]',t) and not re.search(r'\b(VOR|DME|NDB|FT|MBE|hold)\b',t) and len(txt)>0 and len(t)<12: continue
                        txt.append(t);last=ws[0]['top']
                    s=' '.join(txt)
                    s=re.sub(r'\s+',' ',s).strip()
                    if s: res.append(s)
                    break
    return res
def job(p):
    try: return os.path.basename(p),ma(p)
    except Exception as e: return os.path.basename(p),['ERR '+str(e)]
if __name__=='__main__':
    files=[os.path.join(root,d,f) for d in os.listdir(root) for f in os.listdir(os.path.join(root,d)) if '__IAC' in f]
    if len(sys.argv)>1: files=[f for f in files if sys.argv[1] in f]
    with Pool(2) as P: R=dict(P.map(job,files))
    json.dump(R,open(os.environ['WORK']+'/ma.json','w'),ensure_ascii=False)
    for k in list(R)[:12]: print(k,R[k])
