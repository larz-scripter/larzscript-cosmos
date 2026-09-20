#!/usr/bin/env python3
"""Generate packages/physconst/main.lz and web/constants.json from one reviewed table.

Why generated: Larzscript has no exponent syntax, so every constant is a long decimal
literal - easy to mistype by hand. Values here are written once in scientific notation,
converted with exact decimal arithmetic, and cross-checked in tests/test_physconst.lz.

Sources
  exact     SI 2019 defining constants (values are exact by definition)
  derived   exact consequences of the above (computed here with 60 digits)
  CODATA18  CODATA 2018 recommended values (NIST); the standard uncertainty is recorded
  IAU       IAU 2015 Resolution B3 nominal values / IAU 2012 (astronomical unit)
"""
import json, os
from decimal import Decimal as D, getcontext
getcontext().prec = 60
PI = D("3.14159265358979323846264338327950288419716939937510582097494")
def fmt(x):   # decimal literal without exponent
    s = format(D(x), "f")
    return s if "." in s or True else s
rows = []   # (NAME, value Decimal, unit, kind, source, note, uncertainty str or "")
def add(name, val, unit, kind, source, note="", unc=""):
    rows.append((name, D(val), unit, kind, source, note, unc))

# ---- SI 2019 exact
add("c",  "299792458",        "m/s",   "exact", "SI 2019", "speed of light in vacuum")
add("h",  "6.62607015E-34",   "J s",   "exact", "SI 2019", "Planck constant")
add("e",  "1.602176634E-19",  "C",     "exact", "SI 2019", "elementary charge")
add("kB", "1.380649E-23",     "J/K",   "exact", "SI 2019", "Boltzmann constant")
add("NA", "6.02214076E23",    "1/mol", "exact", "SI 2019", "Avogadro constant")
c, h, e, kB, NA = (rows[i][1] for i in range(5))
hbar = h / (2 * PI)
add("hbar", hbar, "J s", "derived", "h / 2 pi", "reduced Planck constant")
add("R", NA * kB, "J/(mol K)", "derived", "N_A k_B", "molar gas constant")
add("F", NA * e, "C/mol", "derived", "N_A e", "Faraday constant")
sigma = 2 * PI**5 * kB**4 / (15 * h**3 * c**2)
add("sigma", sigma, "W/(m^2 K^4)", "derived", "2 pi^5 k^4 / (15 h^3 c^2)", "Stefan-Boltzmann constant")
X = D("4.96511423174427630369875913")      # root of (x-5) e^x + 5 = 0
add("wien_b", h * c / (kB * X), "m K", "derived", "h c / (k x), x = 4.965114231744276", "Wien displacement constant")
add("eV", e, "J", "derived", "e (1 V x 1 C)", "one electronvolt in joules")
add("g0", "9.80665", "m/s^2", "exact", "ISO 80000-3", "standard gravity")
add("atm", "101325", "Pa", "exact", "ISO 80000-4", "standard atmosphere")

# ---- CODATA 2018 measured
add("G",   "6.67430E-11",      "m^3/(kg s^2)", "measured", "CODATA18", "Newtonian constant of gravitation", "1.5E-15")
add("m_e", "9.1093837015E-31", "kg", "measured", "CODATA18", "electron mass", "2.8E-40")
add("m_p", "1.67262192369E-27","kg", "measured", "CODATA18", "proton mass", "5.1E-37")
add("m_n", "1.67492749804E-27","kg", "measured", "CODATA18", "neutron mass", "9.5E-37")
add("u",   "1.66053906660E-27","kg", "measured", "CODATA18", "atomic mass constant", "5.0E-37")
add("alpha","7.2973525693E-3", "",   "measured", "CODATA18", "fine-structure constant", "1.1E-12")
add("eps0","8.8541878128E-12", "F/m","measured", "CODATA18", "vacuum electric permittivity", "1.3E-21")
add("mu0", "1.25663706212E-6", "N/A^2","measured","CODATA18", "vacuum magnetic permeability", "1.9E-16")
add("Rinf","10973731.568160",  "1/m","measured", "CODATA18", "Rydberg constant", "2.1E-5")
add("a0",  "5.29177210903E-11","m",  "measured", "CODATA18", "Bohr radius", "8.0E-21")
add("lambda_C","2.42631023867E-12","m","measured","CODATA18","electron Compton wavelength","7.3E-22")
add("r_e", "2.8179403262E-15", "m",  "measured", "CODATA18", "classical electron radius", "1.3E-24")

