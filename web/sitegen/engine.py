"""Build-time helpers: fill driver templates, run them with the native interpreter (so every number quoted
in the page text is computed by the library, not typed), and format numbers like the browser does."""
import math, os, re, subprocess
from common import ROOT

def lit(x):
    """Decimal literal without exponent (mirrors Cosmos.lit in cosmos.js)."""
    from decimal import Decimal
    x = float(x)
    s = format(Decimal(repr(x)), "f")
    if "." not in s: s += ".0"
    return "(" + s + ")" if x < 0 else s

def strlit(s): return '"' + re.sub(r"[^\x20-\x7e\n]", " ", str(s)).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'

def fill(template, types, values):
    def one(m):
        k = m.group(1); t = types[k]; v = values[k]
        if t == "num": return lit(float(v))
        if t == "int":
            assert float(v) == int(float(v)); return str(int(float(v)))
        if t == "str": return strlit(v)
        raise ValueError(t)
    return re.sub(r"\$\{(\w+)\}", one, template)

def parse(lines):
    kv, rows = {}, {}
    for l in lines:
        if l.startswith("row|"):
            p = l.split("|"); rows.setdefault(p[1], []).append(p[2:]); continue
        i = l.find("=")
        if i > 0 and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", l[:i]): kv[l[:i]] = l[i + 1:]
    return kv, rows

def run_native(src, binary="larzscript"):
    env = dict(os.environ, LARZSCRIPT_PATH=os.path.join(ROOT, "packages"))
    p = subprocess.run([binary, "-e", src], capture_output=True, text=True, env=env, timeout=600)
    if p.returncode != 0: raise RuntimeError("native run failed:\n" + p.stderr + "\n--- program ---\n" + src)
    return parse(p.stdout.splitlines()) + (p.stdout,)

def num(kv, k): return float(kv[k])

# ---- formatting (mirrors cosmos.js; used only for prose)
SUPS = str.maketrans("-0123456789", "\u207b\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079")
def sig(x, n=4):
    x = float(x)
    if x == 0: return "0"
    a = abs(x)
    if 1e-4 <= a < 1e6:
        d = max(0, n - 1 - math.floor(math.log10(a)))
        t = ("%." + str(min(d, 12)) + "f") % x
        if "." in t: t = t.rstrip("0").rstrip(".")
        neg = t.startswith("-"); body = t[1:] if neg else t
        ip, _, fp = body.partition(".")
        ip = "{:,}".format(int(ip)).replace(",", "\u2009")
        return ("-" if neg else "") + ip + ("." + fp if fp else "")
    e = math.floor(math.log10(a)); m = a / 10 ** e
    ms = ("%." + str(n - 1) + "f") % m
    if float(ms) >= 10: ms = ("%." + str(n - 1) + "f") % (m / 10); e += 1
    return ("-" if x < 0 else "") + ms + " \u00d7 10" + str(e).translate(SUPS)
def pct(x, n=4): return sig(float(x) * 100, n) + "%"
YEAR = 31557600.0
def years(sec, n=4): return sig(float(sec) / YEAR, n)

_DUR = [(1e-9, "ns"), (1e-6, "µs"), (1e-3, "ms"), (1, "s"), (60, "minutes"), (3600, "hours"), (86400, "days"), (YEAR, "years"), (YEAR * 1e3, "thousand years"), (YEAR * 1e6, "million years"), (YEAR * 1e9, "billion years")]
def dur(sec, n=4):
    sec = float(sec); a = abs(sec); pick = _DUR[0]
    for u in _DUR:
        if a >= u[0]: pick = u
    return sig(sec / pick[0], n) + " " + pick[1]
LY = 9460730472580800.0
def dist(m, n=4):
    m = float(m); a = abs(m)
    if a >= LY * 0.1: return sig(m / LY, n) + " light-years"
    if a >= 149597870700.0 * 0.1: return sig(m / 149597870700.0, n) + " AU"
    for f, u in [(1e3, "km"), (1, "m"), (1e-3, "mm"), (1e-6, "µm"), (1e-9, "nm"), (1e-12, "pm")]:
        if a >= f: return sig(m / f, n) + " " + u
    return sig(m, n) + " m"
