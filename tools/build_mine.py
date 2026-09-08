# Assemble pixelflow-mine/index.html: the verified simulation core from the
# clone, with an entirely hand-written art layer (no extracted PNGs), a new
# lobby and a shop. Run: python tools/build_mine.py
import io, os, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Locate both trees relative to this file, so the builder works wherever the
# project sits: SRC is the sibling clone the rules are cut from, DST is this
# repo.
HERE = os.path.dirname(os.path.abspath(__file__))
DST = os.path.dirname(HERE)
SRC = os.path.join(os.path.dirname(DST), 'pixelflow-clone')
src = io.open(os.path.join(SRC, 'index.html'), encoding='utf-8').read()


def cut(a, b):
    i = src.index(a)
    j = src.index(b, i)
    return src[i:j]


CONSTS = cut('/* TickShooter (0x4ecd01c) is rate driven.',
             '/* ============================== artwork ==============================')
CORE = cut('const cv = document.getElementById',
           '/* ================================ lobby ================================')


# the core's badge() reads Image.naturalWidth; our sprites are canvases
CORE = CORE.replace('const k = size / Math.max(img.naturalWidth, img.naturalHeight);\n'
                    '  ctx.drawImage(img, x, y, img.naturalWidth * k, img.naturalHeight * k);',
                    'const iw = img.naturalWidth || img.width, ih = img.naturalHeight || img.height;\n'
                    '  const k = size / Math.max(iw, ih);\n'
                    '  ctx.drawImage(img, x, y, iw * k, ih * k);')
assert 'const iw = img.naturalWidth' in CORE
# powerup stock comes from the shop, not a flat 1 each
CORE = CORE.replace("    pw: { shuffle: 1, hand: 1, super: 1, slot: 1, demolish: 1, tray: 1 },",
                    "    pw: Object.assign({}, META.pw),   // bought in the shop" + chr(92) + "n"
                    "    leaving: [],                      // fly-off effect")
assert 'META.pw' in CORE

STYLE = """<style>
  /* Flame Dragons. Every pixel of art in this build is drawn by code - the
     sprites are canvas paths (see the `art` module), the lobby and the shop
     are CSS gradients and clip-paths. No image file is loaded anywhere. */
  :root{
    --bg:#120d1c; --panel:#1d1630; --panel2:#2a2044; --line:#3d2f5e;
    --txt:#f1ecff; --dim:#a394c4; --bad:#ff6b8a; --good:#5ee0a8;
    --accent:#7dd3fc; --gold:#ffcf5c;
  }
  *{box-sizing:border-box}
  html,body{margin:0;height:100%}
  body{
    background:var(--bg); color:var(--txt); overflow:hidden;
    font:13px/1.4 "Segoe UI",system-ui,sans-serif;
    display:flex; flex-direction:column; align-items:center;
    -webkit-user-select:none; user-select:none; touch-action:manipulation;
  }
  button{
    font:inherit;font-weight:600;color:var(--txt);background:var(--panel2);
    border:1px solid var(--line);border-radius:9px;padding:5px 9px;cursor:pointer;
  }
  button:hover{background:var(--line)}
  button:disabled{opacity:.4;cursor:default}
  input{
    font:inherit;width:58px;text-align:center;color:var(--txt);
    background:var(--panel);border:1px solid var(--line);border-radius:9px;padding:5px;
  }
  /* ------------------------------- game ------------------------------- */
  body.meta #top, body.meta #stage, body.meta #legend{display:none}
  body:not(.meta) #home{display:none}
  #top{width:100%;max-width:560px;padding:8px 10px;display:flex;gap:6px;align-items:center;flex:0 0 auto}
  #top .grow{flex:1}
  #meta{font-size:12px;color:var(--dim);white-space:nowrap}
  #stage{position:relative;flex:1 1 auto;width:100%;max-width:560px;min-height:0}
  canvas{position:absolute;inset:0;width:100%;height:100%;display:block}
  #overlay{position:absolute;inset:0;display:none;place-items:center;background:rgba(12,8,20,.86);z-index:5}
  #overlay.on{display:grid}
  #card{
    background:linear-gradient(160deg,var(--panel2),var(--panel));
    border:1px solid var(--line);border-radius:18px;
    padding:22px 26px;text-align:center;min-width:250px;
  }
  #card h2{margin:0 0 6px;font-size:22px}
  #card p{margin:0 0 16px;color:var(--dim)}
  #legend{
    width:100%;max-width:560px;flex:0 0 auto;padding:4px 10px 8px;
    display:flex;flex-wrap:wrap;gap:5px;font-size:11px;color:var(--dim);
  }
  .chip{display:flex;align-items:center;gap:4px;background:var(--panel);
    border:1px solid var(--line);border-radius:999px;padding:2px 7px}
  .sw{width:10px;height:10px;border-radius:3px}
  /* -------------------------------- home ------------------------------- */
  #home{
    position:relative;width:100%;max-width:560px;flex:1 1 auto;min-height:0;
    display:flex;flex-direction:column;
    background:
      radial-gradient(120% 60% at 50% -10%, #33245c 0%, transparent 60%),
      linear-gradient(#1a1230, #120d1c 70%);
  }
  #hdr{
    flex:0 0 auto;display:flex;align-items:center;gap:7px;padding:8px 10px;
    background:linear-gradient(#2b2049,#221a3a);
    border-bottom:1px solid var(--line);
  }
  .cur{
    display:flex;align-items:center;gap:4px;padding:3px 10px 3px 4px;border-radius:999px;
    background:rgba(0,0,0,.3);border:1px solid var(--line);
    font-weight:700;font-size:12px;
  }
  .cur img{width:18px;height:18px}
  .cur.g{color:var(--gold)} .cur.h{color:#ff8fa3} .cur.s{color:var(--accent)}
  #avatar{
    width:38px;height:38px;flex:0 0 auto;border-radius:12px;
    background:linear-gradient(150deg,#4b3780,#2a1f47);
    border:1px solid var(--line);display:grid;place-items:center;
  }
  #avatar img{width:30px;height:30px}
  #scroll{flex:1 1 auto;overflow-y:auto;overflow-x:hidden;position:relative}
  #tree{position:relative;width:100%}
  #tree .band{position:absolute;left:0;right:0}
  #tree .spine{
    position:absolute;left:50%;width:8px;margin-left:-4px;border-radius:4px;
    background:linear-gradient(rgba(255,255,255,.16),rgba(255,255,255,.05));
  }
  .nd{position:absolute;left:50%;width:78px;height:86px;margin-left:-39px;cursor:pointer}
  .nd .hex,.nd .hexIn{
    position:absolute;clip-path:polygon(50% 0,100% 25%,100% 75%,50% 100%,0 75%,0 25%);
  }
  .nd .hex{inset:0;background:#0c0817}
  .nd .hexIn{
    inset:4px;background:linear-gradient(155deg,var(--c1),var(--c2));
    display:grid;place-items:center;
  }
  .nd .num{
    position:relative;font-weight:800;font-size:16px;color:#fff;
    text-shadow:0 2px 3px rgba(0,0,0,.55);
  }
  .nd .pips{position:absolute;left:0;right:0;bottom:13px;display:flex;justify-content:center;gap:3px}
  .nd .pips i{width:4px;height:4px;border-radius:50%;background:rgba(255,255,255,.85)}
  .nd.cur{filter:drop-shadow(0 0 8px var(--accent)) drop-shadow(0 0 18px rgba(125,211,252,.55))}
  .nd.cl .hexIn{filter:saturate(.35) brightness(.62)}
  .nd .done{position:absolute;right:2px;top:4px;width:22px;height:22px}
  .nd:active{transform:scale(.94)}
  #nav{
    flex:0 0 auto;display:flex;gap:4px;padding:6px;
    background:linear-gradient(#221a3a,#191230);border-top:1px solid var(--line);
  }
  #nav .nv{
    flex:1;text-align:center;padding:8px 0 6px;border-radius:11px;
    font-weight:700;font-size:12px;color:var(--dim);cursor:pointer;
    border:1px solid transparent;
  }
  #nav .nv.sel{
    color:#fff;border-color:var(--line);
    background:linear-gradient(#3a2b63,#2a1f4a);
  }
  /* ------------------------------ overlays ----------------------------- */
  .sheet{position:absolute;inset:0;z-index:8;display:none;background:rgba(10,7,18,.78);place-items:center}
  .sheet.on{display:grid}
  .panel{
    position:relative;width:min(360px,90%);max-height:84%;overflow:auto;
    border-radius:20px;padding:16px;
    background:linear-gradient(165deg,#33265c,#201839);
    border:1px solid var(--line);box-shadow:0 16px 40px rgba(0,0,0,.5);
  }
  .panel h3{margin:0 0 2px;font-size:17px;text-align:center}
  .panel .sub{margin:0 0 12px;font-size:11px;color:var(--dim);text-align:center}
  .closeX{
    position:absolute;right:10px;top:10px;width:26px;height:26px;border-radius:50%;
    border:1px solid var(--line);background:rgba(0,0,0,.3);color:var(--txt);
    font-weight:800;cursor:pointer;line-height:1;padding:0;
  }
  #cdArt{display:block;width:74px;margin:-52px auto -2px}
  #cdNo{font-size:21px;font-weight:800;text-align:center}
  #cdDiff{
    display:block;width:fit-content;margin:6px auto 8px;padding:3px 14px 4px;
    border-radius:999px;font-weight:800;font-size:11px;color:#160f22;
    background:linear-gradient(var(--c1),var(--c2));
  }
  #cdStats{font-size:12px;color:#cdbff0;text-align:center;margin-bottom:9px}
  #cdFeats{display:flex;flex-wrap:wrap;gap:4px;justify-content:center;margin-bottom:13px}
  .fchip{
    display:flex;align-items:center;gap:3px;background:rgba(0,0,0,.28);
    border:1px solid var(--line);border-radius:999px;padding:2px 8px 2px 3px;
    font-size:11px;font-weight:700;
  }
  .fchip img{width:19px;height:19px}
  .play{
    display:block;width:100%;padding:12px 0;border:0;border-radius:14px;
    font-size:16px;font-weight:800;color:#10240f;cursor:pointer;
    background:linear-gradient(#8ef2b0,#3fbf7a);
    box-shadow:0 4px 0 #2b8f59;
  }
  .play:active{transform:translateY(2px);box-shadow:0 2px 0 #2b8f59}
  .shopRow{
    display:flex;align-items:center;gap:10px;padding:9px;margin-bottom:7px;
    border-radius:14px;background:rgba(0,0,0,.22);border:1px solid var(--line);
  }
  .shopRow img{width:38px;height:38px;flex:0 0 auto}
  .shopRow .nm{font-weight:700}
  .shopRow .ds{font-size:11px;color:var(--dim)}
  .shopRow .own{font-size:11px;color:var(--accent)}
  .buy{
    margin-left:auto;flex:0 0 auto;display:flex;align-items:center;gap:4px;
    padding:7px 11px;border:0;border-radius:11px;font-weight:800;color:#2a1c00;
    background:linear-gradient(#ffdd8a,#f0b429);box-shadow:0 3px 0 #b07d10;cursor:pointer;
  }
  .buy:disabled{background:#4a3f66;color:#8d81ab;box-shadow:none}
  .buy img{width:15px;height:15px}
.nd .ndName{position:absolute;left:50%;top:50%;transform:translate(56px,-50%);
  white-space:nowrap;font-size:13px;font-weight:700;color:#cfc7e6;
  text-shadow:0 1px 3px #000;pointer-events:none}
.nd.cl .ndName{color:#8ee6a6}
</style>"""