# ---- astronomy
add("AU", "149597870700", "m", "exact", "IAU 2012 B2", "astronomical unit")
add("day", "86400", "s", "exact", "SI", "day")
add("year", "31557600", "s", "exact", "IAU (Julian year)", "Julian year = 365.25 d")
add("ly", c * D("31557600"), "m", "derived", "c x Julian year", "light-year")
add("pc", D("648000") / PI * D("149597870700"), "m", "derived", "648000/pi AU", "parsec")
add("GM_sun", "1.3271244E20", "m^3/s^2", "nominal", "IAU 2015 B3", "solar mass parameter (nominal)")
add("R_sun", "6.957E8", "m", "nominal", "IAU 2015 B3", "solar radius (nominal)")
add("L_sun", "3.828E26", "W", "nominal", "IAU 2015 B3", "solar luminosity (nominal)")
add("T_sun", "5772", "K", "nominal", "IAU 2015 B3", "solar effective temperature (nominal)")
add("GM_earth", "3.986004E14", "m^3/s^2", "nominal", "IAU 2015 B3", "terrestrial mass parameter (nominal)")
add("R_earth", "6.3781E6", "m", "nominal", "IAU 2015 B3", "Earth equatorial radius (nominal)")
add("GM_jup", "1.2668653E17", "m^3/s^2", "nominal", "IAU 2015 B3", "Jovian mass parameter (nominal)")
add("R_jup", "7.1492E7", "m", "nominal", "IAU 2015 B3", "Jupiter equatorial radius (nominal)")
add("T_cmb", "2.7255", "K", "measured", "Fixsen 2009", "cosmic microwave background temperature", "6E-4")
G = next(r[1] for r in rows if r[0] == "G")
add("M_sun", next(r[1] for r in rows if r[0] == "GM_sun") / G, "kg", "derived", "GM_sun / G", "solar mass")
add("M_earth", next(r[1] for r in rows if r[0] == "GM_earth") / G, "kg", "derived", "GM_earth / G", "Earth mass")

def literal(v):
    s = format(v.normalize() if v != 0 else v, "f")
    # keep at most 17 significant digits: a double cannot hold more
    if "." in s:
        digits = s.replace("-", "").replace(".", "").lstrip("0")
        if len(digits) > 17:
            q = D(1).scaleb(v.adjusted() - 16)
            s = format(v.quantize(q), "f")
            if "." in s: s = s.rstrip("0").rstrip(".")
    return s
def sci(v, n=12):
    return ("%." + str(n - 1) + "E") % v

lz = ["# physconst - physical and astronomical constants, GENERATED by tools/gen_constants.py (do not edit).",
      "#",
      "# Larzscript has no exponent syntax, so each value below is a plain decimal literal; the",
      "# scientific-notation value, unit and source are in the trailing comment. Kinds:",
      "#   exact     SI 2019 defining constants - exact by definition",
      "#   derived   exact consequences of those (or of IAU definitions)",
      "#   measured  CODATA 2018 recommended values (NIST) - carry a standard uncertainty",
      "#   nominal   IAU 2015 nominal values - conversion constants, not measurements",
      "#",
      "#   import \"physconst\" as k",
      "#   print(k.c)      # 299792458",
      ""]
info = {}
for name, val, unit, kind, source, note, unc in rows:
    lit = literal(val)
    lz.append("let %s = %s   # %s %s | %s | %s%s" % (name, lit, sci(val), unit, kind, source, (" | u=" + unc) if unc else ""))
    info[name] = {"value": float(val), "sci": sci(val), "unit": unit, "kind": kind, "source": source, "note": note, "uncertainty": unc}
lz.append("")
lz.append("# name -> {unit, kind, source, note} for docs and tools")
def q(s): return '"' + s.replace('"', '\\"') + '"'
lz.append("let INFO = {")
lz.append(",\n".join('  %s: {"unit": %s, "kind": %s, "source": %s, "note": %s}' % (q(n), q(v["unit"]), q(v["kind"]), q(v["source"]), q(v["note"])) for n, v in info.items()))
lz.append("}")
lz.append("")
lz.append("let PI = 3.141592653589793")
open("packages/physconst/main.lz", "w").write("\n".join(lz) + "\n")
os.makedirs("web", exist_ok=True)
json.dump(info, open("web/constants.json", "w"), indent=1)
print("wrote %d constants" % len(rows))
