"""Make drawn SVGs lighter: round the coordinates in path data to whole units,
write them as relative moves (small numbers), and drop the whitespace between
elements. Safe to run more than once.

    python _tools/slim_svg.py img/home/d-littoral.svg img/home/d-soil.svg
"""
import re
import sys

NUM = r"-?\d*\.\d+(?:e-?\d+)?|-?\d+(?:e-?\d+)?"
ARGS = {"M": 2, "L": 2, "C": 6, "Q": 4, "Z": 0}


def join(nums):
    out = ""
    for k, v in enumerate(nums):
        s = str(v)
        if k and not s.startswith("-"):
            out += " " if k % 2 == 0 else ","
        out += s
    return out


def relative(d):
    """absolute M/L/C/Q/Z path data in whole units -> relative; anything else is left as it is"""
    tokens = re.findall(rf"[A-Za-z]|{NUM}", d)
    if any(t.isalpha() and t not in ARGS for t in tokens):
        return d
    out, cmd, cur, start, i = [], None, (0, 0), (0, 0), 0
    while i < len(tokens):
        t = tokens[i]
        if t.isalpha():
            cmd, i = t, i + 1
            if cmd == "Z":
                out.append("z")
                cur = start
                continue
        n = ARGS[cmd]
        vals = [round(float(x)) for x in tokens[i:i + n]]
        if len(vals) < n:
            return d
        i += n
        rel = [v - (cur[0] if k % 2 == 0 else cur[1]) for k, v in enumerate(vals)]
        out.append(cmd.lower() + join(rel))
        cur = (vals[-2], vals[-1])
        if cmd == "M":
            start = cur
            cmd = "L"   # further pairs after M are line-tos
    return "".join(out)


def slim(match):
    attr, d = match.group(1), match.group(2)
    if attr == "d":
        return f'd="{relative(d)}"'
    nums = re.sub(NUM, lambda m: str(round(float(m.group(0)))), d)
    return f'{attr}="{nums}"'


for path in sys.argv[1:]:
    s = open(path, encoding="utf-8").read()
    before = len(s)
    s = re.sub(r'\b(d|points)="([^"]*)"', slim, s)
    s = re.sub(r">\s+<", "><", s)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(s)
    print(f"{path}: {before // 1024} KB -> {len(s) // 1024} KB")