MARKUP = """<body>

<div id="home">
  <div id="hdr">
    <div id="avatar"></div>
    <span class="cur h"><img id="icHeart"><span id="cHeart">5</span></span>
    <span class="cur g"><img id="icGold"><span id="cGold">0</span></span>
    <span class="cur s"><img id="icStar"><span id="cStar">0</span></span>
    <span style="flex:1"></span>
    <button id="reset" title="진행도 초기화" style="padding:3px 8px;font-size:11px">초기화</button>
  </div>

  <div id="scroll"><div id="tree"></div></div>

  <div id="nav">
    <div class="nv sel" id="nvMap">맵</div>
    <div class="nv" id="nvShop">상점</div>
  </div>

  <div class="sheet" id="cardSheet"><div class="panel">
    <button class="closeX" id="cdClose">×</button>
    <img id="cdArt">
    <div id="cdNo"></div>
    <span id="cdDiff"></span>
    <div id="cdStats"></div>
    <div id="cdFeats"></div>
    <button class="play" id="cdPlay">PLAY</button>
  </div></div>

  <div class="sheet" id="shopSheet"><div class="panel">
    <button class="closeX" id="shClose">×</button>
    <h3>상점</h3>
    <p class="sub">골드는 클리어로 벌고 여기서 파워업으로 바꾼다. 결제는 없다.</p>
    <div id="shopList"></div>
  </div></div>

</div>

<div id="top">
  <button id="toHome" title="로비로">&#8962;</button>
  <button id="prev">&#9664;</button>
  <input id="lvl" type="number" min="1" max="2300" value="1">
  <button id="next">&#9654;</button>
  <button id="retry">↻</button>
  <button id="mode" title="가림: 지나가는 줄의 가장자리 첫 픽셀만 보이고 그게 자기 색일 때만 쏜다. 전체: 가림 무시">가림</button>
  <span class="grow"></span>
  <span id="meta"></span>
</div>

<div id="stage">
  <canvas id="cv"></canvas>
  <div id="overlay"><div id="card">
    <h2 id="title"></h2><p id="sub"></p><button id="act"></button>
    <button id="ovHome" style="margin-left:6px">로비</button>
  </div></div>
</div>

<div id="legend"></div>

<script>"""

HEADER = """/* ======================================================================
   Flame Dragons - a conveyor shooter in one file.

   The RULES are reverse engineered from another build of this genre (see
   UNITY_SPEC.md; every constant below still carries its evidence grade and the
   address it came from). The simulation core here is that clone's, unchanged on
   purpose: it is the verified part.

   Everything a player sees is mine. The ten pictures are hand drawn as ASCII
   grids by tools/make_pack.py and inlined above as PACK, so no level file of
   anyone else's ships here. Every sprite is drawn with canvas paths in the
   `art` module below - the shooter is a sticker style dragon that breathes fire
   in its own colour - the 34 material colours are my own palette, and the lobby
   and shop are CSS gradients and clip-paths. Open the network tab: zero
   requests, images or otherwise.
   ====================================================================== */
"""

PALETTE = """/* 34 material colours, mine. Level JSONs carry material IDS only, so the hues
   are free; these walk the hue circle in 97-degree steps with alternating tone
   so no two neighbouring ids look alike (the original palette had several
   near-duplicates, which made colour matching guesswork). The name is derived
   from the hue it actually lands on, so the legend never lies. */
const HUE_NAMES = [
  [15,'Red'],[45,'Orange'],[70,'Amber'],[100,'Lime'],[150,'Green'],[175,'Mint'],
  [195,'Cyan'],[225,'Sky'],[255,'Blue'],[280,'Indigo'],[300,'Violet'],
  [330,'Magenta'],[350,'Pink'],[361,'Red']
];
function hsl2hex(h, s, l){
  s /= 100; l /= 100;
  const k = n => (n + h / 30) % 12;
  const a = s * Math.min(l, 1 - l);
  const f = n => l - a * Math.max(-1, Math.min(k(n) - 3, Math.min(9 - k(n), 1)));
  const b = x => Math.round(255 * f(x)).toString(16).padStart(2, '0');
  return '#' + b(0) + b(8) + b(4);
}
const PALETTE = (() => {
  const seen = {}, out = [];
  for (let i = 0; i < 34; i++){
    const h = (i * 97) % 360, s = i % 2 ? 62 : 82, l = i % 3 === 2 ? 70 : 56;
    let nm = (l > 62 ? 'Light ' : s < 70 ? 'Soft ' : '') + HUE_NAMES.find(x => h < x[0])[1];
    seen[nm] = (seen[nm] || 0) + 1;
    if (seen[nm] > 1) nm += ' ' + seen[nm];
    out.push([nm, hsl2hex(h, s, l)]);
  }
  return out;
})();
const colorOf = m => (PALETTE[m] || ['?', '#8b849c'])[1];

"""

