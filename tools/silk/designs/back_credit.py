#!/usr/bin/env python3
"""BACK CREDIT - retro credit + licence notice for the back (B.SilkS) of the NFC business card.

Replaces Wilson Harper's "Made by Wilson Harper <heart>" (bottom-right as seen from the back) with
a BBS-style credit block, and adds a shell-prompt source line in the free strip under the parts
list. The original designer's credit is KEPT (CERN-OHL-S-2.0 requires retaining notices), and
his heart survives as a pixel heart.

Seen from the back:

    U1 ATtiny816 | D1 TVS DIODE      ORIG. DESIGN
    -------------+------------       WILSON HARPER <3
    U2 NTAG I2C+ | Q1 P-MOSFET       REMIX:
                 |                   AARON PURSELL
                                     ==============
                                     OPEN HW
    > SRC: GITHUB.COM/NASTEA1/NFC_CARD#   CERN-OHL-S-2.0

Board: BLACK soldermask, WHITE silkscreen (white = phosphor). Font: 5-row pixel font
(3x5 cells; M/W 5 px, I . : 1 px) at px = 0.24 mm -> 1.2 mm cap height, 0.24 mm strokes and
0.24 mm counters (JLCPCB: >= 1.0 mm text, >= 0.16 mm features). Every new piece also keeps
>= 0.30 mm from the existing back silk that stays (checked by clearance(); S.check cannot see
top-level gr_* silk).

Coordinates: everything is laid out in BACK-VIEW mm (u = left->right as seen from the back,
y down) and mirrored ONCE, as a whole, with S.mirror_x(pieces, CX) into board coordinates.

Removal: REMOVE_BACK(item) (geom.json items) and back_remover(head, block_text) (board text,
for S.apply) both select exactly the top-level B.SilkS graphics lying entirely inside
OLD_BACK_CREDIT - the 20 polygons of "Made by / Wilson / Harper / <heart>".

Run:  cd /root/nfc_card/tools/silk && /root/nfc-tools/.venv/bin/python -s designs/back_credit.py
"""
import json
import os
import re
import sys

sys.path.insert(0, "/root/nfc_card/tools/silk")
import silklib as S  # noqa: E402

OUT = "/root/.claude/jobs/5ff251a4/tmp/nfc/out"
L = "B.SilkS"

# ---------------------------------------------------------------- removal of the old credit
# Board coordinates (x0, y0, x1, y1). The 20 glyph polygons span x 129.92..141.46,
# y 102.48..109.50. Nearest neighbours that must stay: LED Matrix box (bottom y 100.90), the
# parts-list rule (starts x 143.32), "DIODE"/"MOSFET" glyphs (x >= 143.99), trace art (x <= 128.74).
OLD_BACK_CREDIT = (129.0, 101.5, 142.5, 110.5)
_COORD = re.compile(r'\((?:xy|start|end|mid|center|at) (-?[\d.]+) (-?[\d.]+)')


def _in_credit(pts):
    x0, y0, x1, y1 = OLD_BACK_CREDIT
    return bool(pts) and all(x0 <= x <= x1 and y0 <= y <= y1 for x, y in pts)


def REMOVE_BACK(item):
    """Predicate over geom.json gr['B.SilkS'] items: True for the old 'Made by Wilson Harper' art."""
    return _in_credit(item['pts'])


def back_remover(head, text):
    """S.apply remover: top-level gr_* on B.SilkS entirely inside OLD_BACK_CREDIT."""
    if not head.startswith('gr_') or '(layer "B.SilkS")' not in text:
        return False
    return _in_credit([(float(a), float(b)) for a, b in _COORD.findall(text)])


