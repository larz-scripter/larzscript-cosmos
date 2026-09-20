#!/usr/bin/env python3
"""Mutation check: break the library on purpose and require the test suite to notice.

A test suite that passes tells you little until you know it can fail. Each mutant below is a small, realistic bug
(a flipped sign, a swapped argument, a wrong constant, a dropped term). For each one the relevant test file is
run against the mutated code; the mutant is 'killed' if the tests fail. Every mutant must be killed.

  python3 tools/mutation_check.py            # all mutants
  python3 tools/mutation_check.py quantum    # only mutants whose package name contains 'quantum'
"""
import os, shutil, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# (package, test file, description, old text, new text)
MUTANTS = [
 ("physmath", "test_physmath", "sin: Taylor series cut from 13 terms to 4", "  while n <= 13 {\n    term = -term * r2 / ((2 * n) * (2 * n + 1))", "  while n <= 4 {\n    term = -term * r2 / ((2 * n) * (2 * n + 1))"),
 ("physmath", "test_physmath", "sin: sign error in the third quadrant", "  if q == 2 { return -_sin_kernel(r) }", "  if q == 2 { return _sin_kernel(r) }"),
 ("physmath", "test_physmath", "atan: scale factor 4 -> 3", "  return 4.0 * total\n}\n\nfn atan(x)", "  return 3.0 * total\n}\n\nfn atan(x)"),
 ("physmath", "test_physmath", "exp: Taylor series cut to 3 terms", "  while n <= 22 {", "  while n <= 3 {"),
 ("physmath", "test_physmath", "sci: forget to carry when rounding up a decade", "  if mm >= 10 * scale { mm = round(mm / 10); e = e + 1 }", ""),
 ("physmath", "test_physmath", "sqrt_: lose the power-of-two rescale", "  return sqrt(mant) * pow(2, e)", "  return sqrt(mant) * pow(2, e + 1)"),
 ("physmath", "test_physmath", "log1p: series scaled wrongly", "    return 2.0 * total\n  }\n  return ln(1.0 + y)", "    return 1.9 * total\n  }\n  return ln(1.0 + y)"),
 ("quantum", "test_quantum", "Y gate sign flipped", "fn y(s, k) { return apply1(s, k, 0.0, 0.0, 0.0, -1.0, 0.0, 1.0, 0.0, 0.0) }", "fn y(s, k) { return apply1(s, k, 0.0, 0.0, 0.0, 1.0, 0.0, -1.0, 0.0, 0.0) }"),
 ("quantum", "test_quantum", "qubit order reversed (little-endian)", 'fn _stride(s, k) { return 2 ** (s["n"] - 1 - k) }', 'fn _stride(s, k) { return 2 ** k }'),
 ("quantum", "test_quantum", "CNOT control and target swapped", "fn cnot(s, control, target) { return apply_controlled(s, [control], target,", "fn cnot(s, control, target) { return apply_controlled(s, [target], control,"),
 ("quantum", "test_quantum", "T gate angle pi/4 -> pi/8", "fn t_gate(s, k) { return phase(s, k, m.PI / 4.0) }", "fn t_gate(s, k) { return phase(s, k, m.PI / 8.0) }"),
 ("quantum", "test_quantum", "Ry rotation direction flipped", "  return apply1(s, k, c, 0.0, -sn, 0.0, sn, 0.0, c, 0.0)", "  return apply1(s, k, c, 0.0, sn, 0.0, -sn, 0.0, c, 0.0)"),
 ("quantum", "test_quantum", "no renormalisation after measure", "  let keep = outcome == 1 ? p1 : 1.0 - p1\n  let stride = _stride(s, k)\n  let scale = 1.0 / m.sqrt_(keep)", "  let keep = outcome == 1 ? p1 : 1.0 - p1\n  let stride = _stride(s, k)\n  let scale = 1.0"),
 ("quantum", "test_quantum", "Bloch coherence term wrong sign", '      cr = cr + s["re"][i] * s["re"][j] + s["im"][i] * s["im"][j]', '      cr = cr + s["re"][i] * s["re"][j] - s["im"][i] * s["im"][j]'),
 ("qalgo", "test_qalgo", "QFT: final bit-reversal swaps dropped", "  for i in range(floor(count / 2)) { q.swap(s, first + i, first + count - 1 - i) }\n  return s\n}\n\nfn iqft", "  for i in range(0) { q.swap(s, first + i, first + count - 1 - i) }\n  return s\n}\n\nfn iqft"),
 ("qalgo", "test_qalgo", "Grover diffusion reflects about the wrong state", "  oracle_flip(s, [0])\n  _hadamard_all(s)", "  oracle_flip(s, [1])\n  _hadamard_all(s)"),
 ("qalgo", "test_qalgo", "teleportation applies Z where X is needed", "  if m1 == 1 { q.x(s, 2) }", "  if m1 == 1 { q.z(s, 2) }"),
 ("qalgo", "test_qalgo", "CHSH default settings changed", "b1=-0.7853981633974483", "b1=0.7853981633974483"),
 ("qmech", "test_qmech", "particle in a box: 8 -> 4 in the denominator", "return n * n * k.h * k.h / (8.0 * mass_kg * length_m * length_m)", "return n * n * k.h * k.h / (4.0 * mass_kg * length_m * length_m)"),
 ("qmech", "test_qmech", "hydrogen: reduced mass applied with the wrong sign", "return k.Rinf / (1.0 + k.m_e / mass)", "return k.Rinf / (1.0 - k.m_e / mass)"),
 ("qmech", "test_qmech", "tunneling: 4 E (V0 - E) -> 2 E (V0 - E)", "    return 1.0 / (1.0 + barrier_j * barrier_j * s * s / (4.0 * energy_j * (barrier_j - energy_j)))", "    return 1.0 / (1.0 + barrier_j * barrier_j * s * s / (2.0 * energy_j * (barrier_j - energy_j)))"),
 ("relativity", "test_relativity", "gamma: (1 - b)(1 + b) -> (1 - b)(1 - b)", "  return 1.0 / m.sqrt_((1.0 - b) * (1.0 + b))", "  return 1.0 / m.sqrt_((1.0 - b) * (1.0 - b))"),
 ("relativity", "test_relativity", "Schwarzschild radius loses a factor 2", "fn schwarzschild_radius(mass_kg) { return 2.0 * k.G * mass_kg / (k.c * k.c) }", "fn schwarzschild_radius(mass_kg) { return 1.0 * k.G * mass_kg / (k.c * k.c) }"),
 ("relativity", "test_relativity", "Hawking temperature: 8 pi -> 4 pi", "return k.hbar * k.c * k.c * k.c / (8.0 * m.PI * k.G * mass_kg * k.kB)", "return k.hbar * k.c * k.c * k.c / (4.0 * m.PI * k.G * mass_kg * k.kB)"),
 ("relativity", "test_relativity", "rocket: only one half of the trip counted", '  return {"ship_time_s": 2.0 * tau_half, "earth_time_s": 2.0 * t_half,', '  return {"ship_time_s": tau_half, "earth_time_s": 2.0 * t_half,'),
 ("relativity", "test_relativity", "GPS: velocity term sign flipped", "  return -v2 / (2.0 * k.c * k.c)", "  return v2 / (2.0 * k.c * k.c)"),
 ("astro", "test_astro", "absolute magnitude: 2.5 -> 2.0", "fn absolute_magnitude(luminosity_w) { return 4.74 - 2.5 * m.log10(luminosity_w / k.L_sun) }", "fn absolute_magnitude(luminosity_w) { return 4.74 - 2.0 * m.log10(luminosity_w / k.L_sun) }"),
 ("astro", "test_astro", "Kepler's third law: 2 pi -> pi", "fn orbital_period_s(semi_major_m, gm_m3_s2) { return m.TAU *", "fn orbital_period_s(semi_major_m, gm_m3_s2) { return m.PI *"),
 ("astro", "test_astro", "cosmology: dark energy term uses Om instead of 1 - Om", "+ (1.0 - omega_m))", "+ omega_m)"),
]
def run(pkg_filter=""):
    base = tempfile.mkdtemp(prefix="cosmos-mut-")
    survivors = []; killed = 0; ran = 0
    try:
        for pkg, test, desc, old, new in MUTANTS:
            if pkg_filter and pkg_filter not in pkg: continue
            work = os.path.join(base, "w"); shutil.rmtree(work, ignore_errors=True)
            shutil.copytree(os.path.join(ROOT, "packages"), os.path.join(work, "packages")); shutil.copytree(os.path.join(ROOT, "tests"), os.path.join(work, "tests"))
            f = os.path.join(work, "packages", pkg, "main.lz"); s = open(f, encoding="utf-8").read()
            if s.count(old) != 1: print("BAD MUTANT (pattern found %d times): %s: %s" % (s.count(old), pkg, desc)); survivors.append("bad pattern: " + desc); continue
            open(f, "w", encoding="utf-8").write(s.replace(old, new))
            env = dict(os.environ, LARZSCRIPT_PATH=os.path.join(work, "packages") + ":" + os.path.join(work, "tests"))
            p = subprocess.run(["larzscript", os.path.join(work, "tests", test + ".lz")], capture_output=True, text=True, env=env, timeout=600, cwd=work)
            ran += 1; dead = p.returncode != 0
            fails = [l for l in p.stdout.splitlines() if l.strip().startswith("FAIL")]
            print("%-9s %-46s %s" % ("KILLED" if dead else "SURVIVED", desc[:46], ("(%d checks failed)" % len(fails)) if fails else ("(error: %s)" % (p.stderr.strip().splitlines() or ["?"])[0][:40] if dead else "")))
            killed += dead
            if not dead: survivors.append(desc)
    finally: shutil.rmtree(base, ignore_errors=True)
    print("\n%d mutants run, %d killed, %d survived" % (ran, killed, len(survivors)))
    for x in survivors: print("  SURVIVOR:", x)
    return not survivors
if __name__ == "__main__": sys.exit(0 if run(sys.argv[1] if len(sys.argv) > 1 else "") else 1)