ART = r"""/* ============================== art ==============================
   Hand-written sprites. mk() rasterises a draw function once into an offscreen
   canvas; everything that used to be a PNG is one of these. The core's badge()
   and drawPig() take them unchanged (a canvas answers .width/.height instead of
   .naturalWidth, which is the only line of the core that had to bend). */
function mk(w, h, draw){
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  const g = c.getContext('2d');
  draw(g, w, h);
  return c;
}
const ready = im => !!im && ((im.naturalWidth | 0) || (im.width | 0)) > 0;

function rrp(g, x, y, w, h, r){
  g.beginPath();
  g.moveTo(x + r, y);
  g.arcTo(x + w, y, x + w, y + h, r);
  g.arcTo(x + w, y + h, x, y + h, r);
  g.arcTo(x, y + h, x, y, r);
  g.arcTo(x, y, x + w, y, r);
  g.closePath();
}
function starp(g, cx, cy, r1, r2, n){
  g.beginPath();
  for (let i = 0; i < n * 2; i++){
    const a = -Math.PI / 2 + i * Math.PI / n, r = i % 2 ? r2 : r1;
    g[i ? 'lineTo' : 'moveTo'](cx + Math.cos(a) * r, cy + Math.sin(a) * r);
  }
  g.closePath();
}
// mix a hex toward white (t>0) or black (t<0)
function shade(hex, t){
  const n = parseInt(hex.slice(1), 16);
  const to = t > 0 ? 255 : 0, k = Math.abs(t) / 100;
  const ch = s => Math.round(((n >> s) & 255) * (1 - k) + to * k);
  return 'rgb(' + ch(16) + ',' + ch(8) + ',' + ch(0) + ')';
}
function glyph(g, w, h, col, path){          // stroked outline helper
  g.strokeStyle = col; g.lineWidth = Math.max(1.6, w * 0.09);
  g.lineJoin = 'round'; g.lineCap = 'round';
  path(); g.stroke();
}

/* ---------------------------- the shooter ----------------------------
   One species: a dragon, drawn in a sticker style - a soft pastel blob with a
   thick dark outline, a white belly, two leaf fins, one small wing, dot eyes
   and blush. Every stroke is a canvas path; the material colour is the tint and
   the only gameplay signal, and the outline is a much darker version of that
   tint so the silhouette holds at any hue. No cannon: the shot leaves the MOUTH
   as a flame (drawFlame below). Cached per (material, blink). */
function blobPath(g, cx, cy, rx, ry){
  // an egg with a flat, rounded bottom, leaning slightly left like the sticker
  g.beginPath();
  g.moveTo(cx - rx, cy + ry * 0.62);
  g.bezierCurveTo(cx - rx * 1.05, cy - ry * 0.55, cx - rx * 0.72, cy - ry, cx - rx * 0.10, cy - ry);
  g.bezierCurveTo(cx + rx * 0.62, cy - ry, cx + rx * 1.02, cy - ry * 0.30, cx + rx * 0.96, cy + ry * 0.40);
  g.bezierCurveTo(cx + rx * 0.94, cy + ry * 0.90, cx + rx * 0.55, cy + ry, cx + rx * 0.10, cy + ry);
  g.bezierCurveTo(cx - rx * 0.45, cy + ry, cx - rx * 0.99, cy + ry * 0.98, cx - rx, cy + ry * 0.62);
  g.closePath();
}

function drawDragon(g, w, h, col, blink){
  const u = Math.min(w, h);
  const cx = w * 0.48, cy = h * 0.58;
  const rx = u * 0.40, ry = u * 0.33;
  const ink = shade(col, -66);                  // sticker outline
  const light = shade(col, 30);
  const lw = Math.max(1.4, u * 0.052);
  g.lineJoin = 'round'; g.lineCap = 'round';

  // ---- wing, behind, to the right ----
  g.beginPath();
  g.moveTo(cx + rx * 0.55, cy - ry * 0.10);
  g.quadraticCurveTo(cx + rx * 1.55, cy - ry * 0.62, cx + rx * 1.62, cy + ry * 0.10);
  g.quadraticCurveTo(cx + rx * 1.20, cy + ry * 0.02, cx + rx * 1.28, cy + ry * 0.52);
  g.quadraticCurveTo(cx + rx * 0.80, cy + ry * 0.36, cx + rx * 0.55, cy - ry * 0.10);
  g.closePath();
  g.fillStyle = '#fdfdf7'; g.fill();
  g.strokeStyle = ink; g.lineWidth = lw * 0.8; g.stroke();

  // ---- head fins, behind, leaf shaped ----
  for (const f of [[0.02, -1.12, 0.9], [0.62, -0.86, 0.75]]){
    const fx = f[0], fy = f[1], fr = f[2];
    g.beginPath();
    g.moveTo(cx + rx * fx, cy + ry * (fy + 0.55));
    g.quadraticCurveTo(cx + rx * (fx - 0.30), cy + ry * fy,
                       cx + rx * (fx + 0.42 * fr), cy + ry * (fy - 0.30));
    g.quadraticCurveTo(cx + rx * (fx + 0.52 * fr), cy + ry * (fy + 0.34),
                       cx + rx * fx, cy + ry * (fy + 0.55));
    g.closePath();
    g.fillStyle = light; g.fill();
    g.strokeStyle = ink; g.lineWidth = lw * 0.75; g.stroke();
    g.lineWidth = lw * 0.42;
    g.beginPath();
    g.moveTo(cx + rx * (fx + 0.06), cy + ry * (fy + 0.30));
    g.lineTo(cx + rx * (fx + 0.30 * fr), cy + ry * (fy - 0.08));
    g.stroke();
  }

  // ---- body ----
  blobPath(g, cx, cy, rx, ry);
  g.fillStyle = col; g.fill();
  g.save();
  g.clip();
  g.fillStyle = '#fdfdf7';                      // white belly, lower left
  g.beginPath();
  g.moveTo(cx - rx * 1.1, cy + ry * 1.1);
  g.bezierCurveTo(cx - rx * 1.15, cy - ry * 0.15, cx - rx * 0.35, cy - ry * 0.42,
                  cx + rx * 0.16, cy - ry * 0.05);
  g.bezierCurveTo(cx + rx * 0.60, cy + ry * 0.35, cx + rx * 0.55, cy + ry * 1.1,
                  cx + rx * 0.20, cy + ry * 1.2);
  g.closePath(); g.fill();
  g.fillStyle = 'rgba(255,255,255,.28)';        // soft light along the top
  g.beginPath();
  g.ellipse(cx - rx * 0.10, cy - ry * 0.72, rx * 0.62, ry * 0.26, -0.16, 0, 6.2832);
  g.fill();
  g.restore();
  blobPath(g, cx, cy, rx, ry);
  g.strokeStyle = ink; g.lineWidth = lw; g.stroke();

  // ---- face ----
  const ey = cy - ry * 0.30, ex = rx * 0.26, er = Math.max(1.1, u * 0.035);
  if (blink){
    g.strokeStyle = ink; g.lineWidth = Math.max(1, u * 0.032);
    for (const sgn of [-1, 1]){
      g.beginPath();
      g.arc(cx + sgn * ex - rx * 0.10, ey, er * 1.5, 0.15 * Math.PI, 0.85 * Math.PI);
      g.stroke();
    }
  } else {
    g.fillStyle = ink;
    for (const sgn of [-1, 1]){
      g.beginPath();
      g.ellipse(cx + sgn * ex - rx * 0.10, ey, er, er * 1.25, 0, 0, 6.2832);
      g.fill();
    }
  }
  g.fillStyle = 'rgba(214,150,130,.55)';        // blush
  for (const sgn of [-1, 1]){
    g.beginPath();
    g.ellipse(cx + sgn * rx * 0.62 - rx * 0.10, ey + ry * 0.24,
              rx * 0.17, ry * 0.13, 0, 0, 6.2832);
    g.fill();
  }
  g.fillStyle = ink;                            // nostril
  g.beginPath(); g.arc(cx - rx * 0.62, ey + ry * 0.02, er * 0.5, 0, 6.2832); g.fill();
  g.strokeStyle = ink; g.lineWidth = Math.max(1, u * 0.026);
  g.beginPath();                                // mouth: where the flame goes
  g.arc(cx - rx * 0.52, ey + ry * 0.52, rx * 0.16, 0.12 * Math.PI, 0.88 * Math.PI);
  g.stroke();
}

const dragonCache = new Map();
function tintedPig(mat, blink){
  const key = mat + (blink ? 'b' : '');
  let c = dragonCache.get(key);
  if (c) return c;
  c = mk(64, 72, (g, w, h) => drawDragon(g, w, h, colorOf(mat), blink));
  dragonCache.set(key, c);
  return c;
}

/* The shot: a flame out of the mouth, in the shooter's OWN colour - that is the
   whole point of the game, so the flame must never say anything else. White hot
   at the muzzle tip, the material colour through the body, fading out at the
   tail. */
const rgba = (hex, a) => {
  const n = parseInt(hex.slice(1), 16);
  return 'rgba(' + ((n >> 16) & 255) + ',' + ((n >> 8) & 255) + ',' + (n & 255) + ',' + a + ')';
};
function drawFlame(x, y, ang, r, col, t){
  ctx.save();
  ctx.translate(x, y); ctx.rotate(ang);
  const grd = ctx.createLinearGradient(-r * 2.0, 0, r * 1.2, 0);
  grd.addColorStop(0.00, rgba(col, 0));
  grd.addColorStop(0.30, rgba(col, 0.55));
  grd.addColorStop(0.70, col);
  grd.addColorStop(0.92, shade(col, 45));
  grd.addColorStop(1.00, '#fffdf2');
  ctx.fillStyle = grd;
  const wob = Math.sin(t / 26) * r * 0.16;
  ctx.beginPath();
  ctx.moveTo(r * 1.20, 0);
  ctx.quadraticCurveTo(r * 0.10, -r * 0.78 + wob, -r * 1.95, -r * 0.18);
  ctx.quadraticCurveTo(-r * 0.85, 0, -r * 1.95, r * 0.18);
  ctx.quadraticCurveTo(r * 0.10, r * 0.78 - wob, r * 1.20, 0);
  ctx.closePath();
  ctx.fill();
  ctx.restore();
}


/* ----------------------------- icon set ----------------------------- */
const S = 48;                                  // every icon is drawn at 48px
const ART = {};

ART.lock = mk(S, S, (g, w, h) => {
  glyph(g, w, h, '#ffd166', () => {
    g.beginPath(); g.arc(w / 2, h * 0.38, w * 0.19, Math.PI, 0);
  });
  g.fillStyle = '#ffd166'; rrp(g, w * 0.24, h * 0.40, w * 0.52, h * 0.40, w * 0.10); g.fill();
  g.fillStyle = '#7a5410';
  g.beginPath(); g.arc(w / 2, h * 0.60, w * 0.065, 0, 6.2832); g.fill();
  g.fillRect(w / 2 - w * 0.03, h * 0.60, w * 0.06, h * 0.11);
});
ART.ice = mk(S, S, (g, w, h) => {
  const grd = g.createLinearGradient(0, 0, w, h);
  grd.addColorStop(0, '#dff6ff'); grd.addColorStop(1, '#7cc6ef');
  g.fillStyle = grd;
  starp(g, w / 2, h / 2, w * 0.44, w * 0.17, 6); g.fill();
  g.strokeStyle = 'rgba(255,255,255,.9)'; g.lineWidth = w * 0.045;
  g.beginPath();
  for (let i = 0; i < 3; i++){
    const a = i * Math.PI / 3;
    g.moveTo(w / 2 - Math.cos(a) * w * 0.34, h / 2 - Math.sin(a) * w * 0.34);
    g.lineTo(w / 2 + Math.cos(a) * w * 0.34, h / 2 + Math.sin(a) * w * 0.34);
  }
  g.stroke();
});
ART.iceClock = mk(S, S, (g, w, h) => {
  g.fillStyle = '#bfe9ff';
  g.beginPath(); g.arc(w / 2, h / 2, w * 0.42, 0, 6.2832); g.fill();
  g.strokeStyle = '#2f6f96'; g.lineWidth = w * 0.06;
  g.beginPath(); g.arc(w / 2, h / 2, w * 0.42, 0, 6.2832); g.stroke();
  glyph(g, w, h, '#1d4a66', () => {
    g.beginPath();
    g.moveTo(w / 2, h * 0.28); g.lineTo(w / 2, h / 2); g.lineTo(w * 0.68, h * 0.60);
  });
});
ART.fChain = mk(S, S, (g, w, h) => {
  g.strokeStyle = '#b9c4d6'; g.lineWidth = w * 0.10;
  for (const p of [[0.36, 0.36], [0.64, 0.64]]){
    g.beginPath(); g.ellipse(w * p[0], h * p[1], w * 0.17, h * 0.12, -0.78, 0, 6.2832); g.stroke();
  }
  g.strokeStyle = '#7d879a'; g.lineWidth = w * 0.05;
  g.beginPath(); g.moveTo(w * 0.44, h * 0.44); g.lineTo(w * 0.56, h * 0.56); g.stroke();
});
ART.fTotem = mk(S, S, (g, w, h) => {
  ['#f2a65a', '#e0684b', '#8e5bd0'].forEach((c, i) => {
    g.fillStyle = c;
    rrp(g, w * (0.24 + i * 0.03), h * (0.22 + i * 0.22), w * (0.52 - i * 0.06), h * 0.19, w * 0.06);
    g.fill();
  });
  g.fillStyle = '#3a2450';
  g.beginPath(); g.arc(w * 0.42, h * 0.31, w * 0.035, 0, 6.2832);
  g.arc(w * 0.58, h * 0.31, w * 0.035, 0, 6.2832); g.fill();
});
ART.fPipe = mk(S, S, (g, w, h) => {
  g.strokeStyle = '#8ad3b0'; g.lineWidth = w * 0.20;
  g.beginPath(); g.moveTo(w * 0.14, h * 0.62); g.lineTo(w * 0.86, h * 0.62); g.stroke();
  g.fillStyle = '#4f9c78';
  g.fillRect(w * 0.30, h * 0.44, w * 0.09, h * 0.36);
  g.fillRect(w * 0.61, h * 0.44, w * 0.09, h * 0.36);
  g.fillStyle = '#d9fff0';
  g.beginPath(); g.arc(w * 0.5, h * 0.30, w * 0.11, 0, 6.2832); g.fill();
});
ART.music = mk(S, S, (g, w, h) => {
  g.fillStyle = '#f7a8d8';
  g.beginPath(); g.ellipse(w * 0.38, h * 0.68, w * 0.17, h * 0.13, -0.4, 0, 6.2832); g.fill();
  g.fillRect(w * 0.51, h * 0.20, w * 0.07, h * 0.50);
  g.beginPath();
  g.moveTo(w * 0.58, h * 0.20); g.quadraticCurveTo(w * 0.86, h * 0.26, w * 0.80, h * 0.40);
  g.quadraticCurveTo(w * 0.74, h * 0.30, w * 0.58, h * 0.32);
  g.closePath(); g.fill();
});
ART.hammer = mk(S, S, (g, w, h) => {
  g.save(); g.translate(w / 2, h / 2); g.rotate(-0.5); g.translate(-w / 2, -h / 2);
  g.fillStyle = '#c98b4b';
  rrp(g, w * 0.45, h * 0.34, w * 0.10, h * 0.52, w * 0.04); g.fill();
  const grd = g.createLinearGradient(0, h * 0.16, 0, h * 0.36);
  grd.addColorStop(0, '#e2e8f2'); grd.addColorStop(1, '#98a3b8');
  g.fillStyle = grd;
  rrp(g, w * 0.22, h * 0.16, w * 0.56, h * 0.20, w * 0.06); g.fill();
  g.restore();
});
ART.fAstro = mk(S, S, (g, w, h) => {
  g.fillStyle = '#e9eef7';
  g.beginPath(); g.arc(w / 2, h / 2, w * 0.42, 0, 6.2832); g.fill();
  g.fillStyle = '#2b3c58';
  rrp(g, w * 0.20, h * 0.34, w * 0.60, h * 0.32, h * 0.16); g.fill();
  g.fillStyle = 'rgba(255,255,255,.55)';
  g.beginPath(); g.ellipse(w * 0.36, h * 0.44, w * 0.09, h * 0.05, -0.5, 0, 6.2832); g.fill();
});
ART.question = mk(S, S, (g, w, h) => {
  g.fillStyle = '#7c5cc4';
  rrp(g, w * 0.14, h * 0.14, w * 0.72, h * 0.72, w * 0.20); g.fill();
  g.fillStyle = '#fff';
  g.font = '800 ' + Math.round(h * 0.60) + 'px Segoe UI,system-ui,sans-serif';
  g.textAlign = 'center'; g.textBaseline = 'middle';
  g.fillText('?', w / 2, h * 0.55);
});
ART.fSlotCage = mk(S, S, (g, w, h) => {
  g.strokeStyle = '#cbd3e2'; g.lineWidth = w * 0.07;
  rrp(g, w * 0.16, h * 0.20, w * 0.68, h * 0.60, w * 0.08); g.stroke();
  g.beginPath();
  for (let i = 1; i < 4; i++){
    g.moveTo(w * (0.16 + i * 0.17), h * 0.20);
    g.lineTo(w * (0.16 + i * 0.17), h * 0.80);
  }
  g.lineWidth = w * 0.05; g.stroke();
});
function trayIcon(fill){
  return mk(S, S, (g, w, h) => {
    g.fillStyle = '#5c4a86';
    rrp(g, w * 0.14, h * 0.46, w * 0.72, h * 0.30, w * 0.09); g.fill();
    g.strokeStyle = '#b9a8e8'; g.lineWidth = w * 0.05;
    rrp(g, w * 0.14, h * 0.46, w * 0.72, h * 0.30, w * 0.09); g.stroke();
    if (fill) drawDragon(g, w * 0.62, h * 0.62, fill === 2 ? '#9ad6ff' : '#ffd166', false);
  });
}
ART.tray = trayIcon(0);
ART.trayHalf = trayIcon(2);
ART.trayFull = trayIcon(1);

ART.pwShuffle = mk(S, S, (g, w, h) => {
  glyph(g, w, h, '#7dd3fc', () => {
    g.beginPath();
    g.moveTo(w * 0.18, h * 0.34); g.lineTo(w * 0.66, h * 0.34);
    g.moveTo(w * 0.82, h * 0.66); g.lineTo(w * 0.34, h * 0.66);
  });
  g.fillStyle = '#7dd3fc';
  g.beginPath();
  g.moveTo(w * 0.82, h * 0.34); g.lineTo(w * 0.62, h * 0.22); g.lineTo(w * 0.62, h * 0.46);
  g.closePath(); g.fill();
  g.beginPath();
  g.moveTo(w * 0.18, h * 0.66); g.lineTo(w * 0.38, h * 0.54); g.lineTo(w * 0.38, h * 0.78);
  g.closePath(); g.fill();
});
ART.pwHand = mk(S, S, (g, w, h) => {
  g.fillStyle = '#ffe0b8';
  for (let i = 0; i < 3; i++){
    rrp(g, w * (0.32 + i * 0.13), h * 0.18, w * 0.10, h * 0.26, w * 0.05);
    g.fill();
  }
  rrp(g, w * 0.30, h * 0.34, w * 0.40, h * 0.44, w * 0.14); g.fill();
  g.strokeStyle = '#c99a68'; g.lineWidth = w * 0.035;
  rrp(g, w * 0.30, h * 0.34, w * 0.40, h * 0.44, w * 0.14); g.stroke();
});
ART.pwSuper = mk(S, S, (g, w, h) => {
  const grd = g.createRadialGradient(w / 2, h / 2, 1, w / 2, h / 2, w * 0.45);
  grd.addColorStop(0, '#fff6c8'); grd.addColorStop(1, '#ff9f43');
  g.fillStyle = grd;
  starp(g, w / 2, h / 2, w * 0.46, w * 0.19, 5); g.fill();
  g.fillStyle = '#8a4a00';
  g.beginPath(); g.arc(w / 2, h / 2, w * 0.09, 0, 6.2832); g.fill();
});
ART.pwSlot = mk(S, S, (g, w, h) => {
  g.strokeStyle = '#8ef2b0'; g.lineWidth = w * 0.07;
  rrp(g, w * 0.14, h * 0.30, w * 0.72, h * 0.40, w * 0.10); g.stroke();
  glyph(g, w, h, '#8ef2b0', () => {
    g.beginPath();
    g.moveTo(w * 0.50, h * 0.36); g.lineTo(w * 0.50, h * 0.64);
    g.moveTo(w * 0.36, h * 0.50); g.lineTo(w * 0.64, h * 0.50);
  });
});

ART.heart = mk(S, S, (g, w, h) => {
  const grd = g.createLinearGradient(0, 0, 0, h);
  grd.addColorStop(0, '#ff8fa3'); grd.addColorStop(1, '#e03e5c');
  g.fillStyle = grd;
  g.beginPath();
  g.moveTo(w / 2, h * 0.84);
  g.bezierCurveTo(w * 0.02, h * 0.52, w * 0.16, h * 0.12, w / 2, h * 0.32);
  g.bezierCurveTo(w * 0.84, h * 0.12, w * 0.98, h * 0.52, w / 2, h * 0.84);
  g.closePath(); g.fill();
  g.fillStyle = 'rgba(255,255,255,.5)';
  g.beginPath(); g.ellipse(w * 0.34, h * 0.36, w * 0.10, h * 0.06, -0.5, 0, 6.2832); g.fill();
});
ART.heartEmpty = mk(S, S, (g, w, h) => {
  g.strokeStyle = '#7b6a90'; g.lineWidth = w * 0.07;
  g.beginPath();
  g.moveTo(w / 2, h * 0.82);
  g.bezierCurveTo(w * 0.05, h * 0.52, w * 0.18, h * 0.14, w / 2, h * 0.33);
  g.bezierCurveTo(w * 0.82, h * 0.14, w * 0.95, h * 0.52, w / 2, h * 0.82);
  g.closePath(); g.stroke();
});
ART.coin = mk(S, S, (g, w, h) => {
  const grd = g.createLinearGradient(0, 0, 0, h);
  grd.addColorStop(0, '#ffe9a3'); grd.addColorStop(1, '#e5a51b');
  g.fillStyle = grd;
  g.beginPath(); g.arc(w / 2, h / 2, w * 0.40, 0, 6.2832); g.fill();
  g.strokeStyle = '#a9750c'; g.lineWidth = w * 0.05;
  g.beginPath(); g.arc(w / 2, h / 2, w * 0.40, 0, 6.2832); g.stroke();
  g.fillStyle = '#a9750c';
  g.font = '800 ' + Math.round(h * 0.44) + 'px Segoe UI,system-ui,sans-serif';
  g.textAlign = 'center'; g.textBaseline = 'middle';
  g.fillText('B', w / 2, h * 0.54);
});
ART.star = mk(S, S, (g, w, h) => {
  const grd = g.createLinearGradient(0, 0, 0, h);
  grd.addColorStop(0, '#d8f4ff'); grd.addColorStop(1, '#38bdf8');
  g.fillStyle = grd;
  starp(g, w / 2, h * 0.52, w * 0.42, w * 0.18, 5); g.fill();
});
ART.check = mk(S, S, (g, w, h) => {
  g.fillStyle = '#3fbf7a';
  g.beginPath(); g.arc(w / 2, h / 2, w * 0.40, 0, 6.2832); g.fill();
  glyph(g, w, h, '#0d2a1a', () => {
    g.beginPath();
    g.moveTo(w * 0.30, h * 0.52); g.lineTo(w * 0.45, h * 0.66); g.lineTo(w * 0.72, h * 0.36);
  });
});
ART.avatar = mk(S, S, (g, w, h) => drawDragon(g, w, h, '#7dd3fc', false));

/* Powerups: the same six controllers as the original, icons mine. */
const POWERUPS = [
  { key: 'shuffle', art: 'pwShuffle', label: 'SHUF', desc: '큐 전체를 섞는다' },
  { key: 'hand',    art: 'pwHand',    label: 'HAND', desc: '큐의 아무 하나를 집는다 (맨 앞 규칙 무시)' },
  { key: 'super',   art: 'pwSuper',   label: 'SUPR', desc: '픽셀을 탭하면 특수 슈터가 그 색 덩어리를 관통 사격' },
  { key: 'slot',    art: 'pwSlot',    label: '+SLT', desc: '캐리지를 1개 추가한다' },
  { key: 'demolish',art: 'hammer',    label: 'DEMO', desc: '픽셀을 탭해 주변 반경 2칸을 파괴' },
  { key: 'tray',    art: 'tray',      label: 'TRAY', desc: '맨 앞 하나를 트레이로 빼두고, 다시 눌러 되돌린다' }
];
const url = k => ART[k].toDataURL();

"""

