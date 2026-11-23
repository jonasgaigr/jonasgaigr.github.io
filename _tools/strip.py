"""The strip under the hero: scrubland, then meadow, then the littoral of a pond,
then the pond, left to right, on one ground line. Same hand as the round 2
drawings (2-descent/_draw/draw.py, round2/base/_tools/draw2.py).

Writes three versions into img/home/, the same landscape at three widths so the
plants are never stretched; styles.css picks one by screen width:
  d-strip-wide.svg    2400 x 230   (aspect ~10.4, wide screens)
  d-strip-mid.svg     1500 x 220   (aspect ~6.8, tablets)
  d-strip-narrow.svg   900 x 220   (aspect ~4.1, phones)
Seeded and reproducible; illustration only.
Run:  python _tools/strip.py
"""
import math
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "img", "home")

INK = "#1d2b27"
STRAW = ["#b9a166", "#a88f52", "#c8b47c", "#9c8650"]
GREEN = ["#6f9a56", "#86a85f", "#5d8a4e", "#7c9b63"]
SHRUB = ["#4f6b45", "#5d7a4e", "#6b8757", "#587449", "#7a9461"]
BURNET = ["#7a1f2b", "#8d2a33", "#6c1a26"]
TYPHA = ["#a9a76a", "#9aa062", "#b3a66c"]
WATER = "#3f7f96"


def f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def fi(v):
    """whole units: enough for the leaf masses, and a third of the bytes"""
    return str(round(v))


def smooth(pts, move=True, fmt=f):
    d = [f"M{fmt(pts[0][0])},{fmt(pts[0][1])}"] if move else []
    n = len(pts)
    for i in range(n - 1):
        p0, p1, p2, p3 = pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, n - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d.append(f"C{fmt(c1[0])},{fmt(c1[1])} {fmt(c2[0])},{fmt(c2[1])} {fmt(p2[0])},{fmt(p2[1])}")
    return "".join(d)


def blade(R, x0, y0, h, lean, w):
    """a grass blade: two quadratic curves from the base to a curved-over tip"""
    a = lean + R.gauss(0, 0.06)
    bend = lean * 0.6 + R.gauss(0, 0.05)
    tx, ty = x0 + math.sin(a + bend) * h, y0 - math.cos(a + bend) * h * 0.98
    cx, cy = x0 + math.sin(a) * h * 0.55, y0 - math.cos(a) * h * 0.55
    hw = w / 2
    return (f"M{f(x0 - hw)},{f(y0)}Q{f(cx - hw * 0.5)},{f(cy)} {f(tx)},{f(ty)}"
            f"Q{f(cx + hw * 0.5)},{f(cy)} {f(x0 + hw)},{f(y0)}Z")


def blob(R, cx, cy, rx, ry, n=7, jit=0.2):
    """a leaf mass: a closed quadratic spline through the midpoints of a jittered ring"""
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        k = 1 + R.uniform(-jit, jit)
        pts.append((cx + math.cos(t) * rx * k, cy + math.sin(t) * ry * k))
    mids = [((pts[i][0] + pts[(i + 1) % n][0]) / 2, (pts[i][1] + pts[(i + 1) % n][1]) / 2) for i in range(n)]
    d = [f"M{fi(mids[-1][0])},{fi(mids[-1][1])}"]
    for i in range(n):
        d.append(f"Q{fi(pts[i][0])},{fi(pts[i][1])} {fi(mids[i][0])},{fi(mids[i][1])}")
    return "".join(d) + "Z"


def ss(a, b, u):
    """smoothstep from a to b"""
    t = min(1, max(0, (u - a) / (b - a)))
    return t * t * (3 - 2 * t)


# how much of each habitat there is at u = x / width
def w_scrub(u):
    return 1 - ss(0.17, 0.3, u)


def w_meadow(u):
    return ss(0.15, 0.27, u) * (1 - ss(0.5, 0.62, u))


def w_litt(u):
    return ss(0.48, 0.6, u) * (1 - ss(0.8, 0.86, u))


def w_pond(u):
    return ss(0.79, 0.85, u)


