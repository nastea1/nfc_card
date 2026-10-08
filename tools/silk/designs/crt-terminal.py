"""CRT TERMINAL - retro front artwork for the NFC business card (StaxxLogix / Aaron Pursell).

Concept: the whole free front area is a 1990s CRT monitor (rounded bezel, chin with power LED
and vent slots, neck + foot). On the screen: an inverse-video title bar with window buttons, a
shell session (`$ whoami` -> the name in ANSI-Shadow block letters, `$ cat contact.txt` -> a
numbered BBS menu of contacts) and the QR code "on screen" with a modem caption.

Board: BLACK soldermask, WHITE silkscreen. White silk = phosphor. The QR is drawn inverted
(white quiet zone + light modules, dark modules = bare black mask) so it prints with normal
dark-on-light polarity.

Run:  cd /root/nfc_card/tools/silk && /root/nfc-tools/.venv/bin/python -s designs/crt-terminal.py
"""
import sys, json, math, os

sys.path.insert(0, "/root/nfc_card/tools/silk")
import silklib as S

URL = "https://staxxlogix.com/"
OUT = "/root/.claude/jobs/5ff251a4/tmp/nfc/out"
NAME = "crt-terminal"
LAYER = "F.SilkS"
AX0, AY0, AX1, AY1 = S.FRONT_AREA
AW, AH = AX1 - AX0, AY1 - AY0          # 54.0 x 34.3 mm

# ---------------------------------------------------------------- pixel font (5x7, 6 advance)
F5 = {
    'A': ".###. #...# #...# ##### #...# #...# #...#",
    'B': "####. #...# #...# ####. #...# #...# ####.",
    'C': ".###. #...# #.... #.... #.... #...# .###.",
    'D': "###.. #..#. #...# #...# #...# #..#. ###..",
    'E': "##### #.... #.... ####. #.... #.... #####",
    'F': "##### #.... #.... ####. #.... #.... #....",
    'G': ".###. #...# #.... #.### #...# #...# .####",
    'H': "#...# #...# #...# ##### #...# #...# #...#",
    'I': ".###. ..#.. ..#.. ..#.. ..#.. ..#.. .###.",
    'J': "..### ...#. ...#. ...#. ...#. #..#. .##..",
    'K': "#...# #..#. #.#.. ##... #.#.. #..#. #...#",
    'L': "#.... #.... #.... #.... #.... #.... #####",
    'M': "#...# ##.## #.#.# #.#.# #...# #...# #...#",
    'N': "#...# #...# ##..# #.#.# #..## #...# #...#",
    'O': ".###. #...# #...# #...# #...# #...# .###.",
    'P': "####. #...# #...# ####. #.... #.... #....",
    'Q': ".###. #...# #...# #...# #.#.# #..#. .##.#",
    'R': "####. #...# #...# ####. #.#.. #..#. #...#",
    'S': ".#### #.... #.... .###. ....# ....# ####.",
    'T': "##### ..#.. ..#.. ..#.. ..#.. ..#.. ..#..",
    'U': "#...# #...# #...# #...# #...# #...# .###.",
    'V': "#...# #...# #...# #...# #...# .#.#. ..#..",
    'W': "#...# #...# #...# #.#.# #.#.# #.#.# .#.#.",
    'X': "#...# #...# .#.#. ..#.. .#.#. #...# #...#",
    'Y': "#...# #...# .#.#. ..#.. ..#.. ..#.. ..#..",
    'Z': "##### ....# ...#. ..#.. .#... #.... #####",
    '0': ".###. #...# #..## #.#.# ##..# #...# .###.",
    '1': "..#.. .##.. ..#.. ..#.. ..#.. ..#.. .###.",
    '2': ".###. #...# ....# ...#. ..#.. .#... #####",
    '3': "##### ...#. ..#.. ...#. ....# #...# .###.",
    '4': "...#. ..##. .#.#. #..#. ##### ...#. ...#.",
    '5': "##### #.... ####. ....# ....# #...# .###.",
    '6': "..##. .#... #.... ####. #...# #...# .###.",
    '7': "##### ....# ...#. ..#.. .#... .#... .#...",
    '8': ".###. #...# #...# .###. #...# #...# .###.",
    '9': ".###. #...# #...# .#### ....# ...#. .##..",
    '.': "..... ..... ..... ..... ..... .##.. .##..",
    '@': ".###. #...# #.### #.#.# #.### #.... .####",
    '-': "..... ..... ..... .###. ..... ..... .....",
    '/': "..... ....# ...#. ..#.. .#... #.... .....",
    '\\': "..... #.... .#... ..#.. ...#. ....# .....",
    ':': "..... .##.. .##.. ..... .##.. .##.. .....",
    '>': "#.... .#... ..#.. ...#. ..#.. .#... #....",
    '_': "..... ..... ..... ..... ..... ..... #####",
    '[': ".###. .#... .#... .#... .#... .#... .###.",
    ']': ".###. ...#. ...#. ...#. ...#. ...#. .###.",
    '$': "..#.. .#### #.#.. .###. ..#.# ####. ..#..",
    '#': ".#.#. .#.#. ##### .#.#. ##### .#.#. .#.#.",
    ' ': "..... ..... ..... ..... ..... ..... .....",
    '\x7f': "##### ##### ##### ##### ##### ##### #####",   # cursor block
    # lowercase for the shell commands (no descenders needed: whoami, cat contact.txt)
    'a': "..... ..... .###. ....# .#### #...# .####",
    'c': "..... ..... .###. #.... #.... #...# .###.",
    'h': "#.... #.... #.##. ##..# #...# #...# #...#",
    'i': "..#.. ..... .##.. ..#.. ..#.. ..#.. .###.",
    'm': "..... ..... ##.#. #.#.# #.#.# #...# #...#",
    'n': "..... ..... #.##. ##..# #...# #...# #...#",
    'o': "..... ..... .###. #...# #...# #...# .###.",
    't': ".#... .#... ###.. .#... .#... .#..# ..##.",
    'w': "..... ..... #...# #...# #.#.# #.#.# .#.#.",
    'x': "..... ..... #...# .#.#. ..#.. .#.#. #...#",
}
F5 = {k: v.split() for k, v in F5.items()}