META = r"""/* ============================== home ==============================
   Lobby, level card, shop and sprite sheet. No image files: the hexagons are
   clip-path, the plates are gradients, the icons are the canvases above turned
   into data URLs.

   The level DATA on the card is real - `Difficulty` and the feature arrays come
   out of the level JSONs via reverse/tools/make_manifest.py. The economy does
   not exist in the original (server side), so hearts, gold and prices here are
   mine and deliberately simple: a fail costs a heart, a clear pays gold by
   difficulty, gold buys powerups. */
const NODE_H = 112, LV_MAX = 2300;
const DIFFS = {
  'Easy':      { ko: '쉬움',       pips: 1, c1: '#5cb8ff', c2: '#1e5fd0' },
  'Medium':    { ko: '보통',       pips: 2, c1: '#ffc85c', c2: '#d07a1e' },
  'Hard':      { ko: '어려움',     pips: 3, c1: '#ff8a9c', c2: '#c2255c' },
  'Very Hard': { ko: '매우 어려움', pips: 4, c1: '#c89cff', c2: '#6d28d9' }
};
const dif = d => DIFFS[d] || DIFFS.Easy;
const FEAT_ART = {
  surprise: 'question', connected: 'fChain', lock: 'lock', pipe: 'fPipe',
  hammer: 'hammer', ice: 'ice', chain: 'fChain', totem: 'fTotem',
  music: 'music', slotcage: 'fSlotCage', astro: 'fAstro', door: 'fSlotCage'
};
const FEAT_KO = {
  surprise: '서프라이즈', connected: '연결', lock: '자물쇠', pipe: '파이프',
  hammer: '해머', ice: '얼음', chain: '족쇄', totem: '토템', music: '말렛',
  slotcage: '슬롯케이지', astro: '우주복', door: '컨베이어 문'
};
const SHOP = [
  { k: 'hearts',   name: '하트 가득',   cost: 150, art: 'heart',     desc: '하트를 5개로 채운다' },
  { k: 'shuffle',  name: '셔플',       cost: 60,  art: 'pwShuffle', desc: '큐 전체를 섞는다' },
  { k: 'tray',     name: '트레이',     cost: 80,  art: 'tray',      desc: '맨 앞 하나를 빼 둔다' },
  { k: 'hand',     name: '집게',       cost: 90,  art: 'pwHand',    desc: '큐 아무 자리나 하나 집는다' },
  { k: 'demolish', name: '해머',       cost: 120, art: 'hammer',    desc: '반경 2칸을 부순다' },
  { k: 'super',    name: '슈퍼 슈터',   cost: 180, art: 'pwSuper',   desc: '그 색 덩어리를 관통 사격' },
  { k: 'slot',     name: '캐리지 +1',  cost: 200, art: 'pwSlot',    desc: '캐리지를 하나 늘린다' },
  { k: 'gold',     name: '골드 +500',  cost: 0,   art: 'coin',      desc: '데모용 무료 지급. 결제 없음' }
];

let MAN = null, inHome = true;
const PW0 = { shuffle: 1, hand: 1, super: 1, slot: 1, demolish: 1, tray: 1 };
/* Heart refill. The APK does not ship this: a full scan of data.unity3d by
   script class finds only `ResourceCaptureSystemEvents` ("Heart Resource
   Capture System Events") and `BonusLevelResourceEarnEvents`, neither of which
   carries a timing value, and `HeartNotificationStateProviderSo`'s
   `heartGeneratorSettings` (+0x28) has no instance in the bundle - the heart
   generator is server/remote config [X]. So these numbers are MINE: one heart
   every 30 minutes up to 5, which is the genre default. */
const HEART_MAX = 5, HEART_REFILL_MS = 30 * 60 * 1000;
const META = Object.assign(
  { cleared: [], hearts: 5, gold: 300, current: 1, heartAt: 0, pw: Object.assign({}, PW0) },
  JSON.parse(localStorage.getItem('bb_meta') || '{}'));
META.pw = Object.assign({}, PW0, META.pw);
let cleared = new Set(META.cleared);
const saveMeta = () => {
  META.cleared = Array.from(cleared);
  localStorage.setItem('bb_meta', JSON.stringify(META));
};
const sheet = (id, on) => $(id).classList[on ? 'add' : 'remove']('on');

/* Roll the refill clock forward. `heartAt` is when the NEXT heart lands; each
   whole interval that has passed since then grants one more. */
function refillHearts(){
  if (META.hearts >= HEART_MAX){ META.heartAt = 0; return; }
  if (!META.heartAt){ META.heartAt = Date.now() + HEART_REFILL_MS; saveMeta(); return; }
  let changed = false;
  while (META.hearts < HEART_MAX && Date.now() >= META.heartAt){
    META.hearts++;
    META.heartAt += HEART_REFILL_MS;
    changed = true;
  }
  if (META.hearts >= HEART_MAX) META.heartAt = 0;
  if (changed) saveMeta();
}
const heartLeftMs = () => (META.hearts >= HEART_MAX || !META.heartAt)
  ? 0 : Math.max(0, META.heartAt - Date.now());
function spendHeart(){
  META.hearts = Math.max(0, META.hearts - 1);
  if (!META.heartAt) META.heartAt = Date.now() + HEART_REFILL_MS;   // clock starts on the first loss
  saveMeta();
}

function syncMeta(){
  refillHearts();
  const left = heartLeftMs();
  $('cHeart').textContent = META.hearts + (left
    ? ' (' + Math.floor(left / 60000) + ':' + String(Math.floor(left / 1000) % 60).padStart(2, '0') + ')'
    : '');
  $('cGold').textContent  = META.gold;
  $('cStar').textContent  = cleared.size;
  $('icHeart').src = url(META.hearts ? 'heart' : 'heartEmpty');
}

const nodeTop = n => (LV_MAX - n) * NODE_H;

function nodeHtml(r){
  const d = dif(r.d), done = cleared.has(r.n), cur = r.n === META.current;
  return '<div class="nd' + (done ? ' cl' : '') + (cur ? ' cur' : '')
    + '" data-n="' + r.n + '" style="top:' + (nodeTop(r.n) + 14)
    + 'px;--c1:' + d.c1 + ';--c2:' + d.c2 + '">'
    + '<div class="hex"></div>'
    + '<div class="hexIn"><span class="num">' + r.n + '</span></div>'
    + '<div class="pips">' + '<i></i>'.repeat(d.pips) + '</div>'
    + (done ? '<img class="done" src="' + url('check') + '">' : '')
    + '</div>';
}

// only the visible slice of the 2300 nodes exists
let win = [0, 0];
function renderTree(force){
  const sc = $('scroll'), tree = $('tree');
  const h = sc.clientHeight || 400, top = sc.scrollTop;
  const from = Math.max(1, LV_MAX - Math.ceil((top + h) / NODE_H) - 1);
  const to   = Math.min(LV_MAX, LV_MAX - Math.floor(top / NODE_H) + 1);
  if (!force && from === win[0] && to === win[1]) return;
  win = [from, to];
  let html = '';
  for (let n = from; n <= to; n++) html += nodeHtml(MAN[n - 1]);
  tree.querySelectorAll('.nd').forEach(e => e.remove());
  tree.insertAdjacentHTML('beforeend', html);
}

function buildTreeChrome(){
  const tree = $('tree');
  tree.style.height = (LV_MAX * NODE_H + 40) + 'px';
  const bands = [['#1b2a4d', '#141d3a'], ['#2a1b3f', '#1d1430'], ['#16302c', '#111f22']];
  let html = '';
  for (let b = 0; b * 100 < LV_MAX; b++){
    const lo = b * 100 + 1, hi = Math.min(LV_MAX, lo + 99), c = bands[b % 3];
    html += '<div class="band" style="top:' + nodeTop(hi) + 'px;height:'
      + ((hi - lo + 1) * NODE_H) + 'px;background:linear-gradient('
      + c[0] + ',' + c[1] + ')"></div>';
  }
  html += '<div class="spine" style="top:20px;height:' + (LV_MAX * NODE_H) + 'px"></div>';
  tree.innerHTML = html;
}

function openCard(n){
  const r = MAN[n - 1], d = dif(r.d);
  $('cdArt').src = url('avatar');
  $('cdNo').textContent = '레벨 ' + n;
  $('cdDiff').textContent = d.ko;
  $('cdDiff').style.setProperty('--c1', d.c1);
  $('cdDiff').style.setProperty('--c2', d.c2);
  $('cdStats').textContent = '픽셀 ' + r.px + ' · 캐리지 ' + r.slots
    + ' · 벨트 한도 ' + r.lim + (cleared.has(n) ? ' · 클리어' : '');
  const tags = Object.keys(r.f);
  $('cdFeats').innerHTML = tags.length
    ? tags.map(k => '<span class="fchip"><img src="' + url(FEAT_ART[k] || 'question')
        + '">' + (FEAT_KO[k] || k) + ' ' + r.f[k] + '</span>').join('')
    : '<span style="font-size:11px;color:var(--dim)">피처 없음</span>';
  const noHeart = META.hearts <= 0;
  $('cdPlay').disabled = noHeart;
  $('cdPlay').textContent = noHeart ? '하트 없음' : 'PLAY';
  $('cdPlay').onclick = () => { sheet('cardSheet', false); startLevel(n); };
  sheet('cardSheet', true);
}

function buildShop(){
  $('shopList').innerHTML = SHOP.map(it => {
    const own = it.k === 'hearts' ? META.hearts + ' / 5'
      : it.k === 'gold' ? '' : '보유 ' + (META.pw[it.k] || 0);
    const can = META.gold >= it.cost && !(it.k === 'hearts' && META.hearts >= 5);
    return '<div class="shopRow"><img src="' + url(it.art) + '">'
      + '<div><div class="nm">' + it.name + '</div>'
      + '<div class="ds">' + it.desc + '</div>'
      + (own ? '<div class="own">' + own + '</div>' : '') + '</div>'
      + '<button class="buy" data-k="' + it.k + '"' + (can ? '' : ' disabled') + '>'
      + (it.cost ? '<img src="' + url('coin') + '">' + it.cost : '무료') + '</button></div>';
  }).join('');
  $('shopList').querySelectorAll('.buy').forEach(b => { b.onclick = () => buy(b.dataset.k); });
}

function buy(k){
  const it = SHOP.find(x => x.k === k);
  if (!it || META.gold < it.cost) return;
  META.gold -= it.cost;
  if (k === 'gold') META.gold += 500;
  else if (k === 'hearts'){ META.hearts = HEART_MAX; META.heartAt = 0; }
  else META.pw[k] = (META.pw[k] || 0) + 1;
  saveMeta(); syncMeta(); buildShop();
}

function showHome(){
  inHome = true;
  document.body.classList.add('meta');
  syncMeta();
  const sc = $('scroll');
  sc.scrollTop = Math.max(0, nodeTop(META.current) - sc.clientHeight / 2);
  renderTree(true);
}

function startLevel(n){
  inHome = false;
  document.body.classList.remove('meta');
  load(n);
}

// powerup spending has to reach the saved inventory, through both entry points
const _usePowerup = usePowerup, _useTray = useTray;
usePowerup = function(k){
  const b = G.pw[k]; _usePowerup(k);
  if (G.pw[k] < b){ META.pw[k] = G.pw[k]; saveMeta(); }
};
useTray = function(qi){
  const b = G.pw.tray; _useTray(qi);
  if (G.pw.tray < b){ META.pw.tray = G.pw.tray; saveMeta(); }
};

/* ---------------------------- belt speed ----------------------------
   The measured belt is 5.0 world units/sec with the multiplier at 1.0 (9.1),
   but at this on-screen scale it reads like the original's endgame from the
   first second, so this build halves the base. The AutoFinisher's x2.0 then
   lands back on the measured 5.0 for the last stretch - same shape as the
   original, one notch slower throughout. Everything else about the
   AutoFinisher (the latch, the wall detach, the path-end change) lives in the
   shared core. */
BELT_TUNE = 0.5;                             // mine, a tuning knob

/* A spent shooter flies OUTWARD off the belt (mine). The original simply
   removes it; drawing it drifting away from the picture keeps the last shot
   from reading as the animal being pulled into the board. */
const LEAVE_MS = 430;
function leaveOutward(pig, x, y){
  const cx = L.gx + L.gw / 2, cy = L.gy + L.gh / 2;
  let dx = x - cx, dy = y - cy;
  const d = Math.hypot(dx, dy) || 1;
  (G.leaving || (G.leaving = [])).push({
    pig: pig, x: x, y: y, vx: dx / d * 210, vy: dy / d * 210,
    spin: dx < 0 ? -1 : 1, t0: nowMs()
  });
}

async function boot(){
  $('avatar').innerHTML = '<img src="' + url('avatar') + '">';
  $('icGold').src = url('coin');
  $('icStar').src = url('star');
  MAN = await (await fetch('levels/manifest.json')).json();
  buildTreeChrome(); buildShop();
  $('scroll').addEventListener('scroll', () => renderTree(false));
  $('tree').addEventListener('click', e => {
    const nd = e.target.closest('.nd');
    if (nd) openCard(+nd.dataset.n);
  });
  $('cdClose').onclick = () => sheet('cardSheet', false);
  $('nvShop').onclick  = () => { buildShop(); sheet('shopSheet', true); };
  $('shClose').onclick = () => sheet('shopSheet', false);
  $('reset').onclick = () => {
    if (!confirm('진행도(클리어·하트·골드·파워업)를 지운다')) return;
    cleared = new Set();
    Object.assign(META, { hearts: HEART_MAX, gold: 300, current: 1, heartAt: 0,
                          pw: Object.assign({}, PW0) });
    saveMeta(); buildShop(); showHome();
  };
  // walking out of a level in progress costs a heart, same as failing it
  $('toHome').onclick = () => {
    if (G && G.state === 'play'){
      if (!confirm('레벨을 나가면 하트 1개가 사라진다. 나갈까?')) return;
      spendHeart();
    }
    showHome();
  };
  $('ovHome').onclick = () => { $('overlay').classList.remove('on'); showHome(); };
  addEventListener('resize', () => { if (inHome) renderTree(true); });
  setInterval(() => { if (inHome){ refillHearts(); syncMeta(); } }, 1000);
  showHome();
}

"""

