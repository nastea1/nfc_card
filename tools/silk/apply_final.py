#!/usr/bin/env python3
"""Write the final retro silkscreen into the board, deterministically.

Source is ALWAYS the pristine board at commit 57a460f (Wilson Harper's artwork intact), never the
working-tree file, so re-running gives byte-identical output regardless of what is on disk:
  1. remove Wilson's front artwork        (silklib.old_front_remover, 212 top-level F.SilkS items)
  2. remove the old back credit           (back_credit.back_remover, 20 top-level B.SilkS items)
  3. append the final front (black mask, inverted QR) + back credit pieces as filled gr_poly
  4. drop the removed items' UUIDs from every (group ... (members ...)) list (the old back credit
     lived in group a70294e8); assert no group references an undefined UUID
  5. set the stackup colours for KiCad's 3D viewer: F/B.Mask "Black", F/B.SilkS "White"
     (the JLCPCB order form must ALSO be set to Black mask / White silk - this does not do that)
  6. title block: keep Wilson's lines (company, comment 1, comment 2) as they are - they are his
     Notices - and ADD a modification notice (comment 3/4) and bump rev (CERN-OHL-S-2.0 s.3.3(b))
  7. LED1..LED20 part fields red XL-1608SURC-06FJ -> amber XL-1608UYC-06FJ (tools/bom/leds.py;
     the schematic gets the same swap from `python tools/bom/leds.py`); R4 gets its missing LCSC
     C25076 (tools/bom/fixes.py - absent in the original, so JLCPCB would not place it)
  8. write hardware/Business Card v2.kicad_pcb in place and print counts

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
sys.path.insert(0, os.path.join(HERE, '..', 'bom'))
import leds  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
PCB_REL = 'hardware/Business Card v2.kicad_pcb'
SOURCE_REV = S.SOURCE_REV
EXPECT_REMOVED = 212 + 20
REV = '2-ap1'
MOD_NOTICES = {3: 'Modified by Aaron Pursell 2026-10-07: retro silkscreen front + back credit, amber LEDs',
               4: 'This fork: hardware CERN-OHL-S-2.0 (LICENSE.md); src github.com/nastea1/nfc_card'}
UUID_RE = re.compile(r'"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"')
STACKUP_COLOURS = {'F.SilkS': 'White', 'F.Mask': 'Black', 'B.Mask': 'Black', 'B.SilkS': 'White'}


def source_text():
    r = subprocess.run(['git', '-C', S.REPO, 'show', f'{SOURCE_REV}:{PCB_REL}'],
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


def removed_uuids(src, remover):
    """UUIDs of the top-level blocks that S.apply will delete (same _blocks walk, same remover)."""
    out = set()
    for s, e, head in S._blocks(src):
        if remover(head, src[s:e]):
            out.update(re.findall(r'\(uuid "([0-9a-f-]{36})"\)', src[s:e]))
    return out


_GROUP = re.compile(r'(\t\(group "[^"]*"\n\t\t\(uuid "[0-9a-f-]{36}"\)\n)\t\t\(members ([^()]*)\)\n\t\)\n')


def prune_groups(src, gone):
    """Remove UUIDs in `gone` from every group's member list, re-wrapped the way KiCad 9 writes it
    (2 per line, continuation lines indented 3 tabs); a group left empty is deleted."""
    stats = []

    def fix(m):
        mem = UUID_RE.findall(m.group(2))
        keep = [u for u in mem if u not in gone]
        stats.append((len(mem), len(mem) - len(keep)))
        if len(keep) == len(mem):
            return m.group(0)
        if not keep:
            return ''
        pairs = [' '.join(f'"{u}"' for u in keep[i:i + 2]) for i in range(0, len(keep), 2)]
        return m.group(1) + '\t\t(members ' + '\n\t\t\t'.join(pairs) + ')\n\t)\n'

    new = _GROUP.sub(fix, src)
    assert len(stats) == src.count('\t(group "'), 'a group block did not match the expected layout'
    return new, stats


def undefined_group_members(src):
    """Group members that no (uuid ...) in the board defines (0 in the original board)."""
    defined = set(re.findall(r'\(uuid "([0-9a-f-]{36})"\)', src))
    mem = [u for m in _GROUP.finditer(src) for u in UUID_RE.findall(m.group(2))]
    return [u for u in mem if u not in defined]


def set_title_block(src):
    s0 = src.index('\t(title_block\n')
    s1 = src.index('\n\t)\n', s0) + 4
    tb = src[s0:s1]
    for k in ('(company "Made by Wilson Harper")', '(comment 1 ', '(comment 2 '):
        assert k in tb, f'title_block: expected {k} (Wilson\'s notice) to be present'
    assert '(comment 3 ' not in tb and '(comment 4 ' not in tb
    tb, n = re.subn(r'\(rev "[^"]*"\)', f'(rev "{REV}")', tb)
    assert n == 1
    add = ''.join(f'\t\t(comment {k} "{v}")\n' for k, v in sorted(MOD_NOTICES.items()))
    tb = tb[:-3] + add + tb[-3:]
    return src[:s0] + tb + src[s1:], tb


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
    assert not undefined_group_members(src), 'source board already has dangling group members'
    gone = removed_uuids(src, remover)
    new, removed = S.apply(src, front + back, remover)
    assert removed == EXPECT_REMOVED, f'removed {removed} blocks, expected {EXPECT_REMOVED}'
    assert len(gone) == EXPECT_REMOVED, f'{len(gone)} removed UUIDs, expected {EXPECT_REMOVED}'
    new, gstats = prune_groups(new, gone)
    dangling = undefined_group_members(new)
    assert not dangling, f'{len(dangling)} group members reference undefined UUIDs'
    new, colours = set_stackup_colours(new)
    new, tb = set_title_block(new)
    new, nled = leds.swap(new)
    assert nled == 20
    import fixes
    new = fixes.apply(new, absolute_at=False)
    parse(new)
    path = os.path.join(REPO, PCB_REL)
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(new)
    print(f'source        : git {SOURCE_REV}:{PCB_REL} ({len(src)} chars)')
    print(f'removed blocks: {removed} (Wilson front art 212 + old back credit 20)')
    print(f'added gr_poly : front F.SilkS {len(front)}, back B.SilkS {len(back)}, total {len(front) + len(back)}')
    print(f'groups        : (members, pruned) {gstats}; undefined members now {len(dangling)}')
    print(f'stackup       : {colours}')
    print(f'leds          : {nled} x LED1..20 -> {leds.TO_VALUE} ({leds.TO_LCSC})')
    print('title_block   :\n' + tb.rstrip())
    print(f'wrote         : {path} ({len(new)} chars)')


if __name__ == '__main__':
    main()