def text_rows(s):
    """String -> list of 7 row strings, 5 px glyph + 1 px spacing (last spacing dropped)."""
    rows = [''] * 7
    for i, ch in enumerate(s):
        g = F5[ch]
        for r in range(7):
            rows[r] += g[r] + ('.' if i < len(s) - 1 else '')
    return rows


def text(s, x, y, px):
    """Pixel text with its top-left at (x, y) in AREA-relative mm."""
    return S.bitmap(text_rows(s), AX0 + x, AY0 + y, px, LAYER)


def text_w(s, px):
    return (len(s) * 6 - 1) * px


# ---------------------------------------------------------------- ANSI Shadow (figlet)
ANSI = {
    'A': [" █████╗ ", "██╔══██╗", "███████║", "██╔══██║", "██║  ██║", "╚═╝  ╚═╝"],
    'R': ["██████╗ ", "██╔══██╗", "██████╔╝", "██╔══██╗", "██║  ██║", "╚═╝  ╚═╝"],
    'O': [" ██████╗ ", "██╔═══██╗", "██║   ██║", "██║   ██║", "╚██████╔╝", " ╚═════╝ "],
    'N': ["███╗   ██╗", "████╗  ██║", "██╔██╗ ██║", "██║╚██╗██║", "██║ ╚████║", "╚═╝  ╚═══╝"],
    'P': ["██████╗ ", "██╔══██╗", "██████╔╝", "██╔═══╝ ", "██║     ", "╚═╝     "],
    'U': ["██╗   ██╗", "██║   ██║", "██║   ██║", "██║   ██║", "╚██████╔╝", " ╚═════╝ "],
    'S': ["███████╗", "██╔════╝", "███████╗", "╚════██║", "███████║", "╚══════╝"],
    'E': ["███████╗", "██╔════╝", "█████╗  ", "██╔══╝  ", "███████╗", "╚══════╝"],
    'L': ["██╗     ", "██║     ", "██║     ", "██║     ", "███████╗", "╚══════╝"],
}
VERT = set('║╗╔╝╚')   # box chars with a vertical stroke on the cell's centre line


