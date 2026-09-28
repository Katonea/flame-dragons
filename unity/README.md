# Unity build

The same game as the one-HTML-file build at the site root, rebuilt in Unity 6
on URP. Open `../unity/` and it runs in the browser; portrait, 405x720.

Two things about this directory are deliberate:

**It is gzip, not Brotli.** GitHub Pages cannot set `Content-Encoding`, and a
browser handed raw Brotli bytes under `application/octet-stream` does not start
the player at all. Unity only embeds a decompression fallback for gzip, so this
build carries its own decompressor and costs 16.3MB instead of 12.4MB.

**The level is generated, not extracted.** The pictures and shooter layout come
from `tools/gen_levels.py` in this repo. Only the schema is shared with the
reference game.
