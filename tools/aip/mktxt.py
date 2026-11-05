# pdftotext -layout for every chart PDF (the parsers read these alongside the PDFs)
import os, re, subprocess, sys
from multiprocessing import Pool
root = os.environ['AIP_ROOT']; out = os.environ['AIP_TXT']; os.makedirs(out, exist_ok=True)
jobs = []
for d in sorted(os.listdir(root)):
    p = os.path.join(root, d)
    if not os.path.isdir(p): continue
    for f in os.listdir(p):
        if f.lower().endswith('.pdf') and re.match(r'\w{4}__(SID|STAR|IAC)', f): jobs.append((os.path.join(p, f), os.path.join(out, f[:-4] + '.txt')))
def job(j):
    if not os.path.exists(j[1]): subprocess.run(['pdftotext', '-layout', j[0], j[1]], stderr=subprocess.DEVNULL)
if __name__ == '__main__':
    with Pool(os.cpu_count() or 2) as P: P.map(job, jobs)
    print('txt', len(jobs))