def ansi_lines(word):
    return [''.join(ANSI[c][r] for c in word) for r in range(6)]


def ansi(word, x, y, cw, ch, t, trim):
    """ANSI-Shadow word. █ = full cell; box-drawing shadow = one centred stroke of width t
    (the double lines are simplified to single strokes - at 0.5 mm cells a real double line
    cannot be printed). A █ facing a vertical shadow stroke is pulled back by `trim` so the
    gap stays >= (cw - t) / 2 + trim; arms that reach a cell edge are extended by `trim` so
    they still join the (trimmed) block."""
    out = []
    X, Y = AX0 + x, AY0 + y
    for r, row in enumerate(ansi_lines(word)):
        y0, y1, cy = Y + r * ch, Y + (r + 1) * ch, Y + (r + 0.5) * ch
        c = 0
        n = len(row)
        while c < n:
            if row[c] == '█':
                s = c
                while c + 1 < n and row[c + 1] == '█':
                    c += 1
                xa = X + s * cw + (trim if s > 0 and row[s - 1] in VERT else 0)
                xb = X + (c + 1) * cw - (trim if c + 1 < n and row[c + 1] in VERT else 0)
                out.append(S.rect(xa, y0, xb - xa, y1 - y0, LAYER))
            elif row[c] != ' ':
                k = row[c]
                x0, x1, cx = X + c * cw, X + (c + 1) * cw, X + (c + 0.5) * cw
                hl, hr = cx - t / 2, cx + t / 2       # extent of the centre stroke
                if k == '═':
                    out.append(S.rect(x0 - trim, cy - t / 2, cw + 2 * trim, t, LAYER))
                if k == '║':
                    out.append(S.rect(hl, y0, t, ch, LAYER))
                if k in '╗╝':   # arm to the left edge
                    out.append(S.rect(x0 - trim, cy - t / 2, hr - x0 + trim, t, LAYER))
                if k in '╔╚':   # arm to the right edge
                    out.append(S.rect(hl, cy - t / 2, x1 + trim - hl, t, LAYER))
                if k in '╗╔':   # down
                    out.append(S.rect(hl, cy - t / 2, t, y1 - cy + t / 2, LAYER))
                if k in '╝╚':   # up
                    out.append(S.rect(hl, y0, t, cy + t / 2 - y0, LAYER))
            c += 1
    return out


def ansi_w(word, cw):
    return len(ansi_lines(word)[0]) * cw


# ---------------------------------------------------------------- shapes
def arc_ring(cx, cy, R, t, a0, a1, n=10):
    """Annular sector (outer radius R, width t) from angle a0 to a1 (deg, y down)."""
    ang = [math.radians(a0 + (a1 - a0) * i / n) for i in range(n + 1)]
    outer = [[cx + R * math.cos(a), cy + R * math.sin(a)] for a in ang]
    inner = [[cx + (R - t) * math.cos(a), cy + (R - t) * math.sin(a)] for a in reversed(ang)]
    return {'layer': LAYER, 'pts': outer + inner}


def round_frame(x, y, w, h, r, t):
    """Rounded-rectangle outline (outer corner radius r, stroke t), AREA-relative."""
    X, Y = AX0 + x, AY0 + y
    out = [S.rect(X + r, Y, w - 2 * r, t, LAYER), S.rect(X + r, Y + h - t, w - 2 * r, t, LAYER),
           S.rect(X, Y + r, t, h - 2 * r, LAYER), S.rect(X + w - t, Y + r, t, h - 2 * r, LAYER)]
    out += [arc_ring(X + r, Y + r, r, t, 180, 270), arc_ring(X + w - r, Y + r, r, t, 270, 360),
            arc_ring(X + w - r, Y + h - r, r, t, 0, 90), arc_ring(X + r, Y + h - r, r, t, 90, 180)]
    return out


