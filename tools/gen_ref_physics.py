#!/usr/bin/env python3
"""Independent references for tests/test_relativity.lz, test_astro.lz and test_qmech.lz.

Where floating point could hide an error (gamma near 1, low-speed kinetic energy, rapidity,
the relativistic rocket) the reference uses 50-digit Decimal arithmetic on the EXACT input
doubles. Cosmology uses closed forms (flat LCDM age via asinh; Einstein-de Sitter distance)
plus an independent high-resolution Simpson integral. Writes tests/data_physics.lz."""
import json, math, random
from decimal import Decimal as D, getcontext
getcontext().prec = 50
random.seed(99)
K = {n: v["value"] for n, v in json.load(open("web/constants.json")).items()}
def lit(x): return "0" if x == 0 else format(D(repr(float(x))), "f")
def dec(x): return D(float(x))              # exact binary value of the double
c, G, hbar, kB = K["c"], K["G"], K["hbar"], K["kB"]
Dc = dec(c)

def gamma_dec(b): b = dec(b); return 1 / ((1 - b) * (1 + b)).sqrt()
def atanh_dec(b): b = dec(b); return ((1 + b) / (1 - b)).ln() / 2
def cosh_dec(x): e = x.exp(); return (e + 1 / e) / 2
def acosh_dec(x): return (x + (x * x - 1).sqrt()).ln()

out = {}
betas = [1e-9, 1e-5, 0.001, 0.1, 0.5, 0.8, 0.9, 0.99, 0.999, 0.99999, 0.999999999, 1 - 1e-12] + [random.uniform(0, 1) for _ in range(20)]
out["GAMMA"] = [[b, gamma_dec(b)] for b in betas]
out["RAPIDITY"] = [[b, atanh_dec(b)] for b in betas]
ke = []
for _ in range(25):
    mass = 10 ** random.uniform(-31, 3); v = 10 ** random.uniform(-2, 8.4)
    b = D(float(v)) / Dc; g = 1 / ((1 - b) * (1 + b)).sqrt()
    ke.append([mass, v, (g - 1) * dec(mass) * Dc * Dc])
out["KE"] = ke
add = []
for _ in range(25):
    u, v = random.uniform(-0.99, 0.99) * c, random.uniform(-0.99, 0.99) * c
    add.append([u, v, (u + v) / (1 + u * v / c ** 2)])
out["ADD"] = add
out["DOPPLER"] = [[v, math.sqrt((1 + v / c) / (1 - v / c))] for v in [random.uniform(-0.95, 0.95) * c for _ in range(20)]]
rk = []
for dist, acc in [(4.37 * K["ly"], K["g0"]), (25e6 * K["ly"], K["g0"]), (1e12, 1.0), (2.54e6 * K["ly"], 2 * K["g0"]), (10 * K["ly"], 0.5 * K["g0"])]:
    ch = 1 + dec(acc) * dec(dist) / 2 / (Dc * Dc)
    tau = 2 * Dc / dec(acc) * acosh_dec(ch); tt = 2 * Dc / dec(acc) * (ch * ch - 1).sqrt(); top = Dc * (ch * ch - 1).sqrt() / ch
    rk.append([dist, acc, tau, tt, top, ch])
out["ROCKET"] = rk
# general relativity, plain floats
masses = [1.0, K["M_earth"], K["M_sun"], 4.3e6 * K["M_sun"], 1e-8, 5.0e11]
gr = []
for M in masses:
    rs = 2 * G * M / c ** 2
    gr.append([M, rs, hbar * c ** 3 / (8 * math.pi * G * M * kB), 5120 * math.pi * G ** 2 * M ** 3 / (hbar * c ** 4),
               c ** 3 * (4 * math.pi * rs ** 2) / (4 * G * hbar), M / (4 / 3 * math.pi * rs ** 3)])
out["GR"] = gr
grt = []
for _ in range(20):
    M = 10 ** random.uniform(24, 40); rs = 2 * G * M / c ** 2; r = rs * 10 ** random.uniform(0.01, 6)
    x = D(rs) / D(r); zz = 1 / (1 - x).sqrt() - 1          # 50-digit: plain floats cancel badly in weak fields
    grt.append([M, r, math.sqrt(1 - rs / r), zz, math.sqrt(2 * G * M / r)])
