# Parse AIP Japan RNAV coding tables (SID/STAR/IAC) + waypoint coordinate tables + holds.
import pdfplumber, re, json, sys, os
DASH=set(['-','–','—','凟','–','‒'])
def cid(t):
    if t is None or '(cid:' not in t: return t
    ns=[int(x) for x in re.findall(r'\(cid:(\d+)\)',t)]
    r=re.sub(r'\(cid:(\d+)\)',lambda m:chr(int(m.group(1))+29) if int(m.group(1))<100 else '',t)
    return r if r.strip() else '-'
def nd(s): return None if (s is None or s in DASH or s.strip() in DASH or s=='') else s
def lines_of(words,tol=2.5):
    L=[]
    for w in sorted(words,key=lambda w:(round(w['top']),w['x0'])):
        for l in L:
            if abs(l['y']-w['top'])<tol: l['w'].append(w);break
        else: L.append({'y':w['top'],'w':[w]})
    for l in L: l['w'].sort(key=lambda w:w['x0']); l['t']=' '.join(w['text'] for w in l['w'])
    return sorted(L,key=lambda l:l['y'])
COORD=re.compile(r'^(\d{6}(?:\.\d+)?)([NS])$')
def dms(s,h,deg):
    d=int(s[:deg]);m=int(s[deg:deg+2]);x=float(s[deg+2:]);v=d+m/60+x/3600
    return -v if h in 'SW' else v
