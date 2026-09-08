# Build 100 original levels for this build.
#
# Nothing here is derived from the original level files: the pictures are
# procedural motifs of my own and the shooter/ammo layout is generated. What IS
# reused is the SCHEMA and the invariants verified against the original
# (UNITY_SPEC 4.2 / 4.5):
#
#   - SlotCount == ConveyorLimit == 5                                    [M]
#   - per-material ammo == that colour's pixel count, EXACTLY            [M]
#   - shooter ammo in 10 / 20 / 30 / 40                                  [M]
#   - 3..5 queues, ids unique per level
#   - pictures peel from the outside in, so every colour always has a reachable
#     outermost pixel (the targeting rule of 6.5.2)
#
# Solvability is structural, not lucky: bands and rings expose a whole colour at
# the edge at every step. The browser sim is the real check.
import json, os, random, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, '..', 'levels-own'))

DIFFS = ['Easy'] * 45 + ['Medium'] * 25 + ['Hard'] * 20 + ['Very Hard'] * 10
AMMO_STEPS = [10, 20, 30, 40]


def bands(w, h, cols, horizontal=True):
    n = len(cols)
    px = []
    for y in range(h):
        for x in range(w):
            k = (y if horizontal else x) * n // (h if horizontal else w)
            px.append((x, y, cols[k]))
    return px


def rings(w, h, cols):
    px = []
    steps = min(w, h) // 2 + 1
    for y in range(h):
        for x in range(w):
            d = min(x, y, w - 1 - x, h - 1 - y)
            px.append((x, y, cols[(d * len(cols) // steps) % len(cols)]))
    return px


def checker(w, h, cols, cell):
    px = []
    for y in range(h):
        for x in range(w):
            px.append((x, y, cols[((x // cell) + (y // cell)) % len(cols)]))
    return px


def frame(w, h, cols):
    px = []
    t = max(2, min(w, h) // 5)
    for y in range(h):
        for x in range(w):
            edge = x < t or y < t or x >= w - t or y >= h - t
            cross = abs(x - w // 2) < max(1, t // 2) or abs(y - h // 2) < max(1, t // 2)
            px.append((x, y, cols[0] if edge else (cols[1] if cross else cols[2 % len(cols)])))
    return px


def stripes_diag(w, h, cols):
    px = []
    band = max(2, (w + h) // (len(cols) * 3))
    for y in range(h):
        for x in range(w):
            px.append((x, y, cols[((x + y) // band) % len(cols)]))
    return px


MOTIFS = [
    ('bands-h', lambda w, h, c: bands(w, h, c, True)),
    ('bands-v', lambda w, h, c: bands(w, h, c, False)),
    ('rings', rings),
    ('checker', lambda w, h, c: checker(w, h, c, max(2, min(w, h) // 4))),
    ('frame', frame),
    ('diag', stripes_diag),
]


def make_shooters(counts, rng):
    """{material: pixels} -> shooters whose ammo sums EXACTLY per colour."""
    out = []
    for mat, need in sorted(counts.items()):
        left = need
        while left > 0:
            if left < AMMO_STEPS[0]:
                step = left
            else:
                step = max(a for a in AMMO_STEPS if a <= left)
                if 0 < left - step < AMMO_STEPS[0]:
                    step = left          # fold the remainder in, keep it exact
            out.append({'material': mat, 'ammo': step})
            left -= step
    rng.shuffle(out)
    return out


EMPTY_PIC = {
    'keys': {'Keys': []}, 'surprisePixels': {'SurprisePixels': []},
    'pixelPipes': {'Pipes': []}, 'gates': {'Gates': []}, 'walls': {'Walls': []},
    'snakes': {'Snakes': []}, 'eggBoxes': {'EggBoxes': []},
    'pixelIceBlocks': {'PixelIceBlocks': []}, 'pixelWoodBlocks': {'PixelWoodBlocks': []},
    'pixelColorDoors': {'Doors': []}, 'goldenEggs': {'GoldenEggs': []},
    'biscuits': {'Biscuits': []}, 'splitObjects': {'SplitObjects': []},
    'ufos': {'Ufos': []}, 'pumpkins': {'Pumpkins': []}, 'curtains': {'Curtains': []},
    'shooterCages': {'Cages': []}, 'coloredShooterCages': {'Cages': []},
    'beadGroups': {'BeadGroups': []}, 'multiSnakes': {'MultiSnakes': []},
    'beanBoxes': {'BeanBoxes': []}, 'musicToys': {'MusicToys': []},
    'crossbows': {'Crossbows': []}, 'accordions': {'Accordions': []},
    'matryoshkas': {'Matryoshkas': []}, 'spaceships': {'Spaceships': []},
}


def build(n, rng):
    diff = DIFFS[n - 1]
    span = {'Easy': (14, 20), 'Medium': (18, 26), 'Hard': (22, 30), 'Very Hard': (26, 34)}[diff]
    w = rng.randint(*span)
    h = rng.randint(*span)
    ncol = {'Easy': 3, 'Medium': 4, 'Hard': 5, 'Very Hard': 6}[diff]
    name, fn = MOTIFS[(n - 1) % len(MOTIFS)]
    # rings and frames peel STRICTLY from the outside, so only one colour is
    # shootable at a time; more than four makes the order punishing rather than
    # interesting. Bands/checker/diag expose several colours at once, so they
    # keep the full count.
    if name in ('rings', 'frame'):
        ncol = min(ncol, 4)
    cols = rng.sample(range(34), ncol)
    cells = fn(w, h, cols)

    pixels, counts = [], {}
    for x, y, m in cells:
        pixels.append({'x': x, 'y': y, 'material': m, 'areaX': 1, 'areaY': 1})
        counts[m] = counts.get(m, 0) + 1

    shooters = make_shooters(counts, rng)
    nq = 3 if diff in ('Easy', 'Medium') else rng.choice([4, 5])
    queues = [[] for _ in range(nq)]
    for i, sh in enumerate(shooters):
        queues[i % nq].append(dict(sh, id=i))

    # alignTolerance is 0.15 world units (9.1) and a cell is
    # physicalWidth / max(W, H); keep the cell close to the tolerance so every
    # row and column is actually hittable, and stay inside the original's
    # observed 5.0..7.0 range.
    phys = min(7.0, max(5.0, 0.165 * max(w, h)))
    return {
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
        'motif': name, 'author': 'generated for this build',
    }


def main():
    os.makedirs(OUT, exist_ok=True)
    rng = random.Random(20260908)
    man = []
    for n in range(1, 101):
        lvl = build(n, rng)
        json.dump(lvl, open(os.path.join(OUT, '%d.json' % n), 'w'), separators=(',', ':'))
        pid = lvl['PixelImageData']
        ammo = sum(s['ammo'] for q in lvl['QueueGroup']['shooterQueues'] for s in q['shooters'])
        assert ammo == len(pid['pixels']), (n, ammo, len(pid['pixels']))
        man.append({'n': n, 'd': lvl['Difficulty'], 'slots': 5, 'lim': 5,
                    'px': len(pid['pixels']), 'f': {}})
    json.dump(man, open(os.path.join(OUT, 'manifest.json'), 'w'), separators=(',', ':'))
    from collections import Counter
    print('wrote %d levels to %s' % (len(man), OUT))
    print('difficulty:', dict(Counter(m['d'] for m in man)))
    px = sorted(m['px'] for m in man)
    print('pixels min/med/max: %d / %d / %d' % (px[0], px[50], px[-1]))
    print('motifs:', dict(Counter(build(n, random.Random(20260908))['motif'] for n in range(1, 7))))


if __name__ == '__main__':
    main()