TAIL = r"""$('prev').onclick  = () => load((+$('lvl').value) - 1);
$('next').onclick  = () => load((+$('lvl').value) + 1);
$('retry').onclick = () => load(+$('lvl').value);
$('lvl').onchange  = () => load(+$('lvl').value);
$('mode').onclick  = () => {
  COLUMN_SCAN = !COLUMN_SCAN;
  $('mode').textContent = COLUMN_SCAN ? '가림' : '전체';
  load(+$('lvl').value);
};
addEventListener('resize', () => layout());

boot();
requestAnimationFrame(frame);
</script>
</body>
</html>
"""

# the core already scales the belt by beltMult() and owns the 6.8 latch

# an emptied shooter flies out instead of blinking away, and rearms the 6.8 check
CORE = CORE.replace("""    if (pig.ammo <= 0){
      slot.pig = null; slot.travel = 0; G.depleted++;
      slot.returnUntil = now + RETURN_MS;
      tryActivateAutoFinisher();      // rechecked on every disappearance
    }""",
"""    if (pig.ammo <= 0){
      const at = pathPoint(L.path, slot.s);
      slot.pig = null; slot.travel = 0; G.depleted++;
      slot.returnUntil = now + RETURN_MS;
      leaveOutward(pig, at[0], at[1]);    // mine: fly out, not in
      tryActivateAutoFinisher();          // rechecked on every disappearance
    }""")
