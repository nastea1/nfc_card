#!/usr/bin/env python3
"""BBS LOGIN - retro front silkscreen for the NFC business card (black mask, white silk).

A green-phosphor BBS login screen translated to one-colour silk: a double-line title bar,
an ANSI-Shadow "STAXXLOGIX" marquee, SYSOP line, numbered menu, a C:\\> prompt with a block
cursor, and an inverted QR (white silk = quiet zone + light modules) in its own double-line box.

Run:  cd /root/nfc_card/tools/silk && /root/nfc-tools/.venv/bin/python -s designs/bbs-login.py
"""
import json
import os
import sys

sys.path.insert(0, "/root/nfc_card/tools/silk")
import silklib as S  # noqa: E402

URL = "https://staxxlogix.com/"
OUT = "/root/.claude/jobs/5ff251a4/tmp/nfc/out"
L = "F.SilkS"

# ---------------------------------------------------------------- 5x7 pixel font
F57 = {
    'A': [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'B': ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    'C': [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    'D': ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    'E': ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    'F': ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    'G': [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".####"],
    'H': ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'I': [".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."],
    'J': ["..###", "...#.", "...#.", "...#.", "#..#.", "#..#.", ".##.."],
    'K': ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    'L': ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    'M': ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    'N': ["#...#", "#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#"],
    'O': [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'P': ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    'Q': [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    'R': ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    'S': [".###.", "#...#", "#....", ".###.", "....#", "#...#", ".###."],
    'T': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    'U': ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'V': ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    'W': ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."],
    'X': ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    'Y': ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    'Z': ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    '0': [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    '1': ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    '2': [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    '3': ["#####", "...#.", "..#..", "...#.", "....#", "#...#", ".###."],
    '4': ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    '5': ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    '6': ["..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."],
    '7': ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    '8': [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    '9': [".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."],
    '.': [".....", ".....", ".....", ".....", ".....", ".##..", ".##.."],
    ':': [".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."],
    '-': [".....", ".....", ".....", "#####", ".....", ".....", "....."],
    '/': ["....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."],
    '\\': ["#....", "#....", ".#...", "..#..", "...#.", "....#", "....#"],
    '>': ["#....", ".#...", "..#..", "...#.", "..#..", ".#...", "#...."],
    '_': [".....", ".....", ".....", ".....", ".....", ".....", "#####"],
    '[': [".###.", ".#...", ".#...", ".#...", ".#...", ".#...", ".###."],
    ']': [".###.", "...#.", "...#.", "...#.", "...#.", "...#.", ".###."],
    '@': [".###.", "#...#", "#.###", "#.#.#", "#.###", "#....", ".####"],
    ' ': ["....."] * 7,
}
ADV = 6  # 5 px glyph + 1 px tracking


def text_w(s, px):
    return (len(s) * ADV - 1) * px


def text(s, x, y, px, layer=L):
    """5x7 pixel text, top-left at (x, y); returns pieces."""
    out = []
    for i, ch in enumerate(s):
        out += S.bitmap(F57[ch], x + i * ADV * px, y, px, layer)
    return out


# ---------------------------------------------------------------- ANSI Shadow marquee
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


def marquee_rows(word, sep=' '):
    rows = [''] * 6
    for c, ch in enumerate(word):
        for r in range(6):
            rows[r] += (sep if c else '') + ANSI[ch][r]
    return rows


# which sides of a cell each box-drawing char connects to (L, R, U, D)
BOX = {'═': 'LR', '║': 'UD', '╔': 'RD', '╗': 'LD', '╚': 'RU', '╝': 'LU'}


def ansi(rows, x, y, cw, ch, t, scan=0.0, layer=L):
    """Render ANSI-Shadow rows. '█' = filled cell (optionally split by a `scan` mm dark
    scanline at every row boundary); box chars = single strokes of width t on the cell centre
    lines (the double lines of a terminal font do not fit a 0.6 mm cell at 0.2 mm silk)."""
    out = []
    for r, row in enumerate(rows):
        c = 0
        while c < len(row):
            if row[c] == '█':
                s = c
                while c + 1 < len(row) and row[c + 1] == '█':
                    c += 1
                y0 = y + r * ch + (scan / 2 if r else 0)
                y1 = y + (r + 1) * ch - (scan / 2 if r < len(rows) - 1 else 0)
                out.append(S.rect(x + s * cw, y0, (c - s + 1) * cw, y1 - y0, layer))
            elif row[c] in BOX:
                cx, cy = x + (c + 0.5) * cw, y + (r + 0.5) * ch
                for side in BOX[row[c]]:
                    if side == 'L':
                        out.append(S.rect(x + c * cw, cy - t / 2, cw / 2 + t / 2, t, layer))
                    elif side == 'R':
                        out.append(S.rect(cx - t / 2, cy - t / 2, cw / 2 + t / 2, t, layer))
                    elif side == 'U':
                        out.append(S.rect(cx - t / 2, y + r * ch, t, ch / 2 + t / 2, layer))
                    elif side == 'D':
                        out.append(S.rect(cx - t / 2, cy - t / 2, t, ch / 2 + t / 2, layer))
            c += 1
    return out


# ---------------------------------------------------------------- double-line boxes
def dbl_box(x, y, w, h, t, g, cut_top=None, cut_bot=None, layer=L):
    """Two nested frames (outer + inner, stroke t, gap g) = ╔═╗ box. cut_top/cut_bot =
    (xa, xb): leave the top/bottom border open between xa and xb (for an inline title)."""
    out = []
    for k in (0, 1):
        o = k * (t + g)
        X0, Y0, X1, Y1 = x + o, y + o, x + w - o, y + h - o
        for (yy, cut) in ((Y0, cut_top), (Y1 - t, cut_bot)):
            if cut:
                out.append(S.rect(X0, yy, cut[0] - X0, t, layer))
                out.append(S.rect(cut[1], yy, X1 - cut[1], t, layer))
            else:
                out.append(S.rect(X0, yy, X1 - X0, t, layer))
        out.append(S.rect(X0, Y0 + t, t, Y1 - Y0 - 2 * t, layer))
        out.append(S.rect(X1 - t, Y0 + t, t, Y1 - Y0 - 2 * t, layer))
    return out


def dbl_rule(x0, x1, y, t, g, layer=L):
    """'═══' : two parallel strokes."""
    return [S.rect(x0, y, x1 - x0, t, layer), S.rect(x0, y + t + g, x1 - x0, t, layer)]


def label_rule(x0, x1, y, label, px, t, g, lpad=1.0, gap=0.6, layer=L):
    """'══ LABEL ═══════' : a double rule whose strokes are centred on a pixel-text label.
    y = top of the label."""
    h = 7 * px
    ly = y + h / 2 - (t + g / 2)                # top of the upper stroke
    lw = text_w(label, px)
    xa, xb = x0 + lpad, x0 + lpad + lw
    out = text(label, xa, y, px, layer)
    out += dbl_rule(x0, xa - gap, ly, t, g, layer)
    out += dbl_rule(xb + gap, x1, ly, t, g, layer)
    return out


def scan_cell(x, y, w, h, pitch, t=0.2, layer=L):
    """Horizontal scanlines of width t every `pitch` mm filling a w x h cell."""
    out, yy = [], y
    while yy + t <= y + h + 1e-6:
        out.append(S.rect(x, yy, w, t, layer))
        yy += pitch
    return out


def fade(x0, x1, y, h, layer=L):
    """'█▓▒░' as scanline cells of falling density, left to right."""
    out = []
    steps = [None, 0.4, 0.6, 0.8]               # None = solid; then 50 / 33 / 25 % ink
    cw = (x1 - x0 - 0.4 * (len(steps) - 1)) / len(steps)
    for i, ptch in enumerate(steps):
        cx = x0 + i * (cw + 0.4)
        if ptch is None:
            out.append(S.rect(cx, y, cw, h, layer))
        else:
            out += scan_cell(cx, y, cw, h, ptch, layer=layer)
    return out


# ---------------------------------------------------------------- layout
def layout(mask='black'):
    assert mask == 'black', 'this design is drawn for black mask / white silk only'
    ax0, ay0, ax1, ay1 = S.FRONT_AREA
    m = 0.1                                     # inset from the allowed area
    X0, Y0, X1, Y1 = ax0 + m, ay0 + m, ax1 - m, ay1 - m
    W = X1 - X0
    P = 0.20                                    # small pixel (cap 1.4 mm)
    T, G = 0.20, 0.20                           # double-line stroke / gap
    BT = 2 * T + G                              # double border thickness (0.6)
    pcs = []

    # -- title bar  ╔═══════════════════════════════════════════════╗
    #               ║ STAXXLOGIX // BBS                   EST. 2026 ║
    #               ╚═══════════════════════════════════════════════╝
    th = BT + 0.3 + 7 * P + 0.3 + BT
    pcs += dbl_box(X0, Y0, W, th, T, G)
    ty = Y0 + (th - 7 * P) / 2
    left, right = "STAXXLOGIX // BBS", "MAIN MENU -- EST. 2026"
    inner = BT + 0.6
    pcs += text(left, X0 + inner, ty, P)
    pcs += text(right, X1 - inner - text_w(right, P), ty, P)
    title_bottom = Y0 + th

    # -- ANSI-Shadow marquee, full width
    rows = marquee_rows("STAXXLOGIX")
    cols = len(rows[0])
    cw = round(W / cols, 4)
    chh = 1.1
    my = title_bottom + 0.9
    mx = X0 + (W - cols * cw) / 2
    pcs += ansi(rows, mx, my, cw, chh, 0.2)
    marquee_bottom = my + 6 * chh

    # -- QR box (right, bottom-aligned):   ╔═════════════════╗
    #                                       ║ SCAN TO CONNECT ║
    #                                       ║ [ white field ] ║
    #                                       ╚═════════════════╝
    MOD, QZ, QG = 0.5, 4, 0.3                   # module, quiet modules, black gap to frame
    qn = 29
    qsz = (qn + 2 * QZ) * MOD                   # 18.5 mm white field (quiet zone included)
    bw = qsz + 2 * (BT + QG)
    cap = "SCAN TO CONNECT"
    capw = text_w(cap, P)
    bx = X1 - bw
    fy = Y1 - BT - QG - qsz                     # field top
    cap_y = fy - 0.35 - 7 * P                   # caption row
    top = cap_y - 0.35 - BT
    pcs += dbl_box(bx, top, bw, Y1 - top, T, G)
    pcs += text(cap, bx + (bw - capw) / 2, cap_y, P)
    fx = bx + BT + QG
    q, meta = S.qr_pieces(URL, fx + QZ * MOD, fy + QZ * MOD, MOD, quiet=QZ, invert=True, error='q')
    assert meta['modules'] == qn, meta
    pcs += q
    qr_top = top

    # -- left column: terminal session
    lx0, lx1 = X0, bx - 1.0
    PN = 0.40                                   # name pixel (cap 2.8 mm)
    name = "AARON PURSELL"
    menu = ["[1] WWW  STAXXLOGIX.COM", "[2] MAIL AP@STAXXLOGIX.COM", "[3] DIAL 210-848-8420"]
    for s_ in menu + [name]:
        px_ = PN if s_ == name else P
        assert lx0 + text_w(s_, px_) <= lx1, (s_, text_w(s_, px_), lx1 - lx0)
    y_top = top - (7 * P / 2 - (T + G / 2))    # SYSOP rule strokes level with the QR box top
    y_bot = Y1                                  # prompt cursor bottom aligns with QR box
    # blocks: (height, drawer)
    blocks = [
        ('rule', 7 * P), ('name', 7 * PN), ('gap', 0.0),
        ('m0', 7 * P), ('m1', 7 * P), ('m2', 7 * P), ('gap', 0.0),
        ('modem', 7 * P), ('prompt', 9 * P),
    ]
    used = sum(h for _, h in blocks)
    # spacing: 1 unit between lines, +0.6 unit at each 'gap' marker
    GAPU = 0.6
    lines = [k for k, _ in blocks if k != 'gap']
    units = (len(lines) - 1) + GAPU * sum(1 for k, _ in blocks if k == 'gap')
    u = ((y_bot - y_top) - used) / units
    y = y_top
    for key, h in blocks:
        if key == 'gap':
            y += GAPU * u
            continue
        if key == 'rule':
            pcs += label_rule(lx0, lx1, y, "SYSOP", P, T, G, lpad=2.4)
        elif key == 'name':
            pcs += text(name, lx0, y, PN)
        elif key in ('m0', 'm1', 'm2'):
            pcs += text(menu[int(key[1])], lx0, y, P)
        elif key == 'modem':
            cs = "CONNECT 14400/ARQ"
            pcs += text(cs, lx0, y, P)
            # carrier noise: a ▓▒░ fade drawn as scanlines (the one texture on the card)
            fx0 = lx0 + text_w(cs, P) + 1.2
            pcs += fade(fx0, lx1, y, 7 * P)
        elif key == 'prompt':
            pr = "C:\\> "
            pcs += text(pr, lx0, y + P, P)
            pcs.append(S.rect(lx0 + len(pr) * ADV * P, y, 5 * P, 9 * P))   # block cursor
        y += h + u
    return pcs, {'cw': cw, 'cols': cols, 'qr': meta, 'left_col_w': round(lx1 - lx0, 2),
                 'line_space': round(u, 3), 'qr_top': round(qr_top, 2),
                 'marquee_bottom': round(marquee_bottom, 2)}


def build(mask='black'):
    """Front art (F.SilkS pieces) for the given mask colour."""
    return layout(mask)[0]


def main():
    g = S.load_geom()
    pieces, info = layout('black')
    os.makedirs(OUT, exist_ok=True)
    out = os.path.join(OUT, 'bbs-login_front_black.png')
    img = S.render(g, pieces, 'front', 'black', 20, out)
    # zoomed crop of the art area for legibility review
    ex0, ey0, _, _ = S._edge_bbox(g)
    big = S.render(g, pieces, 'front', 'black', 40)
    a = S.FRONT_AREA
    pad = 2.0
    box = [int((a[0] - ex0 + pad - 1) * 40), int((a[1] - ey0 + pad - 1) * 40),
           int((a[2] - ex0 + pad + 1) * 40), int((a[3] - ey0 + pad + 1) * 40)]
    big.crop(box).save(os.path.join(OUT, 'bbs-login_front_black_zoom.png'))
    dfm = S.check(g, pieces, 'front', S.FRONT_AREA)
    qr = S.qr_verify(g, pieces, URL, mask='black')
    rep = {'pieces': len(pieces), 'info': info, 'bbox': [round(v, 3) for v in S.bbox(pieces)],
           'dfm': dfm, 'qr': qr, 'qr_ok': all(v == URL for v in qr.values()), 'render': out}
    print(json.dumps(rep, indent=1))


if __name__ == '__main__':
    main()
