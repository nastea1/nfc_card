#!/usr/bin/env python3
"""Round-trip check of the board written by apply_final.py.

Usage (after apply_final.py):
  cd /root/nfc_card/tools/silk
  /root/nfc-tools/.venv/bin/python -s geom.py "../../hardware/Business Card v2.kicad_pcb" OUT/geom_final.json
  /root/nfc-tools/.venv/bin/python -s verify_final.py ORIG_GEOM.json OUT/geom_final.json OUT/

Checks, all from the WRITTEN file's geometry:
  - every non-silk item (pads, tracks, zones, footprints, footprint graphics, Edge.Cuts, F/B.Mask)
    is identical to the original board, count AND content
  - F/B.SilkS counts = original - removed + added, and the new polygons equal the design to 1e-6 mm
  - renders both sides (drop_old_front=False, i.e. exactly what is in the file) and decodes the QR
    straight from the round-trip front PNG, plus qr_verify with ink spread at 20 px/mm
  - S.check on the written front polygons

Note: silklib.render()/qr_verify() default to drop_old_front=True, which drops EVERY F.SilkS
graphic inside OLD_FRONT_ART - including the new art once it is in the board. So
qr_verify(geom_final, [], ...) always returns None; the new polygons are re-fed as pieces instead.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'designs'))
import silklib as S  # noqa: E402
import final  # noqa: E402
from back_credit import build_back  # noqa: E402

URL = final.URL


def counts(g):
    c = {k: len(g[k]) for k in ('pads', 'tracks', 'zones', 'footprints', 'fp_silk')}
    c.update({f'gr[{k}]': len(v) for k, v in sorted(g['gr'].items())})
    return c


def main(orig_path, final_path, out_dir):
    import numpy as np, cv2
    g0, g1 = S.load_geom(orig_path), S.load_geom(final_path)
    c0, c1 = counts(g0), counts(g1)
    diff = {k: (c0.get(k), c1.get(k)) for k in sorted(set(c0) | set(c1)) if c0.get(k) != c1.get(k)}
    deep = {k: g0[k] == g1[k] for k in ('pads', 'tracks', 'zones', 'footprints', 'fp_silk')}
    deep.update({f'gr[{L}]': g0['gr'].get(L) == g1['gr'].get(L)
                 for L in set(g0['gr']) | set(g1['gr']) if 'SilkS' not in L})

    k4 = lambda pts: tuple((round(x, 4), round(y, 4)) for x, y in pts)  # noqa: E731

    def new_items(L):
        old = set(k4(i['pts']) for i in g0['gr'][L])
        return [{'layer': L, 'pts': i['pts']} for i in g1['gr'][L] if k4(i['pts']) not in old]

    def max_err(written, design):
        a = sorted(written, key=lambda p: k4(p['pts']))
        b = sorted(design, key=lambda p: k4(p['pts']))
        if len(a) != len(b):
            return f'count {len(a)} != {len(b)}'
        return max(abs(p - q) for A, B in zip(a, b) for pa, pb in zip(A['pts'], B['pts']) for p, q in zip(pa, pb))

    front_d, back_d = final.build('black'), build_back('black')
    nf, nb = new_items('F.SilkS'), new_items('B.SilkS')
    fpng = os.path.join(out_dir, 'roundtrip_front_black.png')
    bpng = os.path.join(out_dir, 'roundtrip_back_black.png')
    S.render(g1, [], 'front', 'black', 20, fpng, drop_old_front=False)
    S.render(g1, [], 'back', 'black', 20, bpng, drop_old_front=False)
    gray = cv2.cvtColor(cv2.imread(fpng), cv2.COLOR_BGR2GRAY)
    png_decode = cv2.QRCodeDetector().detectAndDecode(cv2.GaussianBlur(gray, (3, 3), 0))[0] or None
    rep = {
        'counts_orig': c0, 'counts_final': c1, 'count_diff': diff,
        'only_silk_counts_changed': all('SilkS' in k for k in diff),
        'nonsilk_content_identical': deep,
        'removed_F': c0['gr[F.SilkS]'] - (c1['gr[F.SilkS]'] - len(nf)),
        'removed_B': c0['gr[B.SilkS]'] - (c1['gr[B.SilkS]'] - len(nb)),
        'added_F': len(nf), 'added_B': len(nb),
        'front_max_coord_err_mm': max_err(nf, front_d), 'back_max_coord_err_mm': max_err(nb, back_d),
        'qr_decoded_from_roundtrip_png': png_decode,
        'qr_verify_written_s20': S.qr_verify(g1, nf, URL, mask='black', scale=20,
                                             spread_mm=(0.0, 0.05, -0.05, 0.08, -0.08)),
        'check_front_written': S.check(g1, nf, 'front', S.FRONT_AREA),
        'renders': [fpng, bpng],
    }
    print(json.dumps(rep, indent=1, default=str))


if __name__ == '__main__':
    main(*sys.argv[1:4])
