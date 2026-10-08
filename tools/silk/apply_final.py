#!/usr/bin/env python3
"""Write the final retro silkscreen into the board, deterministically.

Source is ALWAYS the pristine board at commit 57a460f (Wilson Harper's artwork intact), never the
working-tree file, so re-running gives byte-identical output regardless of what is on disk:
  1. remove Wilson's front artwork        (silklib.old_front_remover, 212 top-level F.SilkS items)
  2. remove the old back credit           (back_credit.back_remover, 20 top-level B.SilkS items)
  3. append the final front (black mask, inverted QR) + back credit pieces as filled gr_poly
  4. set the stackup colours for KiCad's 3D viewer: F/B.Mask "Black", F/B.SilkS "White"
     (the JLCPCB order form must ALSO be set to Black mask / White silk - this does not do that)
  5. write hardware/Business Card v2.kicad_pcb in place and print counts

Run:  cd /root/nfc_card/tools/silk && /root/nfc-tools/.venv/bin/python -s apply_final.py
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'designs'))
import silklib as S  # noqa: E402
from kpcb import parse  # noqa: E402
from back_credit import back_remover, build_back  # noqa: E402
import final  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
PCB_REL = 'hardware/Business Card v2.kicad_pcb'
SOURCE_REV = '57a460f'
EXPECT_REMOVED = 212 + 20
STACKUP_COLOURS = {'F.SilkS': 'White', 'F.Mask': 'Black', 'B.Mask': 'Black', 'B.SilkS': 'White'}


def source_text():
    r = subprocess.run(['git', '-C', REPO, 'show', f'{SOURCE_REV}:{PCB_REL}'],
                       capture_output=True, check=True)
    return r.stdout.decode('utf-8')


def set_stackup_colours(src):
    """Rewrite (color "...") inside the (stackup ...) sub-blocks of the named layers only."""
    s0 = src.index('(stackup')
    depth, i = 0, s0
    while True:                       # find the end of the stackup block
        if src[i] == '(':
            depth += 1
        elif src[i] == ')':
            depth -= 1
            if depth == 0:
                break
        i += 1
    block = src[s0:i + 1]
    done = {}
    for lay, col in STACKUP_COLOURS.items():
        pat = re.compile(r'(\(layer "' + re.escape(lay) + r'"\s*\(type "[^"]*"\)\s*\(color ")[^"]*("\))')
        block, n = pat.subn(lambda m: m.group(1) + col + m.group(2), block)
        assert n == 1, f'stackup layer {lay}: expected 1 colour, found {n}'
        done[lay] = col
    return src[:s0] + block + src[i + 1:], done


def deterministic_uuids():
    """S.apply stamps each new gr_poly with uuid.uuid4(); swap in name-based UUIDs (uuid5 over a
    running counter) so the written board is byte-identical on every run."""
    import itertools
    import uuid
    ns = uuid.UUID('6f1c2b1e-5a7d-4c3e-9b8a-0d7e5c4b3a29')
    ctr = itertools.count()
    uuid.uuid4 = lambda: uuid.uuid5(ns, f'nfc_card retro-silk {next(ctr)}')


def source_geom(src, tmp):
    """The back layout reads the ORIGINAL board's geometry (U2 glyph positions, kept silk), so
    derive it from the same 57a460f source with geom.py instead of relying on an external
    geom.json. Points S.load_geom() (NFC_GEOM) at it."""
    pcb, js = os.path.join(tmp, 'source.kicad_pcb'), os.path.join(tmp, 'geom_source.json')
    with open(pcb, 'w', encoding='utf-8', newline='') as f:
        f.write(src)
    subprocess.run([sys.executable, '-s', os.path.join(HERE, 'geom.py'), pcb, js],
                   cwd=HERE, check=True, capture_output=True)
    os.environ['NFC_GEOM'] = js


def main():
    import tempfile
    deterministic_uuids()
    src = source_text()
    tmp = tempfile.TemporaryDirectory()
    source_geom(src, tmp.name)
    front = final.build('black')
    back = build_back('black')
    remover = lambda head, text: S.old_front_remover(head, text) or back_remover(head, text)  # noqa: E731
    new, removed = S.apply(src, front + back, remover)
    assert removed == EXPECT_REMOVED, f'removed {removed} blocks, expected {EXPECT_REMOVED}'
    new, colours = set_stackup_colours(new)
    parse(new)
    path = os.path.join(REPO, PCB_REL)
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(new)
    print(f'source        : git {SOURCE_REV}:{PCB_REL} ({len(src)} chars)')
    print(f'removed blocks: {removed} (Wilson front art 212 + old back credit 20)')
    print(f'added gr_poly : front F.SilkS {len(front)}, back B.SilkS {len(back)}, total {len(front) + len(back)}')
    print(f'stackup       : {colours}')
    print(f'wrote         : {path} ({len(new)} chars)')


if __name__ == '__main__':
    main()
