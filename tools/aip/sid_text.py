import json,re,math
R=math.radians
def dest(p,b,d):
    la,lo=R(p[0]),R(p[1]);b=R(b);d=d/3440.065
    la2=math.asin(math.sin(la)*math.cos(d)+math.cos(la)*math.sin(d)*math.cos(b))
    lo2=lo+math.atan2(math.sin(b)*math.sin(d)*math.cos(la),math.cos(d)-math.sin(la)*math.sin(la2))
    return [round(math.degrees(la2),5),round(math.degrees(lo2),5)]
def gc(a,b):
    la1,lo1,la2,lo2=map(R,[a[0],a[1],b[0],b[1]]);return 3440.065*2*math.asin(math.sqrt(max(0,math.sin((la2-la1)/2)**2+math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2)))
def inter(p1,b1,p2,b2):
    k=math.cos(R(p1[0]));x1,y1=p1[1]*60*k,p1[0]*60;x2,y2=p2[1]*60*k,p2[0]*60
    d1=(math.sin(R(b1)),math.cos(R(b1)));d2=(math.sin(R(b2)),math.cos(R(b2)))
    den=d1[0]*d2[1]-d1[1]*d2[0]
    if abs(den)<1e-6: return None
    t=((x2-x1)*d2[1]-(y2-y1)*d2[0])/den;u=((x2-x1)*d1[1]-(y2-y1)*d1[0])/den
    if t<0 or u<0 or t>150 or u>150: return None
    return [round((y1+d1[1]*t)/60,5),round((x1+d1[0]*t)/(60*k),5)],t
def build(text,NV,mv,PCa):
    """text: common part of a conventional SID. returns list of (name,pos or None)"""
    t=text.replace('VOR/DME','').replace('VORTAC','').replace('TACAN','')
    toks=[]
    for m in re.finditer(r'via ([A-Z]{2,3}) R-? ?(\d{3})|to ([A-Z]{2,3}) ?(\d+(?:\.\d+)?) ?DME|to (\d+(?:\.\d+)?) ?DME|(?:to|direct to|proceed to|proceed direct to) ([A-Z][A-Z0-9]{1,4})\b',t):
        if m.group(1): toks.append(('rad',m.group(1),int(m.group(2))))
        elif m.group(3): toks.append(('dme',m.group(3),float(m.group(4))))
        elif m.group(5): toks.append(('dme',None,float(m.group(5))))
        elif m.group(6) and m.group(6) not in ('DME','VOR','NDB','FL'): toks.append(('fix',m.group(6)))
    out=[];rad=None
    pos=lambda n:PCa.get(n) or (NV[n][:2] if n in NV else None)
    for i,tk in enumerate(toks):
        if tk[0]=='rad':
            if tk[1] not in NV: return None
            if rad:
                X=inter(NV[rad[0]][:2],(rad[1]+mv)%360,NV[tk[1]][:2],(tk[2]+180+mv)%360) or inter(NV[rad[0]][:2],(rad[1]+mv)%360,NV[tk[1]][:2],(tk[2]+mv)%360)
                if not X: return None
                if not out:
                    d=max(2,min(8,X[1]*0.4));out.append(('%s%03d%03d'%(rad[0],rad[1],round(d)),dest(NV[rad[0]][:2],(rad[1]+mv)%360,d)))
                out.append(('%s%03d/%s%03d'%(rad[0],rad[1],tk[1],tk[2]),X[0]))
            rad=(tk[1],tk[2])
        elif tk[0]=='dme':
            nav=tk[1] or (rad[0] if rad else None)
            if not rad or nav!=rad[0] or nav not in NV: continue
            p=dest(NV[nav][:2],(rad[1]+mv)%360,tk[2]);out.append(('%s%03d%03d'%(nav,rad[1],round(tk[2])),p));rad=None
        else:
            p=pos(tk[1])
            if not p: return None
            if rad and rad[0]!=tk[1] and rad[0] in NV:
                c=NV[rad[0]][:2];dd=gc(c,p)
                if dd>3:
                    jd=max(2,min(8,dd*0.5));out.append(('%s%03d%03d'%(rad[0],rad[1],round(jd)),dest(c,(rad[1]+mv)%360,jd)))
            out.append((tk[1],p));rad=None
    return out