assert 'leaveOutward(pig, at[0], at[1]);' in CORE

# the path end (and its cks gate) is core now

# draw the fly-off
CORE = CORE.replace("""  // ---- slot-entrance queue ----""",
"""  // ---- spent shooters flying off the belt ----
  if (G.leaving) for (let i = G.leaving.length - 1; i >= 0; i--){
    const e = G.leaving[i], k = (now - e.t0) / LEAVE_MS;
    if (k >= 1 || k < 0){ G.leaving.splice(i, 1); continue; }
    ctx.save();
    ctx.globalAlpha = 1 - k * k;
    ctx.translate(e.x + e.vx * k, e.y + e.vy * k);
    ctx.rotate(e.spin * k * 1.1);
    const sc = 1 - k * 0.3;
    ctx.scale(sc, sc);
    drawPig(-13, -10, 26, 20, e.pig, {});
    ctx.restore();
  }

  // ---- slot-entrance queue ----""")
assert 'spent shooters flying off the belt' in CORE

CORE = CORE.replace("function frame(now){\n  requestAnimationFrame(frame);\n  if (!G || inLobby) return;",
                    "function frame(now){\n  requestAnimationFrame(frame);\n  if (!G || inHome) return;")
assert 'if (!G || inHome) return;' in CORE
CORE = CORE.replace("""  if (kind === 'win'){
    cleared.add(G.n);
    META.current = Math.max(META.current, Math.min(LV_MAX, G.n + 1));
    META.gold += 50;
  } else {
    META.hearts = Math.max(0, META.hearts - 1);
  }
  saveMeta();""",
"""  if (kind === 'win'){
    cleared.add(G.n);
    META.current = Math.max(META.current, Math.min(LV_MAX, G.n + 1));
    META.gold += 40 + 10 * dif(G.raw.Difficulty).pips;   // harder pays more
  } else {
    spendHeart();
  }
  saveMeta();""")
