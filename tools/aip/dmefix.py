import os
import pdfplumber,re,json,os,math
from multiprocessing import Pool
root=os.environ['AIP_ROOT']
def job(path):
    out=[]
    try:
        with pdfplumber.open(path) as pdf:
            W=pdf.pages[0].extract_words(x_tolerance=1.2,y_tolerance=2)
            for w in W:
                m=re.fullmatch(r'([A-Z]{5})(?:\((IAF|IF|FAF|MAPt|SDF|FAP|MATF|MAHF)\))?',w['text'])
                if not m: continue
                below=[v for v in W if 2<v['top']-w['top']<14 and abs(v['x0']-w['x0'])<30 and re.fullmatch(r'D\d+(\.\d+)?',v['text'])]
                if not below: continue
                d=below[0];nav=[v for v in W if abs(v['top']-d['top'])<3 and 0<v['x0']-d['x1']<12 and re.fullmatch(r'[A-Z]{2,3}',v['text'])]
                if not nav: continue
                out.append([m.group(1),m.group(2) or '',float(d['text'][1:]),nav[0]['text']])
    except Exception as e: pass
    return os.path.basename(path),out
files=[os.path.join(root,d,f) for d in os.listdir(root) for f in os.listdir(os.path.join(root,d)) if '__IAC' in f]
with Pool(2) as P: R=dict(P.map(job,files))
json.dump(R,open(os.environ['WORK']+'/dmefix.json','w'));print(len(R),sum(len(v) for v in R.values()))
print([ (k,v) for k,v in R.items() if 'RJAF__IAC (VOR' in k])
