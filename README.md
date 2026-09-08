# Flame Dragons

A conveyor shooter in **one HTML file**. Queues of dragons ride a belt around a
pixel picture and breathe fire at it; you decide who boards and when. Ten
pictures, no dependencies, no network requests of any kind.

## Run it

Open `index.html`. That is all — the levels are inlined, so there is nothing to
fetch and no server to start.

## Publish it

It is a single static file, so GitHub Pages serves it as-is: push this
repository, then Settings → Pages → Deploy from a branch → `main` / `/ (root)`.
The page lands at `https://<user>.github.io/<repo>/`.

## What is in here

| Path | What it is |
|---|---|
| `index.html` | Everything: the ten levels, the art, the simulation, the lobby, the shop |
| `pack/levels.js` | The generated level pack, inlined into `index.html` at build time |
| `tools/make_pack.py` | Draws the ten pictures as ASCII grids and builds the pack |
| `tools/inject_pack.py` | Swaps a rebuilt pack into `index.html` in place |
| `tools/gen_levels.py` | Generates an abstract level set instead, if you want more |

## The levels

The ten pictures are drawn by hand in `tools/make_pack.py` as ASCII grids — one
character per pixel, a legend mapping each character to a palette id:

```
...HH................HH...      S: scales   H: horns
......SSSSSSSSSSSSSS......      E: eyes     N: nostrils
...SSSEEESSSSSSSSEEESSS...      D: jaw      M: mouth
.....DDDDDDDDDDDDDDDD.....
```

The generator derives everything the simulation needs and checks the two things
that decide whether a level is playable at all:

- **Ammo is exact.** Each colour's shooters carry precisely that colour's pixel
  count, split into chunks inside the 10–40 band. A clear spends every last
  shot; all ten finish at exactly `fired == pixels`.
- **The peel terminates.** A shooter can only hit the *surface* pixel of a scan
  line, so a colour walled in by another sits idle until its cover is gone.
  `peel()` strips the picture the way the game does and asserts every pass
  removes something, which proves no colour is trapped forever.

Difficulty ramps with size and colour count: 새싹 (14×14, 3 colours, 92 pixels)
through 드래곤 (20×19, 6 colours, 284 pixels).

### Rebuilding them

```bash
python tools/make_pack.py && python tools/inject_pack.py
```

Edit a picture in `tools/make_pack.py` - its ASCII grid or its legend -
then run those two and reload. The build is reproducible: run it twice and the
second run reports nothing to do.

## Art

There are **zero image files** — check the network tab, it is empty. `mk(w, h,
draw)` rasterises a draw function into an offscreen canvas once and `ART` holds
the results, so every sprite, icon and lobby ornament is canvas paths and CSS.

The shooter is a dragon, one species, drawn as a sticker: a soft pastel blob
with a thick dark outline, a white belly, two leaf fins, a small wing, dot eyes,
blush and a little smile. The outline is a heavily darkened version of the
material tint, so the silhouette holds at any hue — **colour is the gameplay
signal**, and it is the only thing that changes between shooters. Sprites are
cached per (material, blink).

It has no cannon: a shot is fire out of the mouth. `drawFlame` draws a teardrop
whose head is the shooter's own material colour, so a volley reads as flame
rather than as coloured bullets, plus a burst at the mouth for the first 40 % of
the flight.

The 34 material colours are hues walked in 97° steps with alternating tone,
named after the hue they land on. Levels carry material *ids* only, so the
palette was free.

## Belt speed

The base belt runs at half the reference speed (`BELT_TUNE = 0.5`), because at
this on-screen scale the full rate reads like an endgame from the first second.
The AutoFinisher's `×2.0` then lands back on it for the last stretch — same
shape, one notch slower throughout.

The AutoFinisher is a one-shot latch: it fires when the remaining shooter count
drops to the belt's slot count, rechecked on every disappearance. It detaches
the walls and stops shooters being ejected at the path end, on top of the
speed-up.

## Meta

- Hearts: 5. A fail costs one, **and so does walking out of a level in
  progress** (the 로비 button asks first). Empty hearts refill one per 30
  minutes, or all at once in the shop for 150 gold.
- Gold: a clear pays `40 + 10 × difficulty pips` (Easy 50 … Very Hard 80).
- Powerups are bought in the shop and the stock persists; a level starts with
  what you own.
- Stars = levels cleared. Progress lives in `localStorage` under `bb_meta`; the
  초기화 button wipes it.
- Two tabs only: 맵 and 상점.

## Where the rules came from

The simulation core is reverse engineered from another build of this genre and
kept unchanged on purpose — it is the verified part, and the comments in
`index.html` carry the evidence grade and address for every constant. No level
data, art or asset of anyone else's ships in this repository.
