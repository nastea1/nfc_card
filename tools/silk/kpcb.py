"""Minimal KiCad 9 .kicad_pcb reader: s-expression parse + geometry needed for silkscreen work.

Read-only helpers. Coordinates are KiCad mm, y grows downward. Footprint-local items are
transformed to board coordinates (KiCad rotation: positive angle = counter-clockwise on screen).
"""
import math, re

_TOK = re.compile(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+')


def parse(src):
    stack = [[]]
    for m in _TOK.finditer(src):
        t = m.group(0)
        if t == '(':
            stack.append([])
        elif t == ')':
            x = stack.pop()
            stack[-1].append(x)
        else:
            stack[-1].append(t[1:-1].replace('\\"', '"') if t.startswith('"') else t)
    return stack[0][0]


def get(node, key):
    for c in node:
        if isinstance(c, list) and c and c[0] == key:
            return c
    return None


def all_(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]


def layer(node):
    l = get(node, 'layer')
    return l[1] if l else None


def layers(node):
    l = get(node, 'layers')
    return list(l[1:]) if l else ([layer(node)] if layer(node) else [])


def xy(node):
    return (float(node[1]), float(node[2]))


def pts(node):
    p = get(node, 'pts')
    return [xy(c) for c in p if isinstance(c, list) and c[0] == 'xy'] if p else []


def at(node):
    a = get(node, 'at')
    if not a:
        return (0.0, 0.0, 0.0)
    return (float(a[1]), float(a[2]), float(a[3]) if len(a) > 3 else 0.0)


def xform(pt, origin):
    ox, oy, ang = origin
    a = math.radians(ang)
    x, y = pt
    return (ox + x * math.cos(a) + y * math.sin(a), oy - x * math.sin(a) + y * math.cos(a))


def width(node):
    s = get(node, 'stroke')
    w = get(s, 'width') if s else get(node, 'width')
    return float(w[1]) if w else 0.0


def filled(node):
    f = get(node, 'fill')
    return bool(f) and f[1] in ('yes', 'solid')