out["GRT"] = grt
# GPS
gps = []
for r in [26561750.0, 20200e3 + 6371e3, 42164e3, 7000e3]:
    grav = K["GM_earth"] / c ** 2 * (1 / K["R_earth"] - 1 / r); vel = -(K["GM_earth"] / r) / (2 * c ** 2)
    gps.append([r, (grav + vel) * 86400e6, grav * 86400e6, vel * 86400e6])
out["GPS"] = gps
# astro
star = []
for _ in range(15):
    R = 10 ** random.uniform(7, 12); T = 10 ** random.uniform(3, 4.7)
    L = 4 * math.pi * R ** 2 * K["sigma"] * T ** 4
    star.append([R, T, L, math.sqrt(L / (4 * math.pi * K["sigma"] * T ** 4)), (L / (4 * math.pi * R ** 2 * K["sigma"])) ** 0.25, K["wien_b"] / T])
out["STAR"] = star
mags = [[L, 4.74 - 2.5 * math.log10(L / K["L_sun"])] for L in [10 ** random.uniform(22, 32) for _ in range(12)]]
out["MAG"] = mags
dm = [[d, 5 * math.log10(d / 10)] for d in [10 ** random.uniform(-1, 9) for _ in range(12)]]
out["DISTMOD"] = dm
eq = []
for _ in range(15):
    Ts, Rs, a, A = 10 ** random.uniform(3.4, 4.5), 10 ** random.uniform(8, 10.5), 10 ** random.uniform(9.5, 13), random.uniform(0, 0.7)
    eq.append([Ts, Rs, a, A, Ts * math.sqrt(Rs / (2 * a)) * (1 - A) ** 0.25])
out["EQTEMP"] = eq
kep = []
for _ in range(15):
    a = 10 ** random.uniform(7, 13); gm = 10 ** random.uniform(12, 21)
    kep.append([a, gm, 2 * math.pi * math.sqrt(a ** 3 / gm)])
out["KEPLER"] = kep
# cosmology
def E(z, om): return math.sqrt(om * (1 + z) ** 3 + (1 - om))
def simpson(f, lo, hi, n):
    h = (hi - lo) / n; s = f(lo) + f(hi)
    for i in range(1, n): s += (4 if i % 2 else 2) * f(lo + i * h)
    return s * h / 3
MPC = K["pc"] * 1e6
def age_closed(z, h0, om):    # flat LCDM (matter + Lambda), exact
    ol = 1 - om; a = 1 / (1 + z); h0s = h0 * 1000 / MPC
    return 2 / (3 * h0s * math.sqrt(ol)) * math.asinh(math.sqrt(ol / om) * a ** 1.5) / (K["year"] * 1e9)
cos = []
for z, h0, om in [(0.1, 67.4, 0.315), (0.5, 70, 0.3), (1.0, 67.4, 0.315), (2.0, 73.0, 0.3), (5.0, 67.4, 0.315), (0.01, 70, 0.3), (10.0, 70, 0.3), (1100.0, 67.4, 0.315)]:
    dc = (c / 1000 / h0) * simpson(lambda x: 1 / E(x, om), 0, z, 200000)
    cos.append([z, h0, om, dc, age_closed(z, h0, om), age_closed(0, h0, om)])
out["COSMO"] = cos
eds = [[z, 2 * (c / 1000 / 70.0) * (1 - 1 / math.sqrt(1 + z))] for z in (0.1, 0.5, 1, 3, 10)]
out["EDS"] = eds

with open("tests/data_physics.lz", "w") as f:
    f.write("# GENERATED by tools/gen_ref_physics.py - independent references (50-digit Decimal / closed forms). Do not edit.\n")
    for name, rows in out.items():
        f.write("let REF_%s = [\n  %s\n]\n" % (name, ",\n  ".join("[" + ", ".join(lit(x) for x in row) + "]" for row in rows)))
print("wrote tests/data_physics.lz:", {k: len(v) for k, v in out.items()})
