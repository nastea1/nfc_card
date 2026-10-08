"""BOM fixes to Wilson's original files, applied deterministically by apply_final.py (board) and
leds.py (schematic).

R4 (100 R, 0402, one of the five charlieplex resistors R1/R4-R7) has no LCSC field in the
original schematic or board, while R1, R5, R6 and R7 - same value, same footprint - all carry
C25076. A JLCPCB assembly BOM built from the files therefore leaves R4 unplaced, and the LEDs on
its charlieplex line stay dark. The fix clones R5's LCSC property into R4.

C1 (1.5 pF, the antenna tuning capacitor, 0402 footprint) carries C1639 in the original, which is
0603CG1R5C500NT - an 0603 part that does not fit the 0402 land pattern (JLCPCB matched it as such).
It becomes C1552, 0402CG1R5C500NT: same maker (FH), series, C0G and +-0.25 pF code, in 0402.
"""
import re
import uuid

import silklib as S

_NS = uuid.UUID('0c1f3a52-7e44-4d1b-a6f0-5b7d2e9c8a31')
_REF = re.compile(r'\(property "Reference" "([^"]+)"')


def _balanced(text, start):
    """End index (exclusive) of the parenthesised expression starting at text[start] == '('."""
    depth, i = 0, start
    while True:
        c = text[i]
        if c == '"':
            i += 1
            while text[i] != '"':
                i += 2 if text[i] == '\\' else 1
        elif c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1


def _prop_span(block, key):
    m = re.search(r'\(property "' + re.escape(key) + r'" "', block)
    if not m:
        return None
    return m.start(), _balanced(block, m.start())


def add_field_from_sibling(src, ref, sibling, key, expect, absolute_at):
    """Copy `key` from `sibling` into `ref` (inserted after ref's Description property).
    absolute_at=True (schematic): the copied field takes ref's own Description (at ...)."""
    blocks = {(_REF.search(src[s:e]) or [None, None])[1]: (s, e) for s, e, h in S._blocks(src)
              if h in ('footprint', 'symbol')}
    assert ref in blocks and sibling in blocks, f'{ref} / {sibling} not found'
    rs, re_ = blocks[ref]
    rb, sb = src[rs:re_], src[slice(*blocks[sibling])]
    if _prop_span(rb, key):
        raise AssertionError(f'{ref} already has {key}')
    ss = _prop_span(sb, key)
    assert ss, f'{sibling} has no {key}'
    field = sb[ss[0]:ss[1]]
    assert f'(property "{key}" "{expect}"' in field, f'{sibling} {key} is not {expect}'
    field = re.sub(r'\(uuid "[0-9a-f-]{36}"\)', f'(uuid "{uuid.uuid5(_NS, ref + key)}")', field, count=1)
    ds = _prop_span(rb, 'Description')
    assert ds, f'{ref} has no Description to anchor on'
    if absolute_at:
        at = re.search(r'\(at [^()]*\)', rb[ds[0]:ds[1]]).group(0)
        field = re.sub(r'\(at [^()]*\)', at, field, count=1)
    indent = rb[rb.rfind('\n', 0, ds[0]) + 1:ds[0]]
    nb = rb[:ds[1]] + '\n' + indent + field + rb[ds[1]:]
    return src[:rs] + nb + src[re_:]


def set_field(src, ref, key, old, new):
    """Change ref's `key` from old to new (asserts the old value, exactly one match)."""
    blocks = [(s, e) for s, e, h in S._blocks(src) if h in ('footprint', 'symbol')
              and (m := _REF.search(src[s:e])) and m.group(1) == ref]
    assert len(blocks) == 1, f'{ref}: {len(blocks)} blocks'
    s, e = blocks[0]
    b, n = re.subn(r'(\(property "' + re.escape(key) + r'" ")' + re.escape(old) + '"', r'\g<1>' + new + '"', src[s:e])
    assert n == 1, f'{ref} {key} is not {old}'
    return src[:s] + b + src[e:]


def apply(src, absolute_at):
    src = add_field_from_sibling(src, 'R4', 'R5', 'LCSC', 'C25076', absolute_at)
    return set_field(src, 'C1', 'LCSC', 'C1639', 'C1552')