def draw(WW, HH, seed, name):
    R = random.Random(seed)
    base = HH - 5
    k = HH / 300          # plant scale, against the 300-high burnet strip of round 2
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WW} {HH}" fill="none" stroke-linecap="round" stroke-linejoin="round">']
    o.append(f'<defs><linearGradient id="wf" x1="0" y1="0" x2="1" y2="0">'
             f'<stop offset="0" stop-color="{WATER}" stop-opacity="0"/><stop offset=".12" stop-color="{WATER}" stop-opacity=".55"/>'
             f'<stop offset="1" stop-color="{WATER}" stop-opacity=".62"/></linearGradient></defs>')

    def pick(n, wf, x0=-10, x1=None):
        x1 = WW + 10 if x1 is None else x1
        out = []
        for _ in range(n):
            x = R.uniform(x0, x1)
            if R.random() < wf(max(0, min(1, x / WW))):
                out.append(x)
        return out

    # ---- the pond: open water at the right, a band on the ground line
    px0 = 0.8 * WW
    wh = 24 * k + 6
    o.append(f'<rect x="{f(px0)}" y="{f(base - wh)}" width="{f(WW - px0 + 2)}" height="{f(wh)}" fill="url(#wf)"/>')
    o.append(f'<path d="M{f(px0 + 0.06 * WW)},{f(base - wh)}H{WW}" stroke="#f6fbf6" stroke-width="1.6"/>')
    o.append(f'<g stroke="{INK}" stroke-opacity=".35" stroke-width="1">')
    for x in pick(int(WW / 34), w_pond):
        y = base - wh + R.uniform(3, wh - 2)
        o.append(f'<path d="M{f(x)},{f(y)}h{f(R.uniform(8, 26) * k + 4)}"/>')
    o.append("</g>")

    # ---- back grass, pale: scrub edge and meadow
    o.append('<g fill-opacity=".36">')
    for x in pick(int(WW / 7), lambda u: 0.45 * w_scrub(u) + w_meadow(u) + 0.35 * w_litt(u)):
        h = R.uniform(40, 120) * k
        o.append(f'<path d="{blade(R, x, base, h, R.uniform(-0.35, 0.35), R.uniform(2, 4) * k + .6)}" fill="{R.choice(STRAW)}"/>')
    o.append("</g>")

    # ---- shrubs: a few stems, a rounded crown of leaf masses, twigs
    shrubs = []
    x = R.uniform(-30, 10)
    while x < 0.34 * WW:
        u = max(0, x / WW)
        if R.random() < w_scrub(u) + 0.05:
            shrubs.append(x)
        x += HH * R.uniform(0.38, 0.62)
    for sx in shrubs:
        u = max(0, sx / WW)
        h = HH * R.uniform(0.72, 0.97) * (0.6 + 0.4 * w_scrub(u))
        wd = h * R.uniform(0.7, 1.1)
        # stems
        for _ in range(R.randint(2, 4)):
            bx = sx + R.uniform(-wd * .08, wd * .08)
            ex = sx + R.uniform(-wd * .3, wd * .3)
            ey = base - h * R.uniform(0.45, 0.7)
            o.append(f'<path d="M{f(bx)},{f(base)}Q{f((bx + ex) / 2 + R.uniform(-6, 6))},{f(base - h * .3)} {f(ex)},{f(ey)}" stroke="#5e5444" stroke-width="{f(R.uniform(1.6, 2.6) * k + .6)}"/>')
        # crown
        cy = base - h * 0.62
        masses = []
        for _ in range(int(30 + wd / (3.4 * k + 1))):
            a = R.uniform(0, 2 * math.pi)
            r = R.random() ** 0.6
            mx = sx + math.cos(a) * wd * 0.48 * r
            my = cy + math.sin(a) * h * 0.42 * r
            my = min(my, base - h * 0.18)
            masses.append((my, mx))
        masses.sort()
        o.append('<g fill-opacity=".86">')
        for my, mx in masses:
            rr = R.uniform(6.5, 13) * k + 2
            col = R.choice(SHRUB)
            o.append(f'<path d="{blob(R, mx, my, rr, rr * R.uniform(.7, .95))}" fill="{col}"/>')
        o.append("</g>")
        # light twigs on top of the crown
        o.append(f'<g stroke="#3f4a36" stroke-width="{f(0.9 * k + .3)}" stroke-opacity=".7">')
        for _ in range(R.randint(4, 8)):
            a = R.uniform(math.pi * 1.05, math.pi * 1.95)
            r0 = R.uniform(0.25, 0.4)
            x1_ = sx + math.cos(a) * wd * 0.5 * r0
            y1_ = cy + math.sin(a) * h * 0.38 * r0
            x2_ = sx + math.cos(a) * wd * 0.55
            y2_ = cy + math.sin(a) * h * 0.48
            o.append(f'<path d="M{f(x1_)},{f(y1_)}L{f(x2_)},{f(y2_)}"/>')
        o.append("</g>")
        # a few dark berries
        if R.random() < 0.6:
            o.append('<g fill="#3b2433">')
            for _ in range(R.randint(3, 8)):
                a = R.uniform(0, 2 * math.pi)
                r = R.uniform(0.2, 0.9)
                o.append(f'<circle cx="{f(sx + math.cos(a) * wd * .45 * r)}" cy="{f(cy + math.sin(a) * h * .3 * r)}" r="{f(1.6 * k + .5)}"/>')
            o.append("</g>")

    # ---- great burnet in the meadow
    for x in pick(int(WW / 34), w_meadow, 0.12 * WW, 0.66 * WW):
        h = R.uniform(150, 270) * k
        lean = R.uniform(-0.12, 0.12)
        pts = []
        a = lean
        px, py = x, base
        n = 8
        for _ in range(n + 1):
            pts.append((px, py))
            a += R.gauss(0, 0.03)
            px += math.sin(a) * h / n
            py -= math.cos(a) * h / n
        o.append(f'<path d="{smooth(pts)}" stroke="{INK}" stroke-opacity=".75" stroke-width="{f(1.3 * k + .3)}"/>')
        heads = [pts[-1]]
        for _b in range(R.choice([0, 1, 1, 2])):
            i = R.randint(4, 6)
            bx, by = pts[i]
            sgn = R.choice([-1, 1])
            L = R.uniform(25, 55) * k
            ex, ey = bx + sgn * L * 0.55, by - L
            o.append(f'<path d="M{f(bx)},{f(by)}Q{f(bx + sgn * L * 0.1)},{f(by - L * 0.6)} {f(ex)},{f(ey)}" stroke="{INK}" stroke-opacity=".7" stroke-width="{f(1.1 * k + .3)}"/>')
            heads.append((ex, ey))
        for hx, hy in heads:
            rx, ry = R.uniform(3.6, 5) * k + .6, R.uniform(7, 10.5) * k + 1
            o.append(f'<ellipse cx="{f(hx)}" cy="{f(hy - ry + 1)}" rx="{f(rx)}" ry="{f(ry)}" fill="{R.choice(BURNET)}"/>')

    # ---- reeds (Phragmites) in the littoral: straw stems, leaves, plumes
    reeds, plumes, leaves = [], [], []
    for x in pick(int(WW / 13), w_litt, 0.44 * WW, 0.9 * WW):
        u = x / WW
        h = R.uniform(150, 275) * k * (0.55 + 0.45 * w_litt(u))
        lean = R.gauss(0.05, 0.06)
        tip = (x + math.sin(lean) * h, base - h)
        ctrl = (x + math.sin(lean) * h * 0.25, base - h / 2)
        col = R.choice(STRAW)
        reeds.append(f'<path d="M{f(x)},{f(base)}Q{f(ctrl[0])},{f(ctrl[1])} {f(tip[0])},{f(tip[1])}" stroke="{col}" stroke-width="{f(R.uniform(1.5, 2.3) * k + .5)}"/>')
        if R.random() < 0.6 and h > 150 * k:
            d = 1 if R.random() < 0.82 else -1
            for _ in range(R.randint(5, 8)):
                s0 = (tip[0] - math.sin(lean) * R.uniform(0, 14) * k, tip[1] + R.uniform(0, 14) * k)
                ex = s0[0] + d * R.uniform(7, 22) * k
                ey = s0[1] - R.uniform(4, 20) * k
                plumes.append(f'<path d="M{f(s0[0])},{f(s0[1])}Q{f(s0[0] + d * 3 * k)},{f(s0[1] - 18 * k)} {f(ex)},{f(ey)}"/>')
        if R.random() < 0.55:
            t = R.uniform(0.35, 0.75)
            p = ((1 - t) ** 2 * x + 2 * (1 - t) * t * ctrl[0] + t * t * tip[0],
                 (1 - t) ** 2 * base + 2 * (1 - t) * t * ctrl[1] + t * t * tip[1])
            d = R.choice([-1, 1])
            L = R.uniform(26, 58) * k
            tl = (p[0] + d * L * 0.85, p[1] - L * R.uniform(-0.2, 0.4))
            mid = ((p[0] + tl[0]) / 2, min(p[1], tl[1]) - L * 0.3)
            leaves.append(f'<path d="M{f(p[0])},{f(p[1])}Q{f(mid[0])},{f(mid[1] - 2 * k)} {f(tl[0])},{f(tl[1])}Q{f(mid[0])},{f(mid[1] + 2.2 * k)} {f(p[0])},{f(p[1] + 1.8 * k)}Z" fill="{R.choice(STRAW)}"/>')
    o.append("<g>" + "".join(leaves) + "</g>")
    o.append("<g>" + "".join(reeds) + "</g>")
    o.append(f'<g stroke="#8d775f" stroke-width="{f(1.1 * k + .3)}">' + "".join(plumes) + "</g>")

    # ---- reedmace (Typha) towards the open water: strap leaves, dark heads
    for x in pick(int(WW / 70), lambda u: w_litt(u) * ss(0.6, 0.72, u), 0.58 * WW, 0.88 * WW):
        for _ in range(3):
            h = R.uniform(140, 205) * k
            lean = R.uniform(-0.2, 0.2)
            tip = (x + math.sin(lean) * h, base - h)
            c1 = (x + math.sin(lean) * h * 0.2 - 3 * k, base - h * 0.5)
            c2 = (x + math.sin(lean) * h * 0.2 + 3 * k, base - h * 0.5)
            o.append(f'<path d="M{f(x - 2.4 * k)},{f(base)}Q{f(c1[0])},{f(c1[1])} {f(tip[0])},{f(tip[1])}Q{f(c2[0])},{f(c2[1])} {f(x + 2.4 * k)},{f(base)}Z" fill="{R.choice(TYPHA)}"/>')
        h = R.uniform(160, 205) * k
        o.append(f'<path d="M{f(x)},{f(base)}L{f(x + 2 * k)},{f(base - h - 22 * k)}" stroke="#8a7a4c" stroke-width="{f(2 * k + .4)}"/>')
        o.append(f'<rect x="{f(x - 2.4 * k)}" y="{f(base - h)}" width="{f(8.8 * k + 1)}" height="{f(35 * k)}" rx="{f(4.4 * k + .5)}" fill="#5a3f2e" stroke="{INK}" stroke-width="1"/>')

    # ---- sedge tussocks at the water's edge
    for x in pick(int(WW / 90), lambda u: ss(0.66, 0.76, u) * (1 - ss(0.82, 0.86, u)), 0.6 * WW, 0.86 * WW):
        o.append(f'<g stroke-width="{f(1.2 * k + .3)}">')
        for _ in range(26):
            th = R.uniform(-1.3, 1.3)
            L = R.uniform(30, 58) * k
            b = (x + R.uniform(-9, 9) * k, base - 2)
            tp = (b[0] + math.sin(th) * L, b[1] - math.cos(th) * L + abs(math.sin(th)) * L * 0.5)
            c = (b[0] + math.sin(th) * L * 0.4, b[1] - L * 0.82)
            o.append(f'<path d="M{f(b[0])},{f(b[1])}Q{f(c[0])},{f(c[1])} {f(tp[0])},{f(tp[1])}" stroke="{R.choice(STRAW + GREEN)}"/>')
        o.append("</g>")

    # ---- floating leaves and a few shoots on the open water
    for x in pick(int(WW / 60), lambda u: w_pond(u) * (1 - ss(0.97, 1.0, u) * .5), 0.82 * WW, WW):
        rx = R.uniform(10, 17) * k + 2
        o.append(f'<ellipse cx="{f(x)}" cy="{f(base - wh - 0.6)}" rx="{f(rx)}" ry="{f(2.6 * k + .8)}" fill="#7f9c5b" stroke="{INK}" stroke-width=".9"/>')
    for x in pick(int(WW / 80), lambda u: w_pond(u) * .6, 0.82 * WW, WW):
        h = R.uniform(30, 70) * k
        o.append(f'<path d="M{f(x - 1.5)},{f(base - wh)}Q{f(x - 1)},{f(base - wh - h * .6)} {f(x + 2)},{f(base - wh - h)}Q{f(x + 1.4)},{f(base - wh - h * .6)} {f(x + 1.5)},{f(base - wh)}Z" fill="{R.choice(GREEN)}"/>')

    # ---- front grass: dense in the meadow, under the shrubs, thin at the reeds
    o.append('<g fill-opacity=".72">')
    for x in pick(int(WW / 6.5), lambda u: 0.55 * w_scrub(u) + w_meadow(u) + 0.4 * w_litt(u) * (1 - ss(0.7, 0.8, u))):
        h = R.uniform(25, 95) * k * (1.4 if R.random() < 0.15 else 1)
        o.append(f'<path d="{blade(R, x, base + 2, h, R.uniform(-0.45, 0.45), R.uniform(2.2, 4.5) * k + .6)}" fill="{R.choice(GREEN)}"/>')
    o.append("</g>")

    # ---- the ground line, all the way across
    o.append(f'<path d="M0,{base}H{WW}" stroke="{INK}" stroke-width="1.6"/>')
    o.append("</svg>")
    path = os.path.join(OUT, name)
    open(path, "w", encoding="utf-8").write("".join(o))
    print(name, os.path.getsize(path) // 1024, "KB")


if __name__ == "__main__":
    draw(2400, 230, 7, "d-strip-wide.svg")
    draw(1500, 220, 8, "d-strip-mid.svg")
    draw(900, 220, 9, "d-strip-narrow.svg")