assert 'harder pays more' in CORE

out = ('<!doctype html>\n<html lang="ko">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width,initial-scale=1,'
       'maximum-scale=1,user-scalable=no">\n<title>Flame Dragons</title>\n'
       + STYLE + '\n</head>\n' + MARKUP + '\n'
       + HEADER + PALETTE + CONSTS + ART + CORE + META + TAIL)


# ------------------------------------------------------------- the level set
# The ten pictures live INSIDE the page: pack/levels.js declares PACK (gzipped
# JSON per level, the same "gzip:" form fetchLevel already reads) and PACK_MAN
# (what the lobby needs per node). Inlining them drops both fetches, so the file
# plays straight off disk and hosts anywhere static.
PACK_JS = io.open(os.path.join(DST, 'pack', 'levels.js'), encoding='utf-8').read()
out = out.replace('<script>', '<script>' + chr(10) + PACK_JS, 1)

for _a, _b in (
    ("  const txt = (await (await fetch('levels/' + n + '.json')).text()).trim();",
     "  const txt = PACK[n - 1].trim();"),
    ("  MAN = await (await fetch('levels/manifest.json')).json();",
     "  MAN = PACK_MAN;"),
    ("async function fetchLevel(n){",
     "async function fetchLevel(n){          // the inlined PACK, not the network"),
    # the level count is the pack's, not the reference set's
    ('<input id="lvl" type="number" min="1" max="2300" value="1">',
     '<input id="lvl" type="number" min="1" max="10" value="1">'),
    ("  n = Math.max(1, Math.min(2300, n | 0));",
     "  n = Math.max(1, Math.min(PACK.length, n | 0));"),
    ("const NODE_H = 112, LV_MAX = 2300;",
     "const NODE_H = 112, LV_MAX = PACK_MAN.length;"),
    # ten nodes fit on one screen, so name the picture on each one
    ("""    + '<div class="pips">' + '<i></i>'.repeat(d.pips) + '</div>'""",
     """    + '<div class="pips">' + '<i></i>'.repeat(d.pips) + '</div>'
    + '<div class="ndName">' + (r.name || '') + '</div>'"""),
    ("// only the visible slice of the 2300 nodes exists",
     "// only the visible slice of the map exists"),
):
    assert _a in out, _a[:60]
    out = out.replace(_a, _b, 1)