# ---------------------------------------------------------------- 5-row pixel font
# Mostly 3x5 cells; proportional where a 3-px cell hurts legibility: M and W are 5 px wide
# (a 3-px W reads as U/H at 1.2 mm), I . : are 1 px wide. Tracking = 1 px.
F35 = {
    'A': "### #.# ### #.# #.#",
    'B': "##. #.# ##. #.# ##.",
    'C': "### #.. #.. #.. ###",
    'D': "##. #.# #.# #.# ##.",
    'E': "### #.. ##. #.. ###",
    'G': "### #.. #.# #.# ###",
    'H': "#.# #.# ### #.# #.#",
    'I': "# # # # #",
    'F': "### #.. ##. #.. #..",
    'L': "#.. #.. #.. #.. ###",
    'M': "#...# ##.## #.#.# #...# #...#",
    'N': "##. #.# #.# #.# #.#",
    'O': "### #.# #.# #.# ###",
    'P': "##. #.# ##. #.. #..",
    'R': "##. #.# ##. #.# #.#",
    'S': ".## #.. .#. ..# ##.",
    'T': "### .#. .#. .#. .#.",
    'U': "#.# #.# #.# #.# ###",
    'W': "#...# #...# #.#.# ##.## #...#",
    'X': "#.# #.# .#. #.# #.#",
    '0': "### #.# #.# #.# ###",
    '1': ".#. ##. .#. .#. ###",
    '2': "##. ..# .#. #.. ###",
    '.': ". . . . #",
    ':': ". # . # .",
    '-': "... ... ### ... ...",
    '/': "..# ..# .#. #.. #..",
    '_': "... ... ... ... ###",
    '>': "#.. .#. ..# .#. #..",
    ' ': "... ... ... ... ...",
    '#': "### ### ### ### ###",   # block cursor
}
F35 = {k: v.split() for k, v in F35.items()}
HEART = [".#.#.", "#####", "#####", ".###.", "..#.."]
PX = 0.24                 # pixel = stroke = counter
CAP = 5 * PX              # 1.2 mm


def text_w(s, px=PX):
    return (sum(len(F35[c][0]) for c in s) + len(s) - 1) * px


def text(s, u, y, px=PX):
    """Pixel text (5 rows, proportional), top-left at back-view (u, y)."""
    rows = [''] * 5
    for i, ch in enumerate(s):
        for r in range(5):
            rows[r] += F35[ch][r] + ('.' if i < len(s) - 1 else '')
    return S.bitmap(rows, u, y, px, L)


# ---------------------------------------------------------------- layout (back-view mm)
def layout(g):
    ex0, ey0, ex1, ey1 = S._edge_bbox(g)
    cx = (ex0 + ex1) / 2                       # 152.155: mirror axis
    bv = lambda x: 2 * cx - x                  # board x <-> back-view u
    # left edge of the parts list (the "U1"/"U2" glyphs) in back-view, to align the strip
    rest = [i for i in g['gr']['B.SilkS'] if not REMOVE_BACK(i)]
    u2 = [i for i in rest if i['kind'] == 'poly' and all(107.0 < p[1] < 109.6 for p in i['pts'])]
    strip_u0 = min(bv(p[0]) for i in u2 for p in i['pts'])

    pcs = []
    # credit column: right of the parts list. Free: u 161.0..175.4, y 101.2..112.7
    cu0 = 161.45
    lines = ["ORIG. DESIGN", "WILSON HARPER", "REMIX:", "AARON PURSELL", None, "OPEN HW", "CERN-OHL-S-2.0"]
    # Top = 101.6 (0.4 below the LED Matrix box). Bottom row top = 110.70 so the row ends at 111.90,
    # >= 0.30 from the upward trace-art arrow tip under "2.0" (y ~112.2 at u 172.9..174.0).
    # The 6 inter-row gaps are spread evenly between the two.
    y, last_y = 101.6, 110.70
    rule_t, rule_g = 0.2, 0.2
    gap = (last_y - y - 5 * CAP - (2 * rule_t + rule_g)) / 6     # ~0.44 mm
    ys = {}
    for s in lines:
        if s is None:                         # '═══' double rule, full column width
            w = max(text_w(t) for t in lines if t)
            pcs += [S.rect(cu0, y, w, rule_t, L), S.rect(cu0, y + rule_t + rule_g, w, rule_t, L)]
            y += 2 * rule_t + rule_g + gap
            continue
        pcs += text(s, cu0, y)
        ys[s] = y
        if s == "WILSON HARPER":              # his heart, kept as a pixel heart
            pcs += S.bitmap(HEART, cu0 + text_w(s) + PX, y, PX, L)
        y += CAP + gap
    col_bottom = y - gap
    # source line: shell prompt + block cursor, under the parts list. Its own row: top 110.85 is
    # 0.30 from the rounded end of the parts-list divider, bottom 112.05 is 0.30 above the
    # trace art under it (y 112.35 at u 155..159); 0.15 mm lower than the column's last row.
    src = "> SRC: GITHUB.COM/NASTEA1/NFC_CARD"
    sy = 110.85
    pcs += text(src, strip_u0, sy)
    pcs += S.bitmap(["###"] * 5, strip_u0 + text_w(src) + 2 * PX, sy, PX, L)
    info = {'cx': cx, 'col_u': [cu0, round(cu0 + text_w("WILSON HARPER") + 6 * PX, 3)],
            'col_y': [101.6, round(col_bottom, 3)], 'strip_u': [round(strip_u0, 3),
            round(strip_u0 + text_w(src) + 5 * PX, 3)], 'strip_y': [round(sy, 3), round(sy + CAP, 3)],
            'cap_mm': CAP, 'px_mm': PX}
    return S.mirror_x(pcs, cx), info


