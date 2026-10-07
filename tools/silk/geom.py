"""Dump board geometry relevant to silkscreen layout as JSON (outline, pads, copper, mask, silk)."""
import json, sys, math
from kpcb import *

pcb = parse(open(sys.argv[1], encoding='utf-8').read())
out = {'edge': [], 'pads': [], 'tracks': [], 'zones': [], 'gr': {}, 'fp_silk': [], 'footprints': []}

def shape_pts(n, origin=None):
    k = n[0].split('_', 1)[1]
    tf = (lambda p: xform(p, origin)) if origin else (lambda p: p)
    if k == 'line':
        return k, [tf(xy(get(n, 'start'))), tf(xy(get(n, 'end')))]
    if k == 'rect':
        (x1, y1), (x2, y2) = xy(get(n, 'start')), xy(get(n, 'end'))
        return k, [tf(p) for p in [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]]
    if k == 'poly':
        return k, [tf(p) for p in pts(n)]
    if k == 'curve':
        return k, [tf(p) for p in pts(n)]
    if k == 'arc':
        return k, [tf(xy(get(n, w))) for w in ('start', 'mid', 'end')]
    if k == 'circle':
        c, e = xy(get(n, 'center')), xy(get(n, 'end'))
        r = math.dist(c, e)
        return k, [tf((c[0] + r * math.cos(t * math.pi / 16), c[1] + r * math.sin(t * math.pi / 16))) for t in range(32)]
    if k == 'text':
        return k, [tf(at(n)[:2])]
    return k, []

for n in pcb:
    if not isinstance(n, list) or not n:
        continue
    if n[0].startswith('gr_'):
        k, p = shape_pts(n)
        L = layer(n)
        out['gr'].setdefault(L, []).append({'kind': k, 'pts': p, 'w': width(n), 'fill': filled(n),
                                             'text': n[1] if k == 'text' else None})
    elif n[0] == 'segment':
        out['tracks'].append({'layer': layer(n), 'pts': [xy(get(n, 'start')), xy(get(n, 'end'))], 'w': float(get(n, 'width')[1])})
    elif n[0] == 'arc':
        out['tracks'].append({'layer': layer(n), 'pts': [xy(get(n, w)) for w in ('start', 'mid', 'end')], 'w': float(get(n, 'width')[1]), 'arc': True})
    elif n[0] == 'zone':
        for fp in all_(n, 'filled_polygon'):
            out['zones'].append({'layer': layer(fp) or layer(n), 'pts': pts(fp)})
    elif n[0] == 'footprint':
        o = at(n)
        ref = next((c[2] for c in all_(n, 'property') if c[1] == 'Reference'), '?')
        out['footprints'].append({'lib': n[1], 'ref': ref, 'at': o, 'layer': layer(n)})
        for p in all_(n, 'pad'):
            pa = at(p)
            sz = get(p, 'size')
            c = xform(pa[:2], o)
            out['pads'].append({'ref': ref, 'num': p[1], 'type': p[2], 'shape': p[3], 'c': c,
                                'size': (float(sz[1]), float(sz[2])), 'rot': pa[2] + o[2] if len(get(p,'at'))>3 else o[2],
                                'layers': layers(p)})
        for c in n:
            if isinstance(c, list) and c and c[0].startswith('fp_') and layer(c) in ('F.SilkS', 'B.SilkS', 'F.Mask', 'B.Mask', 'F.Cu', 'B.Cu', 'Edge.Cuts'):
                k, p = shape_pts(c, o)
                out['fp_silk'].append({'ref': ref, 'layer': layer(c), 'kind': k, 'pts': p, 'w': width(c), 'fill': filled(c)})

json.dump(out, open(sys.argv[2], 'w'), indent=0)
def bbox(ps):
    xs = [p[0] for p in ps]; ys = [p[1] for p in ps]
    return (round(min(xs), 2), round(min(ys), 2), round(max(xs), 2), round(max(ys), 2)) if ps else None
for L, items in sorted(out['gr'].items()):
    print(L, len(items), 'bbox', bbox([p for i in items for p in i['pts']]), {k: sum(1 for i in items if i['kind'] == k) for k in set(i['kind'] for i in items)})
print('footprints', len(out['footprints']), sorted(set(f['lib'].split(':')[-1] for f in out['footprints'])))
print('pads', len(out['pads']), 'tracks', len(out['tracks']), {l: sum(1 for t in out['tracks'] if t['layer'] == l) for l in set(t['layer'] for t in out['tracks'])})
print('zones', len(out['zones']), {l: sum(1 for z in out['zones'] if z['layer'] == l) for l in set(z['layer'] for z in out['zones'])})
print('fp graphics', {(f['layer']): sum(1 for g in out['fp_silk'] if g['layer'] == f['layer']) for f in out['fp_silk']})
for f in out['footprints']:
    print('  ', f['ref'], f['lib'], [round(v, 2) for v in f['at']], f['layer'])
