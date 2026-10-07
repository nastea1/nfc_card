"""Silkscreen design toolkit for the NFC business card.

One place for: board geometry (from geom.json), preview rendering, DFM checks and writing new
silkscreen into the .kicad_pcb. Designs describe artwork as simple filled polygons in BOARD
millimetres (KiCad coordinates, y down), seen from the FRONT for both layers; back-layer art is
written in board coordinates too, so text meant to read from the back must be mirrored in x by
the design (use mirror_x()).

Primitive format (a "piece"): {"layer": "F.SilkS"|"B.SilkS", "pts": [[x, y], ...]} - one simple
polygon, no holes, no self-intersection. Overlaps are fine (KiCad unions them on plot). Holes
are made by decomposing (e.g. a frame is four rectangles).
"""
import json, math, os, re, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
PCB_DEFAULT = os.path.join(HERE, '..', '..', 'hardware', 'Business Card v2.kicad_pcb')

# JLCPCB silkscreen limits (standard / high-precision process): min line width 0.153 mm (we use
# 0.16), min character height 1.0 mm, silk-to-pad clearance 0.15 mm. Board edge margin is ours.
MIN_FEATURE = 0.16
MIN_GAP = 0.16
PAD_CLEAR = 0.15
EDGE_MARGIN = 0.5

# The old front artwork (Wilson's name, contacts, QR, NFC symbol): every top-level F.SilkS
# graphic whose bbox lies inside this box. Measured: 212 items in x 132.14..182.18,
# y 81.37..115.38. The U1/U2/Q1 labels and the lightning bolt sit left of x = 129.
OLD_FRONT_ART = (130.0, 80.0, 184.0, 116.0)
# Free area for new front art: right of the component column, inside the LED ring. Pads and
# footprint silk inside it are still checked individually.
FRONT_AREA = (130.6, 80.6, 184.6, 114.9)

MASKS = {
    'white': {'mask': (246, 246, 242), 'silk': (18, 18, 18), 'cu_under': (228, 226, 214)},
    'black': {'mask': (22, 22, 24), 'silk': (238, 238, 232), 'cu_under': (40, 40, 38)},
    'green': {'mask': (20, 82, 40), 'silk': (240, 240, 235), 'cu_under': (30, 105, 52)},
}
GOLD = (212, 175, 55)


def load_geom(path=None):
    path = path or os.environ.get('NFC_GEOM', '/root/.claude/jobs/5ff251a4/tmp/nfc/geom.json')
    return json.load(open(path))


# ---------- primitive helpers ----------

def rect(x, y, w, h, layer='F.SilkS'):
    return {'layer': layer, 'pts': [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]}


def frame(x, y, w, h, t, layer='F.SilkS'):
    """Rectangular outline of thickness t as four rectangles (no holes needed)."""
    return [rect(x, y, w, t, layer), rect(x, y + h - t, w, t, layer),
            rect(x, y + t, t, h - 2 * t, layer), rect(x + w - t, y + t, t, h - 2 * t, layer)]


def line(x1, y1, x2, y2, t, layer='F.SilkS'):
    """A straight stroke of width t as a rectangle polygon."""
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L * t / 2, dx / L * t / 2
    return {'layer': layer, 'pts': [[x1 + nx, y1 + ny], [x2 + nx, y2 + ny], [x2 - nx, y2 - ny], [x1 - nx, y1 - ny]]}


def mirror_x(pieces, cx):
    """Mirror pieces about the vertical line x = cx (for text that reads from the back)."""
    return [{'layer': p['layer'], 'pts': [[2 * cx - x, y] for x, y in reversed(p['pts'])]} for p in pieces]


def bitmap(rows, x, y, px, layer='F.SilkS', on='#', merge=True):
    """Rows of characters -> filled rectangles of size px; horizontal runs merged into one rect."""
    out = []
    for r, row in enumerate(rows):
        c = 0
        while c < len(row):
            if row[c] in on:
                s = c
                while merge and c + 1 < len(row) and row[c + 1] in on:
                    c += 1
                out.append(rect(x + s * px, y + r * px, (c - s + 1) * px, px, layer))
            c += 1
    return out


