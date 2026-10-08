#!/usr/bin/env python3
"""FINAL - retro front silkscreen for Aaron Pursell / StaxxLogix (black mask, white silk).

Winner of the three concepts: MODEM DIAL-UP (a 14.4k modem session on a phosphor terminal),
with the judges' grafts:
  - the phone number appears ONCE, as menu item [3] ATDT 210-848-8420 (the modem dial string);
    the separate ATDT line and the TEL: line are gone
  - numbered BBS menu [1]/[2]/[3] (registry.js) for site / mail / phone, values only so the
    lines fit the column at a LARGER pixel (0.25 mm -> 1.75 mm caps, was 0.23 / 1.61)
  - one texture only: a short █▓▒░ scanline fade after CONNECT 14400
  - LOGIN: becomes an inline-label double rule '══ LOGIN ═══' (the boot.js rule motif)
  - modem lamps (AA outline, CD/RD/SD lit) level with CONNECT, clear of the QR box
  - logo cells shrunk to 0.66 x 1.12 mm and dropped 0.55 mm below the area top (less top-heavy)
  - kept: ANSI-Shadow STAXXLOGIX + full-width '═══' rule, slashed zero, the SCAN / CARRIER
    DETECT double-line QR box, inverted v3-Q QR (0.5 mm modules, 4-module quiet zone), C:\\> + █
  - no title bar, no 'EST.' year, no 'MAIN MENU'

Everything is simple filled rectangles in board mm (front view, y down) on F.SilkS. The back
(B.SilkS) credit comes from back_credit.py (build_back / back_remover).

Run:  cd /root/nfc_card/tools/silk && /root/nfc-tools/.venv/bin/python -s designs/final.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import silklib as S  # noqa: E402
from back_credit import build_back, back_remover, REMOVE_BACK, clearance  # noqa: E402,F401

URL = "https://staxxlogix.com/"
OUT = S.OUT_DIR
NAME = "final"
L = "F.SilkS"
MIN_DIM = 0.2  # our own hard floor for every emitted rectangle (DFM disc is ~0.175 mm)

# ------------------------------------------------------------------ 5x7 pixel font
# '0' is slashed so it never reads as the O in LOGIX.
F57 = {
    'A': [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'B': ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    'C': [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    'D': ["###..", "#..#.", "#...#", "#...#", "#...#", "#..#.", "###.."],
    'E': ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    'F': ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    'G': [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."],
    'H': ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'I': [".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."],
    'J': ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    'K': ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    'L': ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    'M': ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    'N': ["#...#", "#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#"],
    'O': [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'P': ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    'Q': [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    'R': ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    'S': [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    'T': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    'U': ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'V': ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    'W': ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    'X': ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    'Y': ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    'Z': ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    '0': [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    '1': ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    '2': [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    '3': ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
    '4': ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    '5': ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    '6': [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."],
    '7': ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    '8': [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    '9': [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."],
    '.': [".....", ".....", ".....", ".....", ".....", "..#..", "..#.."],
    ':': [".....", "..#..", "..#..", ".....", "..#..", "..#..", "....."],
    '-': [".....", ".....", ".....", ".###.", ".....", ".....", "....."],
    '/': ["....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."],
    '\\': ["#....", "#....", ".#...", "..#..", "...#.", "....#", "....#"],
    '>': [".#...", "..#..", "...#.", "....#", "...#.", "..#..", ".#..."],
    '_': [".....", ".....", ".....", ".....", ".....", ".....", "#####"],
    '[': ["..###", "..#..", "..#..", "..#..", "..#..", "..#..", "..###"],
    ']': ["###..", "..#..", "..#..", "..#..", "..#..", "..#..", "###.."],
    '@': [".###.", "#...#", "#.###", "#.#.#", "#.###", "#....", ".####"],
    ' ': ["....."] * 7,
    # block cursor (full cell incl. the tracking column is drawn by cursor())
    '#': ["#####"] * 7,
}
ADV = 6  # 5-px glyph + 1-px tracking


def text_w(s, px):
    return (len(s) * ADV - 1) * px


def text(s, x, y, px, layer=L):
    """5x7 pixel text, top-left (x, y), pixel px mm. Returns pieces."""
    out = []
    for i, ch in enumerate(s):
        out += S.bitmap(F57[ch], x + i * ADV * px, y, px, layer)
    return out


# ------------------------------------------------------------------ ANSI Shadow
# figlet "ANSI Shadow" glyphs, 6 rows. S and T copied from the BBS boot screen; the rest drawn
# in the same figlet style.
ANSI = {
    'S': ["███████╗", "██╔════╝", "███████╗", "╚════██║", "███████║", "╚══════╝"],
    'T': ["████████╗", "╚══██╔══╝", "   ██║   ", "   ██║   ", "   ██║   ", "   ╚═╝   "],
    'A': [" █████╗ ", "██╔══██╗", "███████║", "██╔══██║", "██║  ██║", "╚═╝  ╚═╝"],
    'X': ["██╗  ██╗", "╚██╗██╔╝", " ╚███╔╝ ", " ██╔██╗ ", "██╔╝ ██╗", "╚═╝  ╚═╝"],
    'L': ["██╗     ", "██║     ", "██║     ", "██║     ", "███████╗", "╚══════╝"],
    'O': [" ██████╗ ", "██╔═══██╗", "██║   ██║", "██║   ██║", "╚██████╔╝", " ╚═════╝ "],
    'G': [" ██████╗ ", "██╔════╝ ", "██║  ███╗", "██║   ██║", "╚██████╔╝", " ╚═════╝ "],
    'I': ["██╗", "██║", "██║", "██║", "██║", "╚═╝"],
}
# arms of each box-drawing char: (left, right, up, down)
ARMS = {'═': (1, 1, 0, 0), '║': (0, 0, 1, 1), '╗': (1, 0, 0, 1), '╔': (0, 1, 0, 1),
        '╝': (1, 0, 1, 0), '╚': (0, 1, 1, 0)}


def ansi_rows(word):
    rows = [''] * 6
    for ch in word:
        for r in range(6):
            rows[r] += ANSI[ch][r]
    assert len(set(len(r) for r in rows)) == 1, 'ragged ANSI rows'
    return rows


def ansi(rows, x, y, cw, ch, t, g, double_h=True, layer=L):
    """Render ANSI-Shadow rows at (x, y) with cell cw x ch mm.
    '█' fills its cell (runs merged). Box-drawing shadow: horizontal arms are a double line
    (two strokes t, gap g, centred on the cell) when double_h, else one stroke t; vertical arms
    are one stroke t centred in the cell (a double vertical does not fit a ~0.68 mm cell)."""
    out = []
    d = (t + g) / 2 if double_h else 0.0
    hy = [-d, d] if double_h else [0.0]
    for r, row in enumerate(rows):
        c = 0
        while c < len(row):
            if row[c] == '█':
                s = c
                while c + 1 < len(row) and row[c + 1] == '█':
                    c += 1
                out.append(S.rect(x + s * cw, y + r * ch, (c - s + 1) * cw, ch, layer))
            c += 1
        for c, cc in enumerate(row):
            if cc not in ARMS:
                continue
            al, ar, au, ad = ARMS[cc]
            x0, y0 = x + c * cw, y + r * ch
            xc, yc = x0 + cw / 2, y0 + ch / 2
            # horizontal strokes
            if al or ar:
                hx0 = x0 if al else xc - t / 2
                hx1 = x0 + cw if ar else xc + t / 2
                for o in hy:
                    out.append(S.rect(hx0, yc + o - t / 2, hx1 - hx0, t, layer))
            # vertical stroke
            if au or ad:
                vy0 = y0 if au else yc - d - t / 2
                vy1 = y0 + ch if ad else yc + d + t / 2
                out.append(S.rect(xc - t / 2, vy0, t, vy1 - vy0, layer))
    return out


# ------------------------------------------------------------------ frames / rules
def dbl_hline(x0, x1, y, t, g, layer=L):
    """'═' double line, top edge at y."""
    if x1 - x0 < MIN_DIM:
        return []
    return [S.rect(x0, y, x1 - x0, t, layer), S.rect(x0, y + t + g, x1 - x0, t, layer)]


def dbl_box(x, y, w, h, t, g, top=None, bot=None, px=0.2, pad=0.5, layer=L):
    """'╔═╗ ║ ║ ╚═╝' double-line box, outer top-left (x, y). Optional labels sit centred in the
    top / bottom border, the border broken around them by `pad`."""
    band = 2 * t + g
    out = []
    # verticals (outer + inner), full height of their rectangles
    out.append(S.rect(x, y, t, h, layer))
    out.append(S.rect(x + w - t, y, t, h, layer))
    out.append(S.rect(x + t + g, y + t + g, t, h - 2 * (t + g), layer))
    out.append(S.rect(x + w - 2 * t - g, y + t + g, t, h - 2 * (t + g), layer))

    def border(yb, label, inner_is_lower):
        # outer line spans x..x+w, inner line spans x+t+g .. x+w-t-g
        yo = yb if inner_is_lower else yb + t + g
        yi = yb + t + g if inner_is_lower else yb
        segs_o, segs_i = [(x, x + w)], [(x + t + g, x + w - t - g)]
        lab = []
        if label:
            tw = text_w(label, px)
            lx = x + (w - tw) / 2
            cut = (lx - pad, lx + tw + pad)
            segs_o = [(a, cut[0]) for a, b in segs_o] + [(cut[1], b) for a, b in segs_o]
            segs_i = [(a, cut[0]) for a, b in segs_i] + [(cut[1], b) for a, b in segs_i]
            lab = text(label, lx, yb + band / 2 - 3.5 * px, px, layer)
        res = []
        for a, b in segs_o:
            res.append(S.rect(a, yo, b - a, t, layer))
        for a, b in segs_i:
            res.append(S.rect(a, yi, b - a, t, layer))
        return res + lab

    out += border(y, top, True)
    out += border(y + h - band, bot, False)
    return out


# ------------------------------------------------------------------ texture (used once)
def scan_cell(x, y, w, h, pitch, t=0.2, layer=L):
    """Horizontal scanlines (stroke t) filling a w x h cell, first line at the top edge and last
    at the bottom edge; the actual pitch is >= `pitch`, so every gap is >= pitch - t."""
    n = max(2, int((h - t) / pitch + 1e-9) + 1)
    p = (h - t) / (n - 1)
    return [S.rect(x, y + i * p, w, t, layer) for i in range(n)]


def fade(x0, x1, y, h, layer=L):
    """'█▓▒░' as cells of falling density, left to right (solid, then 50 / 33 / 25 % ink)."""
    out = []
    steps = [None, 0.4, 0.6, 0.8]
    sp = 0.4
    cw = (x1 - x0 - sp * (len(steps) - 1)) / len(steps)
    for i, ptch in enumerate(steps):
        cx = x0 + i * (cw + sp)
        out += [S.rect(cx, y, cw, h, layer)] if ptch is None else scan_cell(cx, y, cw, h, ptch, layer=layer)
    return out


def label_rule(label, x0, x1, y, px, t, g, lead=2.2, pad=0.6, layer=L):
    """'══ LABEL ═════' : a double rule with the label set inline, row top y, cap 7*px."""
    band = 2 * t + g
    ry = y + (7 * px - band) / 2
    tx = x0 + lead + pad
    out = dbl_hline(x0, x0 + lead, ry, t, g, layer)
    out += text(label, tx, y, px, layer)
    out += dbl_hline(tx + text_w(label, px) + pad, x1, ry, t, g, layer)
    return out


# ------------------------------------------------------------------ layout
def layout(mask='black'):
    assert mask == 'black', 'drawn for black soldermask / white silk only (user decision)'
    E = 0.03  # float guard against the area boundary (check() has no tolerance)
    X0, Y0, X1, Y1 = (v + (E if i < 2 else -E) for i, v in enumerate(S.FRONT_AREA))
    W = X1 - X0
    pcs = []
    info = {}

    # -- ANSI-Shadow marquee, dropped below the area top for air under the LED row
    rows = ansi_rows("STAXXLOGIX")
    cols = len(rows[0])
    cw, chh = 0.66, 1.12
    mx = X0 + (W - cols * cw) / 2
    my = Y0 + 0.55
    pcs += ansi(rows, mx, my, cw, chh, t=0.24, g=0.0, double_h=False)
    info.update(ansi_cols=cols, cell=(cw, chh), logo=(round(mx, 2), round(my, 2),
                round(cols * cw, 2), round(6 * chh, 2)))
    y = my + 6 * chh

    # -- ═══ rule
    t, g = 0.22, 0.22
    y += 0.8
    pcs += dbl_hline(X0, X1, y, t, g)
    y += 2 * t + g + 1.0

    # -- QR box (right, bottom-aligned with the area)
    module, quiet = 0.5, 4
    _, meta = S.qr_pieces(URL, 0, 0, module, quiet=quiet, invert=True, error='q')
    n = meta['modules']
    qs = (n + 2 * quiet) * module           # white square incl. quiet zone
    gapq = 0.6                               # bare black mask between quiet zone and frame; the
                                             # SCAN / CARRIER DETECT labels overhang the band by
                                             # 0.37 mm, so 0.6 keeps them >= 0.2 mm off the quiet zone
    band = 2 * t + g
    bw = qs + 2 * (gapq + band)
    lpx = 0.2                                # lamp + border labels: cap 1.4 mm (smallest text)
    over = (7 * lpx - band) / 2              # label overhang beyond the border band
    bx = X1 - bw
    by = Y1 - over - bw
    pcs += dbl_box(bx, by, bw, bw, t, g, top="SCAN", bot="CARRIER DETECT", px=lpx)
    sx, sy = bx + band + gapq, by + band + gapq
    qr, meta = S.qr_pieces(URL, sx + quiet * module, sy + quiet * module, module, quiet=quiet,
                           invert=True, error='q')
    pcs += qr
    info.update(qr=meta, qr_square=(round(sx, 3), round(sy, 3), round(qs, 2)),
                qr_box=(round(bx, 2), round(by, 2), round(bw, 2)))

    # -- left column
    spx = 0.25        # small text pixel -> cap 1.75 mm
    bpx = 0.40        # name pixel -> cap 2.80 mm
    lx0, lx1 = X0, bx - 1.2
    rows_ = [  # (kind, payload, px, group)
        ('connect', "CONNECT 14400", spx, 0),
        ('rule', "LOGIN", spx, 1),
        ('text', "AARON PURSELL", bpx, 1),
        ('text', "[1] STAXXLOGIX.COM", spx, 2),
        ('text', "[2] AP@STAXXLOGIX.COM", spx, 2),
        ('text', "[3] ATDT 210-848-8420", spx, 2),
        ('prompt', "C:\\>", spx, 3),
    ]
    BETWEEN = 1.8     # gap between groups = BETWEEN * gap inside a group
    hsum = sum(7 * r[2] for r in rows_)
    n_in = sum(1 for a, b in zip(rows_, rows_[1:]) if a[3] == b[3])
    n_bt = len(rows_) - 1 - n_in
    col_top = y
    a = (Y1 - col_top - hsum) / (n_in + BETWEEN * n_bt)
    ly = col_top
    widths = []
    for i, (kind, s, px, grp) in enumerate(rows_):
        h = 7 * px
        if kind == 'rule':
            pcs += label_rule(s, lx0, lx1, ly, px, t, g)
            widths.append((s, lx1 - lx0))
        else:
            pcs += text(s, lx0, ly, px)
            widths.append((s, text_w(s, px)))
        if kind == 'connect':
            fx0 = lx0 + text_w(s, px) + 1.25
            fx1 = lx1 - 0.8                       # extra black before the lamp row
            pcs += fade(fx0, fx1, ly, h)
            info['fade'] = (round(fx0, 2), round(fx1, 2))
            connect_y = ly
        if kind == 'prompt':
            pcs.append(S.rect(lx0 + 5 * ADV * px, ly, 5 * px, h))   # block cursor
        if i < len(rows_) - 1:
            ly += h + (a if rows_[i + 1][3] == grp else BETWEEN * a)
        else:
            ly += h
    assert abs(ly - Y1) < 1e-6 and a >= 0.6, f'column fill wrong: {ly:.2f} gap {a:.2f}'
    for s, w_ in widths:
        assert lx0 + w_ <= lx1 + 1e-9, f'line too wide for column: {s!r} {w_:.2f}'
    info.update(line_gap=round(a, 2), group_gap=round(BETWEEN * a, 2),
                left_col=(round(lx0, 2), round(lx1, 2)),
                widest_line=max(widths, key=lambda w: w[1] if w[0] != 'LOGIN' else 0))

    # -- modem front-panel lamps, level with CONNECT, justified to the QR box width.
    #    AA (auto-answer) is an outline - we dialled out; CD / RD / SD lit.
    lamps = [("AA", 0), ("CD", 1), ("RD", 1), ("SD", 1)]
    lw, lh, lt, lg = 1.0, 0.8, 0.2, 0.35
    item_w = [lw + lg + text_w(nm, lpx) for nm, _ in lamps]
    sp = (bw - sum(item_w)) / (len(lamps) - 1)
    ltop = connect_y + (7 * spx - 7 * lpx) / 2      # centred on the CONNECT cap
    lx = bx
    for (nm, on), iw in zip(lamps, item_w):
        ly_ = ltop + (7 * lpx - lh) / 2
        pcs += [S.rect(lx, ly_, lw, lh)] if on else S.frame(lx, ly_, lw, lh, lt)
        pcs += text(nm, lx + lw + lg, ltop, lpx)
        lx += iw + sp
    lamp_bot = ltop + 7 * lpx
    info['lamps_gap_to_box_label'] = round(by - over - lamp_bot, 2)
    info['fade_to_lamps'] = round(bx - info['fade'][1], 2)
    assert sp >= 1.0 and by - over - lamp_bot >= 1.0, 'lamp row crowded'
    info['min_cap_mm'] = round(7 * min(spx, lpx), 2)
    return pcs, info


def build(mask='black'):
    """F.SilkS pieces for the front (black mask, inverted QR)."""
    pcs, _ = layout(mask)
    for p in pcs:
        xs = [q[0] for q in p['pts']]
        ys = [q[1] for q in p['pts']]
        w, h = max(xs) - min(xs), max(ys) - min(ys)
        assert min(w, h) >= MIN_DIM - 1e-9, f'rect below {MIN_DIM} mm: {w:.3f} x {h:.3f} at {p["pts"][0]}'
    return pcs


# ------------------------------------------------------------------ verification
def gap_blobs(g, pieces, side='front', scale=40):
    """Re-run check()'s narrow-gap test and return each gap blob's bbox in board mm, so a gap
    warning can be proven to come only from QR modules touching at their corners."""
    import numpy as np, cv2
    sk = 'F.SilkS' if side == 'front' else 'B.SilkS'
    ex0, ey0, ex1, ey1 = S._edge_bbox(g)
    Wd, Hd = int((ex1 - ex0) * scale) + 1, int((ey1 - ey0) * scale) + 1
    P = lambda p: (int(round((p[0] - ex0) * scale)), int(round((p[1] - ey0) * scale)))
    art = np.zeros((Hd, Wd), np.uint8)
    for pc in pieces:
        if pc['layer'] == sk:
            cv2.fillPoly(art, [np.array([P(p) for p in pc['pts']], np.int32)], 255)
    k = max(3, int(S.MIN_FEATURE * scale) | 1)
    disc = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    gap = cv2.subtract(cv2.morphologyEx(art, cv2.MORPH_CLOSE, disc), art)
    gap = cv2.morphologyEx(gap, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    n, _, st, _ = cv2.connectedComponentsWithStats(gap)
    return [(st[i, 0] / scale + ex0, st[i, 1] / scale + ey0,
             (st[i, 0] + st[i, 2]) / scale + ex0, (st[i, 1] + st[i, 3]) / scale + ey0)
            for i in range(1, n)]


QR_SPREADS = (0.0, 0.05, -0.05, 0.08, -0.08, 0.10, -0.10)


def main():
    g = S.load_geom()
    pcs, info = layout('black')
    pcs = build('black')
    back = build_back('black')
    os.makedirs(OUT, exist_ok=True)
    front_png = os.path.join(OUT, f"{NAME}_front_black.png")
    back_png = os.path.join(OUT, f"{NAME}_back_black.png")
    S.render(g, pcs, side='front', mask='black', scale=20, out=front_png)
    S.render(g, back, side='back', mask='black', scale=20, out=back_png, drop_back=REMOVE_BACK)
    ex0, ey0, _, _ = S._edge_bbox(g)
    X0, Y0, X1, Y1 = S.FRONT_AREA
    z = S.render(g, pcs, side='front', mask='black', scale=60)
    box = [int((v - o + 2.0) * 60) for v, o in ((X0 - 1, ex0), (Y0 - 2, ey0), (X1 + 1, ex0), (Y1 + 2, ey0))]
    zoom = os.path.join(OUT, f"{NAME}_front_black_zoom.png")
    z.crop(box).save(zoom)

    chk = S.check(g, pcs, 'front', S.FRONT_AREA)
    sx, sy, qs = info['qr_square']
    blobs = gap_blobs(g, pcs)
    outside = [b for b in blobs if not (sx <= b[0] and b[2] <= sx + qs and sy <= b[1] and b[3] <= sy + qs)]
    chk_b = S.check(g, back, 'back')
    clr_b = clearance(g, back)
    qr12 = S.qr_verify(g, pcs, URL, mask='black')
    qr20 = S.qr_verify(g, pcs, URL, mask='black', scale=20, spread_mm=QR_SPREADS)
    rep = {'renders': [front_png, back_png, zoom],
           'front_check': chk, 'front_gap_blobs': len(blobs), 'front_gap_blobs_outside_qr': outside,
           'back_check': chk_b, 'back_clearance': clr_b,
           'qr_verify_default': qr12, 'qr_verify_scale20': qr20,
           'qr_ok': all(qr20[str(s)] == URL for s in (0.0, 0.05, -0.05, 0.08, -0.08)),
           'dfm_ok': not chk['errors'] and not outside and not chk_b['errors'] and clr_b['px_too_close'] == 0,
           'front_pieces': len(pcs), 'back_pieces': len(back), 'info': info}
    print(json.dumps(rep, indent=1, default=str))


if __name__ == '__main__':
    main()
