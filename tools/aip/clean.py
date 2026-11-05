import re
def dec(s):
    def fix(tok):
        if re.search(r'[\x00-\x1f]',tok): return ''.join(chr(ord(c)+29) if ord(c)<0x60 else c for c in tok)
        return tok
    return ' '.join(fix(t) for t in s.split(' '))
START=re.compile(r'\b(Climb|Turn|Direct|From|To|At|Proceed|Continue|Cross|Fly|Track|When|After|Straight|Immediately|Climbing|Via|Upon|Execute|Make|Maintain)\b')
def clean_ma(s):
    s=dec(s).replace('Û','°').replace('˚','°').replace('´','FT')
    m=START.search(s)
    if m and m.start()<70: s=s[m.start():]
    return re.sub(r'\s+',' ',s).strip()