def qr_pieces(data, x, y, module, quiet=4, layer='F.SilkS', invert=False, error='q'):
    """QR code as silk. invert=False: dark modules are silk (light board, dark ink).
    invert=True: light modules AND the quiet zone are silk, dark modules are bare mask
    (dark board, light ink) - so the printed code still has normal polarity."""
    import segno
    q = segno.make(data, error=error, micro=False, boost_error=False)
    m = [list(r) for r in q.matrix]
    n = len(m)
    rows = []
    for r in range(-quiet, n + quiet):
        s = ''
        for c in range(-quiet, n + quiet):
            dark = 0 <= r < n and 0 <= c < n and m[r][c]
            s += '#' if (dark != invert) else '.'
        rows.append(s)
    if not invert:
        rows = [row[quiet:len(row) - quiet] for row in rows[quiet:len(rows) - quiet]]
        return bitmap(rows, x, y, module, layer), {'version': q.version, 'modules': n, 'error': q.error}
    return bitmap(rows, x - quiet * module, y - quiet * module, module, layer), {'version': q.version, 'modules': n, 'error': q.error}


def bbox(pieces):
    xs = [p[0] for pc in pieces for p in pc['pts']]
    ys = [p[1] for pc in pieces for p in pc['pts']]
    return (min(xs), min(ys), max(xs), max(ys))


# ---------- rendering ----------

