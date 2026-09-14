# Build the 50-level pack that ships inside index.html.
#
# The pictures live in tools/pictures.py as ASCII grids: one character per
# source pixel, a legend mapping each character to a palette id, '.' for empty.
# They are mine, drawn by hand. Nothing is derived from another game's level
# files, so this pack is safe to publish.
#
# The grids are drawn at HALF the shipping resolution and doubled here by
# scale2x. That is deliberate: the reference build's levels run 32..48 cells
# wide and a few hundred to ~1900 pixels, and a grid that size is miserable to
# draw and diff by hand. Drawing at half scale keeps the source readable while
# the shipped picture lands in the reference band.
#
# The SCHEMA and its invariants are the ones the simulation needs:
#   - SlotCount == ConveyorLimit == 5
#   - per-material ammo == that colour's pixel count, EXACTLY
#   - shooter ammo inside the 10..40 band the original uses (see split)
#   - no feature containers: these are plain pictures
#
# Layering rule that keeps them solvable: a shooter can only hit the SURFACE
# pixel of a scan line, so every colour needs a pixel on the silhouette at the
# start or it sits idle until the colour covering it peels away. peel() below
# strips a picture the way the game does and proves the board empties.
#
# Output: pack/levels.js, inlined by build_mine.py.
import base64
import gzip
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_levels import EMPTY_PIC
from pictures import PACK

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, '..', 'pack'))
# The same fifty levels unpacked: readable, diffable JSON. Generated output,
# not input - edit a picture's ASCII grid above and rebuild.
JSON_OUT = os.path.abspath(os.path.join(HERE, '..', 'levels-json'))

# --------------------------------------------------------------------- build


def grid(art):
    rows = art.strip('\n').split('\n')
    w = max(len(r) for r in rows)
    rows = [r.ljust(w, '.') for r in rows]
    while rows and set(rows[0]) == {'.'}:
        rows.pop(0)
    while rows and set(rows[-1]) == {'.'}:
        rows.pop()
    keep = [c for c in range(w) if any(r[c] != '.' for r in rows)]
    return [r[keep[0]:keep[-1] + 1] for r in rows]


def scale2x(rows):
    """Double the grid, rounding diagonal steps instead of squaring them.

    Plain nearest-neighbour doubling would keep every staircase exactly as
    drawn, only twice as chunky. This is the EPX/scale2x rule: a corner pixel
    is replaced by its neighbour when the two neighbours on that side agree and
    the two on the other side do not, which rounds a 45-degree step and leaves
    flat runs alone. Empty cells take part, so silhouettes round off too.
    """
    h, w = len(rows), len(rows[0])

    def at(x, y):
        return rows[y][x] if 0 <= x < w and 0 <= y < h else '.'

    out = []
    for y in range(h):
        top, bot = [], []
        for x in range(w):
            p = rows[y][x]
            a, b = at(x, y - 1), at(x + 1, y)
            c, d = at(x - 1, y), at(x, y + 1)
            top.append(a if (c == a and c != d and a != b) else p)
            top.append(b if (a == b and a != c and b != d) else p)
            bot.append(c if (d == c and d != b and c != a) else p)
            bot.append(d if (b == d and b != a and d != c) else p)
        out.append(''.join(top))
        out.append(''.join(bot))
    return out


def peel(rows, name):
    """Peel the picture the way the game does and return the colours per pass.

    A shooter hits only the first live pixel walking in from an edge, so each
    pass strips exactly those surface pixels. If a pass removes nothing while
    pixels remain, some colour is walled in forever and the level is unwinnable.
    """
    h, w = len(rows), len(rows[0])
    live = {(x, y) for y in range(h) for x in range(w) if rows[y][x] != '.'}
    passes = []
    while live:
        surface = set()
        for x in range(w):
            for ys in (range(h), range(h - 1, -1, -1)):
                for y in ys:
                    if (x, y) in live:
                        surface.add((x, y))
                        break
        for y in range(h):
            for xs in (range(w), range(w - 1, -1, -1)):
                for x in xs:
                    if (x, y) in live:
                        surface.add((x, y))
                        break
        assert surface, '%s: %d pixels walled in' % (name, len(live))
        passes.append({rows[y][x] for x, y in surface})
        live -= surface
    return passes


def split(need):
    """One colour's pixel count -> shooter ammo values summing EXACTLY to it.

    gen_levels' splitter is greedy off 10/20/30/40 and folds the remainder into
    the last shooter, which can push it past 40. Here the count is divided into
    near-equal chunks around 21 instead, so every shooter lands in the 10..40
    band the original uses and a level carries a decision's worth of them
    rather than one fat shooter per colour.
    """
    if need <= 26:
        return [need]
    k = max(2, round(need / 21))
    base, rem = divmod(need, k)
    return [base + (1 if i < rem else 0) for i in range(k)]


