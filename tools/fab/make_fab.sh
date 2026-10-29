#!/bin/bash
# JLCPCB production files from the KiCad project, with kicad-cli (KiCad 9 or 10).
#   tools/fab/make_fab.sh  ->  fab/gerbers.zip, fab/bom_jlc.csv, fab/cpl_jlc.csv
# Order settings these files assume (they are NOT in the files): Soldermask BLACK, Silkscreen
# WHITE, surface finish ENIG, thickness 0.8 mm. On a light soldermask the inverted QR prints with
# reversed polarity and will not scan.
set -euo pipefail
KCLI=${KCLI:-kicad-cli}
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
HW="$ROOT/hardware"; PCB="$HW/Business Card v2.kicad_pcb"; SCH="$HW/Business Card v2.kicad_sch"
OUT="$ROOT/fab"; TMP=$(mktemp -d "$ROOT/.fabtmp.XXXXXX")  # under the repo: a Flatpak kicad-cli has its own /tmp
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$OUT" "$TMP/gerbers"

"$KCLI" pcb export gerbers -o "$TMP/gerbers/" \
  --layers F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts \
  --subtract-soldermask "$PCB"
"$KCLI" pcb export drill -o "$TMP/gerbers/" --format excellon --excellon-units mm "$PCB"
( cd "$TMP/gerbers" && rm -f "$OUT/gerbers.zip" && python3 -c "
import zipfile,os,sys
z=zipfile.ZipFile(sys.argv[1],'w',zipfile.ZIP_DEFLATED)
for f in sorted(os.listdir('.')): z.write(f)
z.close()" "$OUT/gerbers.zip" )

# BOM grouped by part; parts without an LCSC number (antenna copper, UPDI pads, power symbols) are
# not placed by JLCPCB and are dropped.
"$KCLI" sch export bom -o "$TMP/bom.csv" \
  --fields 'Value,Reference,${FOOTPRINT_NAME},LCSC' --labels 'Comment,Designator,Footprint,LCSC Part #' \
  --group-by 'Value,${FOOTPRINT_NAME},LCSC' --ref-range-delimiter '' --exclude-dnp "$SCH"
"$KCLI" pcb export pos -o "$TMP/pos.csv" --format csv --units mm --side both --exclude-dnp "$PCB"
python3 - "$TMP/bom.csv" "$TMP/pos.csv" "$OUT/bom_jlc.csv" "$OUT/cpl_jlc.csv" <<'PY'
import csv, sys
bom_in, pos_in, bom_out, cpl_out = sys.argv[1:5]
rows, by = [], {}
for r in csv.DictReader(open(bom_in, encoding='utf-8')):
    if not r['LCSC Part #'].strip():
        continue
    k = r['LCSC Part #'].strip()
    if k in by:   # same part on two footprint names (LED1-20 + LED22): one line, or JLCPCB flags it
        by[k]['Designator'] += ',' + r['Designator']
    else:
        by[k] = r; rows.append(r)
placed = {d.strip() for r in rows for d in r['Designator'].split(',')}
with open(bom_out, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, ['Comment', 'Designator', 'Footprint', 'LCSC Part #']); w.writeheader(); w.writerows(rows)
with open(cpl_out, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
    n = 0
    for r in csv.DictReader(open(pos_in, encoding='utf-8')):
        if r['Ref'] in placed:
            w.writerow([r['Ref'], r['PosX'] + 'mm', r['PosY'] + 'mm', 'Top' if r['Side'] == 'top' else 'Bottom', r['Rot']]); n += 1
print(f'BOM lines {len(rows)}, parts {len(placed)}, CPL rows {n}')
PY
ls -la "$OUT"
