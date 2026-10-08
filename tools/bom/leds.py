#!/usr/bin/env python3
"""Animation LEDs LED1..LED20: red XL-1608SURC-06FJ (C7371900) -> amber XL-1608UYC-06FJ (C7371901).

Amber is the brightest retro-CRT colour that still lights on the NFC-harvested supply: same
XINGLIGHT -06FJ family as the red, 600 mcd, Vf 1.9-2.3 V (the red is 600 mcd, 1.8-2.3 V). The
phosphor-green XL-1608SYGC-06 (C965805) was rejected: 60 mcd, ten times dimmer.

The part fields are copied from LED22, which is already this exact amber part, so nothing is
typed by hand. Only property VALUES change; footprints, pads, nets and positions do not.

Footprint note: LED1..20 keep JLCImport:XL-1608SURC-06FJ. Its pad 1 is the ANODE at +x and its
pad 2 the cathode at -x; the amber footprint numbers them the other way (pad 1 = cathode at -x),
but in both the CATHODE is the -x pad, so the amber part sits the right way round on the red
land pattern. At JLCPCB, check in the placement preview that every LED's cathode mark is on the
-x pad (the side LED1..20 have always had their cathode on).

Usage:
  leds.swap(text) -> (new_text, n)       for .kicad_pcb (footprints) and .kicad_sch (symbols)
  python leds.py                          rewrite the schematic from the pristine 57a460f source
                                          (LED swap + fixes.py: R4's missing LCSC number, C1 0603->0402 part)
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'silk'))
import silklib as S  # noqa: E402  (for _blocks: top-level s-expression walk)

KEYS = ('Value', 'Datasheet', 'Description', 'LCSC', 'Manufacturer', 'Manufacturer Part')
TEMPLATE_REF = 'LED22'
SWAP_REFS = {f'LED{i}' for i in range(1, 21)}
FROM_VALUE, TO_VALUE = 'XL-1608SURC-06FJ', 'XL-1608UYC-06FJ'
FROM_LCSC, TO_LCSC = 'C7371900', 'C7371901'
SOURCE_REV = '57a460f'
SCH_REL = 'hardware/Business Card v2.kicad_sch'

_REF = re.compile(r'\(property "Reference" "(LED\d+)"')


def _prop_re(key):
    return re.compile(r'(\(property "' + re.escape(key) + r'" ")((?:\\.|[^"\\])*)(")')


def _prop(block, key):
    m = _prop_re(key).search(block)
    return m.group(2) if m else None


def swap(src):
    blocks = [(s, e, src[s:e]) for s, e, head in S._blocks(src) if head in ('footprint', 'symbol')]
    tmpl = [b for _, _, b in blocks if (m := _REF.search(b)) and m.group(1) == TEMPLATE_REF]
    assert len(tmpl) == 1, f'expected exactly one {TEMPLATE_REF}, found {len(tmpl)}'
    want = {k: _prop(tmpl[0], k) for k in KEYS}
    assert want['Value'] == TO_VALUE and want['LCSC'] == TO_LCSC, f'{TEMPLATE_REF} is not the amber part: {want}'
    assert all(v is not None for v in want.values()), f'{TEMPLATE_REF} lacks a field: {want}'
    out, last, seen = [], 0, set()
    for s, e, b in blocks:
        m = _REF.search(b)
        if not m or m.group(1) not in SWAP_REFS:
            continue
        ref = m.group(1)
        assert _prop(b, 'Value') == FROM_VALUE and _prop(b, 'LCSC') == FROM_LCSC, f'{ref} is not the red part'
        nb = b
        for k in KEYS:
            nb, n = _prop_re(k).subn(lambda mm: mm.group(1) + want[k].replace('\\', '\\\\') + mm.group(3), nb, count=1)
            assert n == 1, f'{ref}: field {k} missing'
        out.append(src[last:s])
        out.append(nb)
        last = e
        seen.add(ref)
    out.append(src[last:])
    assert seen == SWAP_REFS, f'swapped {sorted(seen)}, expected LED1..LED20'
    return ''.join(out), len(seen)


def main():
    repo = os.path.abspath(os.path.join(HERE, '..', '..'))
    src = subprocess.run(['git', '-C', repo, 'show', f'{SOURCE_REV}:{SCH_REL}'], capture_output=True, check=True).stdout.decode('utf-8')
    new, n = swap(src)
    import fixes
    new = fixes.apply(new, absolute_at=True)
    from kpcb import parse
    parse(new)
    with open(os.path.join(repo, SCH_REL), 'w', encoding='utf-8', newline='') as f:
        f.write(new)
    print(f'schematic: {n} LEDs -> {TO_VALUE} ({TO_LCSC}), R4 LCSC C25076 added, C1 -> C1552; wrote {SCH_REL}')


if __name__ == '__main__':
    main()