def build(name, diff, nq, art, legend):
    rows = scale2x(grid(art))
    h, w = len(rows), len(rows[0])
    passes = peel(rows, name)
    late = sorted(set(legend) - passes[0])

    pixels, counts = [], Counter()
    for y in range(h):
        for x in range(w):
            ch = rows[y][x]
            if ch == '.':
                continue
            # ASCII row 0 is the top; the board's y grows upward
            pixels.append({'x': x, 'y': h - 1 - y, 'material': legend[ch],
                           'areaX': 1, 'areaY': 1})
            counts[legend[ch]] += 1

    # Deal the shooters so consecutive queue heads offer different colours:
    # cycle the materials biggest first, then round-robin into the queues. A
    # player tapping heads in order always has a surface colour available.
    by_mat = {m: [{'material': m, 'ammo': a} for a in split(counts[m])]
              for m in counts}
    mats = sorted(by_mat, key=lambda m: -counts[m])
    order = []
    while any(by_mat.values()):
        for m in mats:
            if by_mat[m]:
                order.append(by_mat[m].pop(0))
    queues = [[] for _ in range(nq)]
    for i, sh in enumerate(order):
        queues[i % nq].append(dict(sh, id=i))

    # alignTolerance is 0.15 world units and a cell is physicalWidth/max(W,H);
    # keep the cell near the tolerance so every row and column stays hittable,
    # inside the 5.0..7.0 range the simulation expects.
    phys = min(7.0, max(5.0, 0.165 * max(w, h)))
    lvl = {
        'Difficulty': diff, 'HasTimeLimit': False, 'TimeLimit': 0,
        'SlotCount': 5, 'ConveyorLimit': 5,
        'QueueGroup': {'shooterQueues': [{'shooters': q} for q in queues]},
        'SurpriseShooters': {'Shooters': []}, 'ConnectedShooters': {'Connections': []},
        'Locks': {'Shooters': []}, 'ShooterPipes': {'Pipes': []},
        'Hammers': {'Shooters': []}, 'ShooterIceBlocks': {'Blocks': []},
        'ChainedShooters': {'Chains': []}, 'BullTotems': {'Totems': []},
        'MusicToyMallets': {'Mallets': []}, 'SlotCages': {'Cages': []},
        'AstronautShooters': {'Shooters': []}, 'ConveyorDoors': {'Doors': []},
        'PixelImageData': dict(EMPTY_PIC, **{
            'width': w, 'height': h,
            'physicalWidth': round(phys, 2), 'physicalHeight': round(phys, 2),
            'pixels': pixels, 'pixelHealths': [],
        }),
        'isValid': True, 'validationErrors': [],
        'picture': name, 'author': 'drawn for this build',
    }
    return lvl, len(passes), late


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(JSON_OUT, exist_ok=True)
    blobs, man = [], []
    for i, (name, diff, nq, (art, legend)) in enumerate(PACK, 1):
        lvl, npass, late = build(name, diff, nq, art, legend)
        pid = lvl['PixelImageData']

        need = Counter(p['material'] for p in pid['pixels'])
        sup = Counter()
        for q in lvl['QueueGroup']['shooterQueues']:
            for s in q['shooters']:
                sup[s['material']] += s['ammo']
        assert need == sup, (i, name, dict(need), dict(sup))

        raw = json.dumps(lvl, separators=(',', ':')).encode('utf-8')
        # mtime=0: gzip stamps the current time into its header by default, which
        # would make every rebuild produce a different pack and a noisy diff.
        blob = gzip.compress(raw, 9, mtime=0)
        blobs.append('gzip:' + base64.b64encode(blob).decode())

        with open(os.path.join(JSON_OUT, '%d.json' % i), 'w',
                  encoding='utf-8') as fh:
            json.dump(lvl, fh, ensure_ascii=False, indent=1)

        # what the game loads is the blob, so prove the blob still decodes to
        # the level that was just built. Both outputs come from this same
        # object, so the readable copy cannot describe anything else.
        assert json.loads(gzip.decompress(blob)) == lvl, (i, name)

        man.append({'n': i, 'd': diff, 'slots': 5, 'lim': 5,
                    'px': len(pid['pixels']), 'name': name, 'f': {}})
        nsh = sum(len(q['shooters']) for q in lvl['QueueGroup']['shooterQueues'])
        print('%2d %-8s %-10s %2dx%-2d %4d px %d colours %2d shooters '
              '%2d peels late:%s'
              % (i, name, diff, pid['width'], pid['height'], len(pid['pixels']),
                 len(need), nsh, npass, late or '-'))

    js = ("/* The fifty pictures of this build, drawn by hand as ASCII grids in\n"
          "   tools/pictures.py and generated by tools/make_pack.py. Nothing here\n"
          "   comes from another game's level data. Each entry is gzipped JSON,\n"
          "   base64'd, which fetchLevel already knows how to read. */\n"
          'const PACK = ' + json.dumps(blobs) + ';\n'
          'const PACK_MAN = ' + json.dumps(man, ensure_ascii=False) + ';\n')
    path = os.path.join(OUT, 'levels.js')
    open(path, 'w', encoding='utf-8').write(js)
    print('\nwrote %s  %.1f KB' % (path, len(js.encode('utf-8')) / 1024))
    print('unpacked copies in %s' % JSON_OUT)


if __name__ == '__main__':
    main()