def R(x, y, w, h):
    return S.rect(AX0 + x, AY0 + y, w, h, LAYER)


def poly(pts):
    return {'layer': LAYER, 'pts': [[AX0 + a, AY0 + b] for a, b in pts]}


def inverse_bar(s, x, y, w, px, pad_px, buttons=True):
    """Inverse-video title bar: a white bar, text and window buttons cut out (bare mask)."""
    W = int(round(w / px))
    H = 7 + 2 * pad_px
    grid = [['#'] * W for _ in range(H)]
    rows = text_rows(s)
    x0 = pad_px + 1
    for r, row in enumerate(rows):
        for c, v in enumerate(row):
            if v == '#':
                grid[pad_px + r][x0 + c] = '.'
    if buttons:
        # three 7x7 buttons at the right: minimise (bar), maximise (hollow box), close (X)
        btn = [
            ["......."] * 5 + [".#####.", "......."],
            [".......", ".#####.", ".#...#.", ".#...#.", ".#...#.", ".#####.", "......."],
            [".......", ".#...#.", "..#.#..", "...#...", "..#.#..", ".#...#.", "......."],
        ]
        bx = W - pad_px - 1 - 3 * 7 - 2 * 1
        for i, b in enumerate(btn):
            for r in range(7):
                for c in range(7):
                    # a button = dark square with the white symbol inside it
                    grid[pad_px + r][bx + i * 8 + c] = '#' if b[r][c] == '#' else '.'
    return S.bitmap([''.join(r) for r in grid], AX0 + x, AY0 + y, px, LAYER), H * px


# ---------------------------------------------------------------- the design
P = dict(
    body_t=0.30, body_r=2.4, body_h=31.0,
    scr_in=0.85, scr_t=0.25, scr_r=1.5, scr_bot=28.3,
    pad=0.5,
    bar_px=0.25, bar_pad=2,
    cmd_px=0.22, txt_px=0.22, cap_px=0.20,
    cw=0.53, ch=0.70, st=0.20, trim=0.04,
    qr_mod=0.52, qr_quiet=4,
)