def build_back(mask='black'):
    """B.SilkS pieces (board coordinates) for the back credit. Designed for the black mask."""
    return layout(S.load_geom())[0]


# ---------------------------------------------------------------- verification helpers
def clearance(g, pieces, clr=0.3, scale=40):
    """Min distance check of new art vs. the existing back silk that stays (S.check cannot see
    top-level gr_* silk). Returns px of art within clr mm of kept silk, and the min distance."""
    import numpy as np, cv2
    ex0, ey0, ex1, ey1 = S._edge_bbox(g)
    W, H = int((ex1 - ex0) * scale) + 1, int((ey1 - ey0) * scale) + 1
    P = lambda p: (int(round((p[0] - ex0) * scale)), int(round((p[1] - ey0) * scale)))
    occ = np.zeros((H, W), np.uint8)
    for i in g['gr']['B.SilkS']:
        if REMOVE_BACK(i):
            continue
        ps = S._bez(*i['pts']) if i['kind'] == 'curve' and len(i['pts']) == 4 else i['pts']
        a = np.array([P(p) for p in ps], np.int32)
        if i['fill'] and len(ps) > 2:
            cv2.fillPoly(occ, [a], 255)
            if i['w']:
                cv2.polylines(occ, [a], True, 255, max(1, int(round(i['w'] * scale))))
        elif len(ps) > 1:
            cv2.polylines(occ, [a], False, 255, max(1, int(round((i['w'] or 0.12) * scale))))
    art = np.zeros_like(occ)
    for pc in pieces:
        cv2.fillPoly(art, [np.array([P(p) for p in pc['pts']], np.int32)], 255)
    dist = cv2.distanceTransform(255 - occ, cv2.DIST_L2, 5) / scale
    near = (art > 0) & (dist < clr)
    return {'clear_mm': clr, 'px_too_close': int(near.sum()),
            'min_dist_mm': round(float(dist[art > 0].min()), 3)}


def main():
    g = S.load_geom()
    pieces, info = layout(g)
    os.makedirs(OUT, exist_ok=True)
    out = os.path.join(OUT, 'back_black.png')
    S.render(g, pieces, 'back', 'black', 20, out, drop_back=REMOVE_BACK)
    # zoom of the credit region (back view)
    ex0, ey0, ex1, ey1 = S._edge_bbox(g)
    big = S.render(g, pieces, 'back', 'black', 40, drop_back=REMOVE_BACK)
    W = big.size[0]
    Pz = lambda x, y: (W - (x - ex0 + 2.0) * 40, (y - ey0 + 2.0) * 40)
    a, b = Pz(184.0, 99.5), Pz(126.0, 114.0)
    zoom = os.path.join(OUT, 'back_black_zoom.png')
    big.crop((int(a[0]), int(a[1]), int(b[0]), int(b[1]))).save(zoom)
    removed = [n for n, i in enumerate(g['gr']['B.SilkS']) if REMOVE_BACK(i)]
    rp = [p for n in removed for p in g['gr']['B.SilkS'][n]['pts']]
    src = open(S.PCB_DEFAULT, encoding='utf-8').read()
    _, n_txt = S.apply(src, [], back_remover)
    rep = {
        'removed_geom_items': len(removed), 'removed_idx': removed,
        'removed_bbox': [round(min(p[0] for p in rp), 3), round(min(p[1] for p in rp), 3),
                         round(max(p[0] for p in rp), 3), round(max(p[1] for p in rp), 3)],
        'removed_board_blocks': n_txt,
        'pieces': len(pieces), 'bbox_board': [round(v, 3) for v in S.bbox(pieces)], 'info': info,
        'dfm': S.check(g, pieces, 'back'),
        'clearance_vs_kept_silk': clearance(g, pieces),
        'renders': [out, zoom],
    }
    print(json.dumps(rep, indent=1))


if __name__ == '__main__':
    main()
