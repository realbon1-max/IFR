# Change report (markdown) between the previous and the rebuilt data, for the pull request.
import json, os
W = os.environ['WORK']; L = lambda f: json.load(open(os.path.join(W, f))) if os.path.exists(os.path.join(W, f)) else {}
old, new = L('pld_old.json'), L('pl_compact.json'); oc, nc = L('chx_old.json'), L('charts_idx.json'); po, pn = L('pcd_old.json'), L('pc_compact.json')
src = L('rendered.json')
out = [f"## AIP 更新レポート（AIRAC {os.environ.get('AIRAC_EFF','?')}）", '']
def procs(d, a): return {f"{x[0]} {x[1]}": json.dumps(x[2], ensure_ascii=False, sort_keys=True) for x in d.get(a, [])}
add = rem = chg = 0; lines = []
for a in sorted(set(old) | set(new)):
    o, n = procs(old, a), procs(new, a)
    A = sorted(set(n) - set(o)); R = sorted(set(o) - set(n)); C = sorted(k for k in set(o) & set(n) if o[k] != n[k])
    add += len(A); rem += len(R); chg += len(C)
    if A or R or C: lines.append(f"- **{a}**" + ''.join([f"　追加: {', '.join(A)}" if A else '', f"　削除: {', '.join(R)}" if R else '', f"　経路・高度が変化: {', '.join(C)}" if C else '']))
out.append(f"### 手順（コーディング表）　追加 {add}・削除 {rem}・変化 {chg}"); out += lines or ['- 変化なし']; out.append('')
moved = []
for a in sorted(set(po) & set(pn)):
    for f in sorted(set(po[a]) & set(pn[a])):
        p, q = po[a][f], pn[a][f]
        d = ((p[0] - q[0]) ** 2 + ((p[1] - q[1]) * 0.8) ** 2) ** 0.5 * 60
        if d > 0.2: moved.append(f"- {a} {f}：{d:.1f}NM 移動")
out.append(f"### fix座標の変化（0.2NM超）　{len(moved)}件"); out += moved[:200] or ['- 変化なし']; out.append('')
ch = []
for a in sorted(set(oc) | set(nc)):
    o = {f"{x[0]} {x[1]}" for x in oc.get(a, [])}; n = {f"{x[0]} {x[1]}" for x in nc.get(a, [])}
    if o != n: ch.append(f"- {a}：追加 {', '.join(sorted(n - o)) or 'なし'}／削除 {', '.join(sorted(o - n)) or 'なし'}")
out.append(f"### チャート画像　作り直した飛行場 {len(src.get('rendered', []))}：{' '.join(src.get('rendered', [])) or 'なし'}"); out += ch or ['- 手順名の増減なし']; out.append('')
out += ['### 自動では更新していないもの', '- 飛行場の基本データ（滑走路・周波数・SID/STAR/進入の一覧と最低気象条件）、航空路・fix・管制区、従来型進入の形（ベースターン等）は前の版のままです。上の一覧で変化がある飛行場は、チャート画像と見比べて確認してください。', '', '問題がなければこのプルリクエストを「Merge」すると、アプリに反映されます。']
open(os.path.join(W, 'report.md'), 'w').write('\n'.join(out)); print('\n'.join(out[:40]))
