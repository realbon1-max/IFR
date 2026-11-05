import os,re,json,sys
from multiprocessing import Pool
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from parse_ct import parse
root=os.environ['AIP_ROOT']
def job(p):
    try: return p,parse(p)
    except Exception as e: return p,{'err':str(e)}
files=[]
for d in sorted(os.listdir(root)):
    for f in os.listdir(os.path.join(root,d)):
        if re.match(r'\w{4}__(SID|STAR|IAC)',f): files.append(os.path.join(root,d,f))
txt=os.environ['AIP_TXT']+'/'
pass
print(len(files))
with Pool(8) as pool: res=dict(pool.map(job,files))
json.dump(res,open(os.environ['WORK']+'/ct_raw.json','w'),ensure_ascii=False)