# ---------------------------------------------------------------- rename pass
# This build carries none of the reference's naming: `pig` was its word for a
# shooter, here they are dragons. The sprite painter is renamed first so the
# mechanical word pass cannot collide with it.
W = chr(92) + 'b'          # word boundary, built to survive this generator
out = re.sub('drawDragon', 'drawDragonSprite', out)
for a, b in (('pigBlink', 'dragonBlink'), ('pigHappy', 'dragonHappy'),
             ('pigDead', 'dragonDead'), ('tintedPig', 'tintedDragon'),
             ('drawPig', 'drawDragon'), ('bloop', 'dragon')):
    out = out.replace(a, b)
out = re.sub(W + 'pigs' + W, 'dragons', out)
out = re.sub(W + 'pig' + W, 'dragon', out)
out = re.sub(W + 'Pig' + W, 'Dragon', out)
out = out.replace('돼지', '드래곤')
# 드래곤 ends in a consonant, so the particles have to change with it
for a2, b2 in (('드래곤가', '드래곤이'), ('드래곤를', '드래곤을'),
               ('드래곤는', '드래곤은'), ('드래곤와', '드래곤과'),
               ('드래곤로', '드래곤으로')):
    out = out.replace(a2, b2)
# no product names from the reference anywhere in the shipped file
out = out.replace('Pixel Flow 0.33.0', 'the reference build')
out = out.replace('Pixel Flow', 'the reference build')
out = out.replace('../pixelflow-clone/UNITY_SPEC.md', 'UNITY_SPEC.md')
out = out.replace('pixelflow-clone', 'reference build')
out = out.replace('pixelflow-mine', 'this build')
out = out.replace('PixelFlow', 'ReferenceBuild')
for bad in ('Pixel Flow', 'pixelflow', 'PixelFlow', '돼지'):
    assert bad not in out, 'rename pass missed: ' + bad
for pat in (W + 'pig' + W, W + 'Pig' + W, W + 'pigs' + W):
    assert not re.search(pat, out), 'left behind: ' + pat

os.makedirs(DST, exist_ok=True)
io.open(os.path.join(DST, 'index.html'), 'w', encoding='utf-8', newline='').write(out)

print('wrote %s  %d bytes  %d lines' % (os.path.join(DST, 'index.html'),
                                        len(out), out.count('\n') + 1))
print('leftover image refs:', sorted(set(re.findall(r'[\w/]*\.png|\bart/', out))) or 'none')
print('levels inlined:', PACK_JS.count('gzip:'))
