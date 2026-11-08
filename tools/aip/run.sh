#!/usr/bin/env bash
# Rebuild the procedure data and chart images from an AIP Japan AD 2 folder set.
# env: AIP_ROOT (folder with ICAO__YYYYMMDD subfolders), HTML (app index.html), CHARTS (charts dir), WORK (scratch), AIRAC_EFF (YYYY-MM-DD)
set -euo pipefail
D=$(cd "$(dirname "$0")" && pwd)
export AIP_TXT="${AIP_TXT:-$WORK/txt}"; mkdir -p "$WORK" "$AIP_TXT"
python3 "$D/prep.py"
python3 "$D/mktxt.py"
cd "$WORK"
python3 "$D/run_ct.py"       # coding tables / waypoint tables / holds
python3 "$D/build_pl.py"     # procedure legs + coordinates
python3 "$D/ma_text.py"      # missed-approach text
python3 "$D/ma_text2.py"
python3 "$D/dmefix.py"       # DME fixes
python3 "$D/compact_pl.py"   # compact PLD / PCD
python3 "$D/embed.py"
python3 "$D/apply_sid.py"    # runway fill for SIDs in DB
python3 "$D/render_charts.py"
python3 "$D/embed.py"        # CHX + AIRAC after charts
python3 "$D/fixups.py"       # manual corrections (split combined charts etc.)
python3 "$D/report.py"
