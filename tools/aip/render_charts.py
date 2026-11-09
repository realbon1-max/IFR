import os,re,subprocess,json,sys,hashlib
from multiprocessing import Pool
from PIL import Image
root=os.environ['AIP_ROOT'];out=os.environ['CHARTS']
latest={}
for d in os.listdir(root):
    if '__' not in d or not os.path.isdir(os.path.join(root,d)): continue
    a,dt=d.split('__');latest[a]=max(latest.get(a,''),dt)
# only re-render aerodromes whose AD 2 folder date changed since the last build (charts/_src.json)
srcf=os.path.join(out,'_src.json');SRC=json.load(open(srcf)) if os.path.exists(srcf) else {}
OLD=json.load(open(os.environ['WORK']+'/chx_old.json')) if os.path.exists(os.environ['WORK']+'/chx_old.json') else {}
todo={a:dt for a,dt in latest.items() if SRC.get(a)!=dt or os.environ.get('CHARTS_ALL')}
jobs=[]
for a,dt in todo.items():
    import shutil
    if os.path.isdir(f'{out}/{a}'): shutil.rmtree(f'{out}/{a}')
    for f in sorted(os.listdir(f'{root}/{a}__{dt}')):
        m=re.match(r'\w{4}__\s*(SID ?- ?[Ii]nstrument|SID|STAR|IAC|ADC|APDC|GMC)\s*(?:\((.*?)\)?|(-\s*\d+))?\s*(?:＊)?_\d{8}\.pdf$',f.replace('＊',''))
        if not m: continue
        kind='SID' if m.group(1).startswith('SID') else 'STAR' if m.group(1)=='STAR' else 'AD' if m.group(1) in ('ADC','APDC','GMC') else 'APP'
        short=(m.group(2) or '').strip() if kind!='AD' else (m.group(1)+' '+(m.group(3) or '').replace(' ','')).strip()
        jobs.append((a,kind,short,f'{root}/{a}__{dt}/{f}'))
def job(j):
    a,kind,short,p=j
    slug=re.sub(r'[^A-Za-z0-9]+','_',f'{kind}_{short}').strip('_')[:60]+'_'+hashlib.md5(p.encode()).hexdigest()[:4]
    os.makedirs(f'{out}/{a}',exist_ok=True);tmp=os.path.join(os.environ['WORK'],'tmp',f'{a}_{slug}')
    os.makedirs(os.path.dirname(tmp),exist_ok=True);subprocess.run(['pdftoppm','-r','190' if kind=='AD' else '140','-gray','-png',p,tmp],stderr=subprocess.DEVNULL)
    fs=[]
    for k in range(1,9):
        cand=[x for x in [f'{tmp}-{k}.png',f'{tmp}-0{k}.png'] if os.path.exists(x)]
        if not cand: break
        im=Image.open(cand[0]);name=f'{slug}-{k}.webp';im.save(f'{out}/{a}/{name}','WEBP',quality=55,method=6);os.remove(cand[0]);fs.append(name)
    return a,kind,short,fs
if __name__=='__main__':
    with Pool(2) as P: R=P.map(job,jobs)
    idx={a:v for a,v in OLD.items() if a not in todo and a in latest}
    for a,kind,short,fs in R:
        if fs: idx.setdefault(a,[]).append([kind,short,fs])
    idx=dict(sorted(idx.items()))
    json.dump(idx,open(os.environ['WORK']+'/charts_idx.json','w'),separators=(',',':'))
    json.dump({**{a:SRC.get(a) for a in latest if a not in todo and SRC.get(a)},**todo},open(srcf,'w'),indent=0,sort_keys=True)
    json.dump({'rendered':sorted(todo)},open(os.environ['WORK']+'/rendered.json','w'))
    print(len(R),sum(len(x[3]) for x in R))