def _bez(p0, p1, p2, p3, n=16):
    return [((1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * p1[0] + 3 * (1 - t) * t * t * p2[0] + t ** 3 * p3[0],
             (1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * p1[1] + 3 * (1 - t) * t * t * p2[1] + t ** 3 * p3[1])
            for t in [i / n for i in range(n + 1)]]


def _edge_bbox(g):
    ps = [p for i in g['gr'].get('Edge.Cuts', []) for p in i['pts']]
    return (min(p[0] for p in ps), min(p[1] for p in ps), max(p[0] for p in ps), max(p[1] for p in ps))


def _corner_r(g):
    for i in g['gr'].get('Edge.Cuts', []):
        if i['kind'] == 'arc':
            (x1, y1), (x2, y2), (x3, y3) = i['pts']
            d = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
            if d:
                ux = ((x1 ** 2 + y1 ** 2) * (y2 - y3) + (x2 ** 2 + y2 ** 2) * (y3 - y1) + (x3 ** 2 + y3 ** 2) * (y1 - y2)) / d
                uy = ((x1 ** 2 + y1 ** 2) * (x3 - x2) + (x2 ** 2 + y2 ** 2) * (x1 - x3) + (x3 ** 2 + y3 ** 2) * (x2 - x1)) / d
                return math.dist((ux, uy), (x1, y1))
    return 3.0


def _is_old_front(item):
    x0, y0, x1, y1 = OLD_FRONT_ART
    return all(x0 <= p[0] <= x1 and y0 <= p[1] <= y1 for p in item['pts'])


def render(g, pieces, side='front', mask='white', scale=20, out=None, drop_old_front=True,
           drop_back=None, show_cu=True):
    """Preview PNG of one side. pieces = new art. drop_old_front removes Wilson's front art.
    drop_back: optional predicate(item) -> True to remove an existing B.SilkS graphic."""
    from PIL import Image, ImageDraw
    col = MASKS[mask]
    ex0, ey0, ex1, ey1 = _edge_bbox(g)
    pad = 2.0
    W, H = int((ex1 - ex0 + 2 * pad) * scale), int((ey1 - ey0 + 2 * pad) * scale)
    img = Image.new('RGB', (W, H), (120, 120, 140))
    d = ImageDraw.Draw(img)
    mir = side == 'back'

    def P(p):
        x = (p[0] - ex0 + pad) * scale
        if mir:
            x = W - x
        return (x, (p[1] - ey0 + pad) * scale)

    tl, br = P((ex0, ey0)), P((ex1, ey1))
    box = [min(tl[0], br[0]), tl[1], max(tl[0], br[0]), br[1]]
    d.rounded_rectangle(box, radius=_corner_r(g) * scale, fill=col['mask'])
    cu = 'F.Cu' if side == 'front' else 'B.Cu'
    mk = 'F.Mask' if side == 'front' else 'B.Mask'
    sk = 'F.SilkS' if side == 'front' else 'B.SilkS'
    if show_cu:
        for z in g['zones']:
            if z['layer'] == cu and len(z['pts']) > 2:
                d.polygon([P(p) for p in z['pts']], fill=col['cu_under'])
        for t in g['tracks']:
            if t['layer'] == cu:
                d.line([P(p) for p in t['pts']], fill=col['cu_under'], width=max(1, int(t['w'] * scale)))
    # mask openings (exposed gold): F.Mask graphics
    for i in g['gr'].get(mk, []):
        ps = [P(p) for p in i['pts']]
        if i['kind'] == 'curve' and len(i['pts']) == 4:
            ps = [P(p) for p in _bez(*i['pts'])]
        if i['fill'] and len(ps) > 2:
            d.polygon(ps, fill=GOLD)
        elif len(ps) > 1:
            d.line(ps, fill=GOLD, width=max(1, int(i['w'] * scale)), joint='curve')
    for pd in g['pads']:
        if cu in pd['layers'] or '*.Cu' in pd['layers']:
            (cx, cy), (w, h) = pd['c'], pd['size']
            rot = math.radians(pd.get('rot', 0) or 0)
            corners = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
            ps = [P((cx + a * math.cos(rot) + b * math.sin(rot), cy - a * math.sin(rot) + b * math.cos(rot))) for a, b in corners]
            d.polygon(ps, fill=GOLD)

    def draw_item(i, color):
        ps = [P(p) for p in i['pts']]
        if i['kind'] == 'curve' and len(i['pts']) == 4:
            ps = [P(p) for p in _bez(*i['pts'])]
        if i.get('fill') and len(ps) > 2:
            d.polygon(ps, fill=color)
            if i.get('w'):
                d.line(ps + [ps[0]], fill=color, width=max(1, int(i['w'] * scale)))
        elif len(ps) > 1:
            d.line(ps, fill=color, width=max(1, int((i.get('w') or 0.12) * scale)), joint='curve')
        elif i['kind'] == 'text' and i.get('text'):
            d.text(ps[0], i['text'], fill=color)

    for i in g['gr'].get(sk, []):
        if side == 'front' and drop_old_front and _is_old_front(i):
            continue
        if side == 'back' and drop_back and drop_back(i):
            continue
        draw_item(i, col['silk'])
    for f in g['fp_silk']:
        if f['layer'] == sk:
            draw_item(f, col['silk'])
    for pc in pieces:
        if pc['layer'] == sk:
            d.polygon([P(p) for p in pc['pts']], fill=col['silk'])
    if out:
        img.save(out)
    return img


# ---------- DFM / layout checks ----------

def check(g, pieces, side='front', area=None, scale=40):
    """Returns a dict of problems for new art on one side. Raster-based, conservative."""
    import numpy as np, cv2
    sk = 'F.SilkS' if side == 'front' else 'B.SilkS'
    cu = 'F.Cu' if side == 'front' else 'B.Cu'
    mine = [p for p in pieces if p['layer'] == sk]
    res = {'pieces': len(mine), 'errors': [], 'warnings': []}
    if not mine:
        return res
    ex0, ey0, ex1, ey1 = _edge_bbox(g)
    W, H = int((ex1 - ex0) * scale) + 1, int((ey1 - ey0) * scale) + 1
    P = lambda p: (int(round((p[0] - ex0) * scale)), int(round((p[1] - ey0) * scale)))
    art = np.zeros((H, W), np.uint8)
    for pc in mine:
        if len(pc['pts']) < 3:
            res['errors'].append(f'piece with <3 points: {pc["pts"]}')
            continue
        cv2.fillPoly(art, [np.array([P(p) for p in pc['pts']], np.int32)], 255)
    # 1. inside the board with margin, and inside the allowed area if given
    bx0, by0, bx1, by1 = bbox(mine)
    if bx0 < ex0 + EDGE_MARGIN or by0 < ey0 + EDGE_MARGIN or bx1 > ex1 - EDGE_MARGIN or by1 > ey1 - EDGE_MARGIN:
        res['errors'].append(f'art bbox {tuple(round(v, 2) for v in (bx0, by0, bx1, by1))} within {EDGE_MARGIN} mm of the board edge')
    if area:
        ax0, ay0, ax1, ay1 = area
        if bx0 < ax0 or by0 < ay0 or bx1 > ax1 or by1 > ay1:
            res['errors'].append(f'art bbox {tuple(round(v, 2) for v in (bx0, by0, bx1, by1))} outside allowed area {area}')
    # 2. keep-outs: pads (+clearance), exposed copper (mask openings), existing footprint silk
    keep = np.zeros_like(art)
    for pd in g['pads']:
        if cu in pd['layers'] or '*.Cu' in pd['layers']:
            (cx, cy), (w, h) = pd['c'], pd['size']
            r = math.hypot(w, h) / 2 + PAD_CLEAR
            cv2.circle(keep, P((cx, cy)), int(r * scale), 255, -1)
    mk = 'F.Mask' if side == 'front' else 'B.Mask'
    for i in g['gr'].get(mk, []):
        ps = i['pts'] if not (i['kind'] == 'curve' and len(i['pts']) == 4) else _bez(*i['pts'])
        arr = np.array([P(p) for p in ps], np.int32)
        if i['fill'] and len(ps) > 2:
            cv2.fillPoly(keep, [arr], 255)
        elif len(ps) > 1:
            cv2.polylines(keep, [arr], False, 255, max(1, int((i['w'] + 2 * PAD_CLEAR) * scale)))
    for f in g['fp_silk']:
        if f['layer'] == sk and len(f['pts']) > 1:
            arr = np.array([P(p) for p in f['pts']], np.int32)
            cv2.polylines(keep, [arr], f['kind'] in ('rect', 'poly', 'circle'), 255, max(1, int(((f['w'] or 0.12) + 0.2) * scale)))
    hit = cv2.bitwise_and(art, keep)
    if hit.any():
        ys, xs = np.nonzero(hit)
        res['errors'].append(f'{len(xs)} px of art over a pad / exposed copper / footprint silk keep-out, e.g. at '
                             f'({xs[0] / scale + ex0:.2f}, {ys[0] / scale + ey0:.2f}) mm')
    # 3. thin features: opening with a MIN_FEATURE disc removes anything thinner
    k = max(3, int(MIN_FEATURE * scale) | 1)
    disc = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    thin = cv2.subtract(art, cv2.morphologyEx(art, cv2.MORPH_OPEN, disc))
    thin = cv2.morphologyEx(thin, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    if thin.sum() / 255 > 0.002 * (art.sum() / 255 + 1):
        ys, xs = np.nonzero(thin)
        res['errors'].append(f'features thinner than {MIN_FEATURE} mm: {len(xs)} px, e.g. at ({xs[0] / scale + ex0:.2f}, {ys[0] / scale + ey0:.2f}) mm')
    # 4. narrow gaps: closing fills gaps narrower than MIN_GAP
    gap = cv2.subtract(cv2.morphologyEx(art, cv2.MORPH_CLOSE, disc), art)
    gap = cv2.morphologyEx(gap, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    if gap.sum() / 255 > 0.002 * (art.sum() / 255 + 1):
        ys, xs = np.nonzero(gap)
        res['warnings'].append(f'gaps narrower than {MIN_GAP} mm may fill in: {len(xs)} px, e.g. at ({xs[0] / scale + ex0:.2f}, {ys[0] / scale + ey0:.2f}) mm')
    res['ink_area_mm2'] = round(art.sum() / 255 / scale / scale, 1)
    return res


def qr_verify(g, pieces, data, mask='white', side='front', spread_mm=(0.0, 0.05, -0.04), scale=12):
    """Render the side like a photo (8-12 px/mm), simulate ink spread/shrink, decode with OpenCV.
    Returns {spread: decoded_text_or_None}. All must equal data."""
    import numpy as np, cv2
    img = render(g, pieces, side=side, mask=mask, scale=scale, show_cu=False)
    gray = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
    out = {}
    det = cv2.QRCodeDetector()
    for s in spread_mm:
        k = max(1, int(abs(s) * scale * 2) | 1)
        ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
        silk_dark = MASKS[mask]['silk'][0] < MASKS[mask]['mask'][0]
        im = gray.copy()
        if s:
            grow_silk = s > 0
            # silk dark -> growing silk = erode the image (dark spreads); silk light -> dilate
            im = cv2.erode(im, ker) if grow_silk == silk_dark else cv2.dilate(im, ker)
        im = cv2.GaussianBlur(im, (3, 3), 0)
        txt, _, _ = det.detectAndDecode(im)
        if not txt:
            txt, _, _ = det.detectAndDecode(255 - im)
            txt = ('INVERTED:' + txt) if txt else None
        out[str(s)] = txt
    return out


# ---------- writing the .kicad_pcb ----------

def _blocks(src):
    """Yield (start, end, head) for every top-level child '(...)' of the root kicad_pcb list."""
    depth, i, n = 0, 0, len(src)
    start = None
    while i < n:
        ch = src[i]
        if ch == '"':
            i += 1
            while i < n and src[i] != '"':
                i += 2 if src[i] == '\\' else 1
        elif ch == '(':
            depth += 1
            if depth == 2:
                start = i
        elif ch == ')':
            if depth == 2:
                head = re.match(r'\(\s*([^\s()]+)', src[start:start + 64]).group(1)
                yield start, i + 1, head
            depth -= 1
        i += 1


def _fmt(v):
    s = f'{v:.6f}'.rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


def gr_poly_text(pc, uid=None):
    # wrap points 4 per line like KiCad does
    toks = [f'(xy {_fmt(x)} {_fmt(y)})' for x, y in pc['pts']]
    lines = '\n'.join('\t\t\t' + ' '.join(toks[i:i + 4]) for i in range(0, len(toks), 4))
    return (f'\t(gr_poly\n\t\t(pts\n{lines}\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type solid)\n\t\t)\n'
            f'\t\t(fill yes)\n\t\t(layer "{pc["layer"]}")\n\t\t(uuid "{uid or uuid.uuid4()}")\n\t)\n')


def apply(src, pieces, remove):
    """Return new board text: top-level graphics for which remove(head, block_text) is True are
    deleted; pieces are appended as gr_poly before the closing paren. Everything else is kept
    byte-for-byte."""
    from kpcb import parse
    out, last, removed = [], 0, 0
    for s, e, head in _blocks(src):
        if remove(head, src[s:e]):
            ls = src.rfind('\n', 0, s) + 1
            out.append(src[last:ls])
            le = e + 1 if e < len(src) and src[e] == '\n' else e
            last = le
            removed += 1
    out.append(src[last:])
    body = ''.join(out).rstrip()
    assert body.endswith(')'), 'board text does not end with )'
    new = body[:-1].rstrip('\n') + '\n' + ''.join(gr_poly_text(p) for p in pieces) + ')\n'
    parse(new)  # must still parse
    return new, removed


def old_front_remover(head, text):
    """True for Wilson's front artwork: top-level gr_* on F.SilkS entirely inside OLD_FRONT_ART."""
    if not head.startswith('gr_') or '(layer "F.SilkS")' not in text:
        return False
    pts = [(float(a), float(b)) for a, b in re.findall(r'\((?:xy|start|end|mid|center|at) (-?[\d.]+) (-?[\d.]+)', text)]
    x0, y0, x1, y1 = OLD_FRONT_ART
    return bool(pts) and all(x0 <= x <= x1 and y0 <= y <= y1 for x, y in pts)