def build(mask='black'):
    p = P
    out = []
    # --- monitor body + screen
    out += round_frame(0, 0, AW, p['body_h'], p['body_r'], p['body_t'])
    sx0, sy0 = p['scr_in'], p['scr_in']
    sx1, sy1 = AW - p['scr_in'], p['scr_bot']
    out += round_frame(sx0, sy0, sx1 - sx0, sy1 - sy0, p['scr_r'], p['scr_t'])
    ix0, iy0 = sx0 + p['scr_t'] + p['pad'], sy0 + p['scr_t'] + p['pad']   # content box
    ix1 = sx1 - p['scr_t'] - p['pad']

    # --- title bar (inverse video)
    bar, bar_h = inverse_bar("STAXXLOGIX // TERMINAL", ix0, iy0, ix1 - ix0, p['bar_px'], p['bar_pad'])
    out += bar
    y = iy0 + bar_h + 0.7

    # --- QR on the right, top aligned with the first prompt line (quiet zone included)
    q_side = (29 + 2 * p['qr_quiet']) * p['qr_mod']
    qx = ix1 - q_side
    qr, info = S.qr_pieces(URL, AX0 + qx + p['qr_quiet'] * p['qr_mod'], AY0 + y + p['qr_quiet'] * p['qr_mod'],
                           p['qr_mod'], quiet=p['qr_quiet'], layer=LAYER, invert=True, error='q')
    assert info['modules'] == 29, info
    out += qr

    # --- shell session, left column
    cpx, tpx = p['cmd_px'], p['txt_px']
    out += text("$ whoami", ix0, y, cpx)
    y += 7 * cpx + 0.6
    out += ansi("AARON", ix0, y, p['cw'], p['ch'], p['st'], p['trim'])
    y += 6 * p['ch'] + 0.45
    out += ansi("PURSELL", ix0, y, p['cw'], p['ch'], p['st'], p['trim'])
    y += 6 * p['ch'] + 0.75
    out += text("$ cat contact.txt", ix0, y, cpx)
    y += 7 * cpx + 0.65
    for line in ("[1] STAXXLOGIX.COM", "[2] AP@STAXXLOGIX.COM", "[3] ATDT 210-848-8420"):
        out += text(line, ix0, y, tpx)
        y += 7 * tpx + 0.66
    y += 0.15
    out += text("$ \x7f", ix0, y, cpx)
    cap = "SCAN TO CONNECT"
    out += text(cap, qx + (q_side - text_w(cap, p["cap_px"])) / 2, y + 7 * (cpx - p["cap_px"]), p["cap_px"])

    # --- chin: scanline speaker grille left (the one sparse hatch), power LED + button right
    cy = (sy1 + p['body_h']) / 2
    for i in range(3):
        out.append(R(3.0, cy - 0.6 + i * 0.5, 6.0, 0.2))
    out.append(R(AW - 4.4, cy - 0.35, 0.7, 0.7))            # power LED
    out += [R(AW - 7.0, cy - 0.45, 1.6, 0.25), R(AW - 7.0, cy + 0.2, 1.6, 0.25),
            R(AW - 7.0, cy - 0.2, 0.25, 0.4), R(AW - 5.65, cy - 0.2, 0.25, 0.4)]   # button outline

    # --- stand: neck + foot
    b = p['body_h']
    cxm = AW / 2
    out.append(poly([[cxm - 4.0, b - 0.05], [cxm - 3.75, b - 0.05], [cxm - 5.25, AH - 0.85], [cxm - 5.5, AH - 0.85]]))
    out.append(poly([[cxm + 3.75, b - 0.05], [cxm + 4.0, b - 0.05], [cxm + 5.5, AH - 0.85], [cxm + 5.25, AH - 0.85]]))
    out.append(R(cxm - 9.0, AH - 0.85, 18.0, 0.65))
    return out


def main():
    g = S.load_geom()
    pieces = build('black')
    os.makedirs(OUT, exist_ok=True)
    png = os.path.join(OUT, f'{NAME}_front_black.png')
    img = S.render(g, pieces, 'front', mask='black', scale=20, out=png)
    # zoomed crop of the free area for inspection
    ex0, ey0, _, _ = S._edge_bbox(g)
    z = S.render(g, pieces, 'front', mask='black', scale=40)
    c = lambda x, y: (int((x - ex0 + 2) * 40), int((y - ey0 + 2) * 40))
    zoom = os.path.join(OUT, f'{NAME}_front_black_zoom.png')
    z.crop(c(AX0 - 1, AY0 - 1) + c(AX1 + 1, AY1 + 1)).save(zoom)
    rep = {
        'design': NAME,
        'renders': [png, zoom],
        'check': S.check(g, pieces, 'front', S.FRONT_AREA),
        'qr_verify': S.qr_verify(g, pieces, URL, mask='black'),
        # The default qr_verify (scale 12) quantises its +-0.05/-0.04 kernels to 1 px, i.e. no
        # spread at all - so prove real margin at scale 40, where 0.075 mm = a 3 px radius.
        'qr_verify_spread075': S.qr_verify(g, pieces, URL, mask='black', scale=40, spread_mm=(0.0, 0.075, -0.075)),
        # informational only: +-0.1 mm per side (dark modules 0.52 -> 0.32 mm) is past the margin
        'qr_probe_0p1_info': S.qr_verify(g, pieces, URL, mask='black', scale=20, spread_mm=(0.1, -0.1)),
        'bbox': [round(v, 2) for v in S.bbox(pieces)],
        'params': P,
    }
    rep['qr_ok'] = all(v == URL for v in rep['qr_verify'].values()) and all(v == URL for v in rep['qr_verify_spread075'].values())
    rep['dfm_ok'] = not rep['check']['errors']
    print(json.dumps(rep, indent=1))


if __name__ == '__main__':
    main()
