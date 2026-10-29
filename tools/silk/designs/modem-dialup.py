#!/usr/bin/env python3
"""MODEM DIAL-UP - retro front silkscreen for the NFC business card (black mask, white silk).

Concept: a 14.4k modem session captured on a phosphor terminal.
  - ANSI-Shadow "STAXXLOGIX" marquee (full-cell blocks + box-drawing shadow strokes)
  - a double-line '═══' rule
  - the session log: ATDT <number> / CONNECT 14400 / LOGIN: <name> / HOST / MAIL / TEL
  - a C:\\> prompt with a block cursor
  - the QR (inverted: white silk = quiet zone + light modules, bare black mask = dark modules)
    inside a double-line box whose borders read "SCAN" and "CARRIER DETECT" (the reworded
    NO CARRIER box from the BBS boot screen).

Everything is simple filled rectangles in board mm (front view, y down) on F.SilkS.

Run:  cd /root/nfc_card/tools/silk && /root/nfc-tools/.venv/bin/python -s designs/modem-dialup.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import silklib as S  # noqa: E402

URL = "https://staxxlogix.com/"
OUT = S.OUT_DIR
NAME = "modem-dialup"
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


# ------------------------------------------------------------------ layout
def layout(mask='black'):
    E = 0.03  # float guard against the area boundary
    X0, Y0, X1, Y1 = (v + (E if i < 2 else -E) for i, v in enumerate(S.FRONT_AREA))
    W = X1 - X0
    pcs = []
    info = {}

    # -- ANSI-Shadow marquee
    rows = ansi_rows("STAXXLOGIX")
    cols = len(rows[0])
    cw = 0.68
    chh = 1.15
    mx = X0 + (W - cols * cw) / 2
    my = Y0 + 0.2
    pcs += ansi(rows, mx, my, cw, chh, t=0.24, g=0.0, double_h=False)
    info.update(ansi_cols=cols, cell=(cw, chh), logo_w=round(cols * cw, 2))
    y = my + 6 * chh

    # -- ═══ rule
    t, g = 0.22, 0.22
    y += 0.8
    pcs += dbl_hline(X0, X1, y, t, g)
    y += 2 * t + g + 1.0

    # -- QR box (right)
    module, quiet = 0.5, 4
    qr_probe, meta = S.qr_pieces(URL, 0, 0, module, quiet=quiet, invert=True, error='q')
    n = meta['modules']
    qs = (n + 2 * quiet) * module           # white square incl. quiet zone
    gapq = 0.5                               # black mask between quiet zone and frame
    band = 2 * t + g
    bw = qs + 2 * (gapq + band)
    lpx = 0.2
    over = (7 * lpx - band) / 2              # label overhang beyond the border band
    bx = X1 - bw
    by = Y1 - over - bw
    pcs += dbl_box(bx, by, bw, bw, t, g, top="SCAN", bot="CARRIER DETECT", px=lpx)
    sx, sy = bx + band + gapq, by + band + gapq
    qr, meta = S.qr_pieces(URL, sx + quiet * module, sy + quiet * module, module, quiet=quiet,
                           invert=True, error='q')
    pcs += qr
    info.update(qr=meta, qr_square=round(qs, 2), qr_box=(round(bx, 2), round(by, 2), round(bw, 2)))

    # -- modem front-panel lamps, one row level with the ATDT line, justified to the QR box
    #    width: [lamp] LABEL ...  AA (auto-answer) is dark - we dialled out.
    lamps = [("AA", 0), ("CD", 1), ("RD", 1), ("SD", 1)]
    lw, lh, lt, lg = 1.0, 0.8, 0.2, 0.35
    item_w = [lw + lg + text_w(nm, lpx) for nm, _ in lamps]
    sp = (bw - sum(item_w)) / (len(lamps) - 1)
    ltop = y + (7 * 0.23 - 7 * lpx) / 2          # centre on the 1.61 mm ATDT cap
    lx = bx
    for (nm, on), iw in zip(lamps, item_w):
        ly_ = ltop + (7 * lpx - lh) / 2
        if on:
            pcs.append(S.rect(lx, ly_, lw, lh))
        else:
            pcs += S.frame(lx, ly_, lw, lh, lt)
        pcs += text(nm, lx + lw + lg, ltop, lpx)
        lx += iw + sp
    lamp_bot = ltop + 7 * lpx
    assert sp >= 1.0 and lamp_bot + 1.0 <= by - over, 'lamp row crowded'
    info['lamps_gap_to_box'] = round(by - over - lamp_bot, 2)

    # -- session log (left column)
    lx0, lx1 = X0, bx - 1.2
    spx = 0.23        # small text pixel -> cap 1.61 mm
    bpx = 0.40        # name pixel -> cap 2.80 mm
    # groups of (text, px); gaps: a inside a group, 2a between groups, solved to fill the column
    groups = [[("NFC TAP TO SAVE", spx), ("CONNECT 14400", spx)],
              [("LOGIN:", spx), ("AARON PURSELL", bpx)],
              [("HOST: STAXXLOGIX.COM", spx), ("MAIL: AP@STAXXLOGIX.COM", spx),
               ("WWW:  STAXXLOGIX.COM", spx)],
              [("C:\\>", spx)]]
    hsum = sum(7 * px for gr in groups for _, px in gr)
    n_in = sum(len(gr) - 1 for gr in groups)
    n_between = len(groups) - 1
    col_h = Y1 - y
    a = (col_h - hsum) / (n_in + 2 * n_between)
    lines = []
    ly = y
    for gi, gr in enumerate(groups):
        for li, (s, px) in enumerate(gr):
            pcs += text(s, lx0, ly, px)
            lines.append((s, text_w(s, px)))
            if s.startswith("C:"):
                # block cursor one cell after the prompt
                pcs.append(S.rect(lx0 + 5 * ADV * px, ly, 5 * px, 7 * px))
            ly += 7 * px + (a if li < len(gr) - 1 else 2 * a)
    ly -= 2 * a
    py = ly - 7 * spx
    info['line_gap'] = round(a, 2)
    info['left_col'] = (round(lx0, 2), round(lx1, 2))
    info['widest_line'] = max(lines, key=lambda a: a[1])
    for s, w_ in lines:
        assert lx0 + w_ <= lx1 + 1e-9, f'line too wide for column: {s!r} {w_:.2f}'
    assert abs(ly - Y1) < 1e-6 and a >= 0.6, f'column fill wrong: {ly:.2f} gap {a:.2f}'
    info['min_cap_mm'] = round(7 * min(spx, lpx), 2)
    return pcs, info


def build(mask='black'):
    pcs, _ = layout(mask)
    for p in pcs:
        xs = [q[0] for q in p['pts']]
        ys = [q[1] for q in p['pts']]
        w, h = max(xs) - min(xs), max(ys) - min(ys)
        assert min(w, h) >= MIN_DIM - 1e-9, f'rect below {MIN_DIM} mm: {w:.3f} x {h:.3f} at {p["pts"][0]}'
    return pcs


def main():
    g = S.load_geom()
    pcs, info = layout('black')
    pcs = build('black')
    os.makedirs(OUT, exist_ok=True)
    out = os.path.join(OUT, f"{NAME}_front_black.png")
    img = S.render(g, pcs, side='front', mask='black', scale=20, out=out)
    # zoomed crop of the art area for review
    ex0, ey0, _, _ = S._edge_bbox(g)
    X0, Y0, X1, Y1 = S.FRONT_AREA
    z = S.render(g, pcs, side='front', mask='black', scale=60)
    pad = 2.0
    box = [int((v - o + pad) * 60) for v, o in ((X0 - 1, ex0), (Y0 - 1, ey0), (X1 + 1, ex0), (Y1 + 1, ey0))]
    zoom = os.path.join(OUT, f"{NAME}_front_black_zoom.png")
    z.crop(box).save(zoom)
    chk = S.check(g, pcs, 'front', S.FRONT_AREA)
    qr = S.qr_verify(g, pcs, URL, mask='black')
    qr20 = S.qr_verify(g, pcs, URL, mask='black', scale=20, spread_mm=(0.0, 0.05, -0.05, 0.08, -0.08))
    rep = {'render': out, 'zoom': zoom, 'check': chk, 'qr_verify': qr, 'qr_verify_scale20': qr20,
           'qr_ok': all(v == URL for v in qr.values()), 'info': info}
    print(json.dumps(rep, indent=1, default=str))


if __name__ == '__main__':
    main()