LAB=re.compile(r'(RWY\s?\d{2}[LRC]?(?:\s*[/&,]\s*\d{2}[LRC]?)*|[A-Z0-9 ]*(DEPARTURE|ARRIVAL|TRANSITION)\b.*|MISSED APPROACH.*|.*\b(RNP|RNAV|ILS|LOC|VOR|NDB|GLS)\b.*RWY.*)')
def parse(path):
    out={'tables':[],'coords':{},'holds':[]}
    with pdfplumber.open(path) as pdf:
        for pi,page in enumerate(pdf.pages):
            words=page.extract_words(x_tolerance=1.2,y_tolerance=2,keep_blank_chars=False)
            for w in words: w['text']=cid(w['text']).replace('\u3000','').replace('䢢','')
            words=[w for w in words if w['text']]
            L=lines_of(words)
            # coordinates anywhere
            for l in L:
                ws=l['w'];tx=[w['text'] for w in ws]
                for i,w in enumerate(ws):
                    j=' '.join(tx[i:i+3])
                    m=re.match(r'^(\d{6}(?:\.\d+)?)([NS])\s*/?\s*(\d{7}(?:\.\d+)?)([EW])',j)
                    if not m: continue
                    k=i-1
                    while k>=0 and tx[k] in (':','/'): k-=1
                    if k<0 or ws[i]['x0']-ws[k]['x1']>300: continue
                    nm=re.sub(r'\(.*\)$','',tx[k]).rstrip(':')
                    if not re.fullmatch(r'[A-Z][A-Z0-9]{1,6}',nm): continue
                    out['coords'][nm]=[round(dms(m.group(1),m.group(2),2),6),round(dms(m.group(3),m.group(4),3),6),'T']
            # split coordinates: NAME lat on one line, lon just below
            lats=[w for w in words if re.fullmatch(r'\d{6}\.\d+[NS]',w['text'])]
            for la in lats:
                lo=[w for w in words if re.fullmatch(r'\d{7}\.\d+[EW]',w['text']) and 0<w['top']-la['top']<16 and abs(w['x0']-la['x0'])<25]
                if not lo: continue
                lo=lo[0];nm=[w for w in words if abs(w['top']-la['top'])<3 and w['x1']<la['x0'] and la['x0']-w['x1']<60 and re.fullmatch(r'[A-Z][A-Z0-9]{1,6}',w['text'])]
                if not nm: nm=[w for w in words if 3<la['top']-w['top']<16 and abs(w['x0']-la['x0'])<45 and re.fullmatch(r'[A-Z][A-Z0-9]{1,6}',w['text'])]
                if not nm: nm=[w for w in words if abs(w['top']-lo['top'])<3 and w['x1']<lo['x0'] and lo['x0']-w['x1']<260 and re.fullmatch(r'[A-Z][A-Z0-9]{1,6}',w['text'])]
                if not nm: continue
                nm=max(nm,key=lambda w:w['x1'])['text']
                if nm in out['coords']: continue
                out['coords'][nm]=[round(dms(la['text'][:-1],la['text'][-1],2),6),round(dms(lo['text'][:-1],lo['text'][-1],3),6),'S']
            hdrs=[w for w in words if w['text']=='Serial']
            for hi,h in enumerate(hdrs):
                y0=h['top']
                hl=[w for w in words if abs(w['top']-y0)<3 and w['x0']>=h['x0']-2]
                hl.sort(key=lambda w:w['x0'])
                # restrict to this table: stop at next 'Serial' to the right on same line (side by side tables)
                right=[w for w in hdrs if abs(w['top']-y0)<3 and w['x0']>h['x0']+5]
                xmax=min([w['x0'] for w in right]+[1e9])
                hl=[w for w in hl if w['x0']<xmax-2]
                names=[w['text'] for w in hl]
                # merge split header words ("Way point")
                cols=[];
                for w in hl:
                    t=w['text']
                    if cols and t in ('point','igation','tical','ier','er','ication'): cols[-1]['x1']=w['x1'];cols[-1]['t']+=t;continue
                    cols.append({'t':t,'x0':w['x0'],'x1':w['x1']})
                key=[c['t'].lower()[:4] for c in cols]
                # second header line may add RDH column
                sub=[w for w in words if 2<w['top']-y0<16 and h['x0']-2<=w['x0']<xmax-2]
                if any(w['text']=='RDH' for w in sub) and 'rdh' not in key:
                    r=[w for w in sub if w['text']=='RDH'][0];cols.append({'t':'RDH','x0':r['x0'],'x1':r['x1']})
                cols.sort(key=lambda c:c['x0'])
                cen=[(c['x0']+c['x1'])/2 for c in cols]
                xL=h['x0']-6;xR=(cols[-1]['x1']+40) if xmax>1e8 else xmax-2
                # table vertical end: next header/hold/coords/CHANGE below in same x span
                stops=[l['y'] for l in L if l['y']>y0+20 and any(xL<=w['x0']<=xR for w in l['w']) and re.search(r'^(Serial|Inbound|Waypoint\s*Coord|Waypoint Coordinates|CHANGE|Civil Aviation)',' '.join(w['text'] for w in l['w'] if xL<=w['x0']<=xR).strip())]
                yend=min(stops+[page.height])
                # label lines above
                prevend=max([0]+[hh['top'] for hh in hdrs if hh['top']<y0-5 and abs(hh['x0']-h['x0'])<40])
                labs=[]
                for l in L:
                    if prevend<l['y']<y0-1:
                        t=' '.join(w['text'] for w in l['w'] if xL-120<=w['x0']<=xR).strip()
                        t=t.split('*')[0].strip()
                        if t and LAB.fullmatch(t) and 'CHART' not in t: labs.append(t)
                tw=[w for w in words if y0+8<w['top']<yend and xL<=w['x0']<=xR]
                rows=[w for w in tw if re.fullmatch(r'\d{3}',w['text']) and abs(w['x0']-h['x0'])<12]
                rows.sort(key=lambda w:w['top'])
                if not rows: continue
                R=[{'y':r['top'],'c':{}} for r in rows]
                colname=lambda x:min(range(len(cen)),key=lambda i:abs(cen[i]-x))
                for w in tw:
                    if w in rows: continue
                    xc=(w['x0']+w['x1'])/2;ci=colname(xc);cn=cols[ci]['t'].lower()
                    ri=min(range(len(R)),key=lambda i:abs(R[i]['y']-w['top']))
                    if abs(R[ri]['y']-w['top'])>(18 if cn.startswith('path') else 14): continue
                    R[ri]['c'].setdefault(cn[:4],[]).append((w['top']-R[ri]['y'],w['text']))
                legs=[]
                for r in R:
                    g=lambda k:[t for _,t in sorted(r['c'].get(k,[]),key=lambda a:abs(a[0]))]
                    crs=g('cour');mag=[c for c in crs if re.fullmatch(r'\d{3}(\.\d)?',c)];tru=[c.strip('()') for c in crs if c.startswith('(')]
                    def one(k):
                        v=[x for x in g(k) if x not in DASH];return v[0] if v else None
                    leg={'pt':one('path'),'fix':one('wayp'),'fo':one('fly')=='Y','crs':mag[0] if mag else None,'crsT':tru[0] if tru else None,
                         'dist':one('dist'),'turn':one('turn'),'alt':' '.join(x for x in g('alti') if x not in DASH) or None,'spd':' '.join(x for x in g('spee') if x not in DASH) or None,
                         'vpa':one('vert') or one('rdh'),'nav':one('navi') or one('rnp')}
                    pp=g('path');pts=[x for x in pp if re.fullmatch(r'[A-Z]{2}',x)];leg['pt']=pts[0] if pts else None
                    allp=[t for _,t in sorted(r['c'].get('path',[]))]
                    if 'Center:' in allp:
                        i=allp.index('Center:');cand=[x for x in allp[i+1:] if re.fullmatch(r'[A-Z0-9]{3,6}',x) and x!='RF']
                        if cand: leg['ctr']=cand[0]
                    rr=[x for x in allp if x.startswith('r=')]
                    if rr: leg['r']=rr[0][2:].replace('NM','')
                    if leg.get('ctr') and not leg['pt']: leg['pt']='RF'
                    legs.append(leg)
                out['tables'].append({'page':pi,'y':round(y0),'x':round(h['x0']),'labels':labs,'legs':legs})
            # holds
            for l in L:
                ws=l['w']
                for i,w in enumerate(ws):
                    if w['text']=='Hold' and i+1<len(ws):
                        fix=ws[i+1]['text'];rest=[x['text'] for x in ws[i+2:i+9]]
                        near=[x for x in words if abs(x['top']-l['y'])<14 and abs(x['x0']-ws[i+1]['x1'])<60 and re.fullmatch(r'\d{3}',x['text'])]
                        out['holds'].append({'fix':fix,'crs':near[0]['text'] if near else None,'rest':rest})
    return out
if __name__=='__main__':
    r=parse(sys.argv[1]);print(json.dumps(r,ensure_ascii=False,indent=0)[:6000])
