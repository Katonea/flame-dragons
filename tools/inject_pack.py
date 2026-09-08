# Swap a freshly built pack/levels.js into index.html, in place.
#
# build_mine.py assembles index.html from scratch and needs the sibling clone it
# cuts the rule core out of. This does not: it only replaces the two PACK
# declarations already sitting at the top of index.html, so the level pipeline
# still works on a machine that has nothing but this repository.
#
#     python tools/make_pack.py && python tools/inject_pack.py
#
# Everything else in index.html - the art, the simulation, the lobby, the shop -
# is left untouched.
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PAGE = os.path.join(ROOT, 'index.html')
PACK = os.path.join(ROOT, 'pack', 'levels.js')

PACK_DECL = r'const PACK = \[.*?\];\n'
MAN_DECL = r'const PACK_MAN = \[.*?\];\n'


def one(pattern, text, what):
    """Exactly one match, or the file is not shaped the way this assumes."""
    found = re.findall(pattern, text, re.S)
    if len(found) != 1:
        sys.exit('expected 1 %s, found %d - aborting without writing' % (what, len(found)))
    return found[0]


def main():
    js = io.open(PACK, encoding='utf-8').read()
    page = io.open(PAGE, encoding='utf-8').read()

    new_pack = one(PACK_DECL, js, 'PACK declaration in the pack')
    new_man = one(MAN_DECL, js, 'PACK_MAN declaration in the pack')
    one(PACK_DECL, page, 'PACK declaration in the page')
    one(MAN_DECL, page, 'PACK_MAN declaration in the page')

    # lambda, not a replacement string: the pack is full of base64 that would
    # otherwise be read as backreferences
    out = re.sub(PACK_DECL, lambda m: new_pack, page, count=1, flags=re.S)
    out = re.sub(MAN_DECL, lambda m: new_man, out, count=1, flags=re.S)

    n = out.count('"gzip:')
    if not n:
        sys.exit('no levels in the new pack; refusing to write')
    if out == page:
        print('index.html already carries this pack, nothing to do')
        return
    io.open(PAGE, 'w', encoding='utf-8', newline='').write(out)
    print('injected %d levels into %s  (%d chars)' % (n, PAGE, len(out)))


if __name__ == '__main__':
    main()
