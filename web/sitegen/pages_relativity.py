import json
from common import esc
from engine import *
import ui

def _run(driver, types, values):
    kv, rows, _ = run_native(fill(driver, types, values))
    return kv, rows

# ============================================================================= time dilation
TD_DRIVER = '''import "relativity" as rel
import "physconst" as k
import "physmath" as m
fn kv(name, x) { print(name + "=" + m.sci(x, 11)) }
let v = ${speed} * ${unit}
let tau = ${dur} * ${dur_unit}
let len0 = ${length} * ${len_unit}
if v <= 0 or v >= k.c { throw {"type": "LarzValueError", "message": "Enter a speed above 0 and below the speed of light (299,792,458 m/s)."} }
let b = v / k.c
let g = rel.gamma(v)
let gm1 = b * b * g * g / (g + 1.0)
kv("v_ms", v)
kv("beta", b)
kv("gamma", g)
kv("gamma_minus_1", gm1)
kv("tau_s", tau)
kv("observer_s", rel.time_dilation(tau, v))
kv("gain_s", gm1 * tau)
kv("len_m", len0)
kv("length_m", rel.length_contraction(len0, v))
kv("ke_per_kg", rel.kinetic_energy_j(1.0, v))
kv("doppler_in", rel.doppler_factor(v))
kv("doppler_out", 1.0 / rel.doppler_factor(v))
'''
TD_TYPES = {"speed": "num", "unit": "num", "dur": "num", "dur_unit": "num", "length": "num", "len_unit": "num"}
SPEED_UNITS = [("299792458", "fraction of light speed (c = 1)"), ("1000", "km/s"), ("1", "m/s"), ("0.2777777777777778", "km/h"), ("0.44704", "mph")]

def time_dilation():
    ex_vals = {"speed": 0.99, "unit": 299792458, "dur": 1, "dur_unit": 31557600, "length": 100, "len_unit": 1}
    ex, _ = _run(TD_DRIVER, TD_TYPES, ex_vals)
    table_src = '''import "relativity" as rel
import "physconst" as k
import "physmath" as m
for row in [["a jet airliner (900 km/h)", 250.0], ["the International Space Station (7.66 km/s)", 7660.0], ["a GPS satellite (3.874 km/s)", 3874.0], ["Earth orbiting the Sun (29.78 km/s)", 29780.0], ["Parker Solar Probe at closest approach (192 km/s)", 192000.0], ["10% of light speed", 0.1 * k.c], ["50% of light speed", 0.5 * k.c], ["90% of light speed", 0.9 * k.c], ["99% of light speed", 0.99 * k.c], ["99.9% of light speed", 0.999 * k.c], ["99.99% of light speed", 0.9999 * k.c]] {
  let g = rel.gamma(row[1])
  let b = row[1] / k.c
  print("row|t|" + row[0] + "|" + m.sci(row[1], 8) + "|" + m.sci(g, 10) + "|" + m.sci(b * b * g * g / (g + 1.0) * 31557600.0, 8))
}'''
    _, rows, _ = run_native(table_src)
    trs = []
    for label, v, g, gain in rows["t"]:
        gm1 = float(gain) / YEAR                      # gamma - 1, exact (never derived from a rounded gamma)
        speed = (sig(float(v) / 299792458 * 100, 5) + "% of c") if float(v) > 1e7 else (sig(float(v) / 1000, 4) + " km/s")
        trs.append([esc(label), speed, ("1 + " + sig(gm1, 3)) if gm1 < 1e-3 else sig(float(g), 8), dur(float(gain))])
    iss = [r for r in rows["t"] if r[0].startswith("the International")][0]
    gps = [r for r in rows["t"] if r[0].startswith("a GPS")][0]
    jet = [r for r in rows["t"] if r[0].startswith("a jet")][0]
    f = lambda k_: float(ex[k_])
    faq = [
        ("Does time dilation really happen, or is it just theory?",
         "It is one of the best-tested predictions in physics. Fast-moving muons created high in the atmosphere live long enough to reach the ground only because their clocks run slow; particle accelerators routinely keep unstable particles alive far longer than their rest-frame lifetime; atomic clocks flown on aircraft have disagreed with ground clocks by exactly the predicted amounts; and GPS satellites would drift by kilometres per day if engineers did not correct for relativity."),
        ("What is the Lorentz factor?",
         "The Lorentz factor γ = 1/√(1 − v²/c²) is the number that multiplies time, divides length and scales energy and momentum in special relativity. It equals 1 at rest, "
         f"{sig(float(rows['t'][6][2]), 5)} at half the speed of light, {sig(f('gamma'), 5)} at 99% of light speed, and grows without limit as the speed approaches c."),
        ("Why does the calculator reject speeds at or above the speed of light?",
         "Because γ diverges at v = c: an object with mass would need infinite energy to reach it, and beyond it the formula gives imaginary numbers. Massless particles such as photons always travel at exactly c and do not have a rest frame, so time dilation does not apply to them."),
        ("How much do astronauts on the International Space Station age differently?",
         f"Special relativity alone says a clock moving at the station's {sig(float(iss[1]) / 1000, 3)} km/s runs slow by a factor of {sig(float(iss[3]) / YEAR, 3)}, which is about {dur(iss[3], 3)} per year. Gravity partly cancels that: the station is higher than the ground, so its clocks also run slightly fast, and the net effect is a few milliseconds per year."),
        ("Is time dilation symmetric — does each observer see the other's clock run slow?",
         "Yes, for two observers in uniform relative motion each measures the other's clock running slow, and there is no contradiction because they disagree about which events are simultaneous. The twin paradox is resolved because only the travelling twin accelerates and changes reference frames, so the twins' histories are not symmetric."),
    ]
    form = ui.panel("Set the speed and the durations", '<div class="cs-grid">' +
        ui.field("speed", "Speed", "0.99", step="any", min="0") +
        ui.select("unit", "Speed unit", SPEED_UNITS, "299792458") +
        ui.field("dur", "Time on the moving clock", "1", step="any", min="0") +
        ui.select("dur_unit", "Time unit", [("1", "seconds"), ("60", "minutes"), ("3600", "hours"), ("86400", "days"), ("31557600", "years")], "31557600") +
        ui.field("length", "Length at rest", "100", step="any", min="0") +
        ui.select("len_unit", "Length unit", [("1", "metres"), ("1000", "kilometres"), ("0.3048", "feet")], "1") + "</div>" +
        ui.chips([("Airliner", {"speed": 900, "unit": "0.2777777777777778"}), ("ISS", {"speed": 7.66, "unit": "1000"}), ("GPS satellite", {"speed": 3.874, "unit": "1000"}),
                  ("Parker Solar Probe", {"speed": 192, "unit": "1000"}), ("50% c", {"speed": 0.5, "unit": "299792458"}), ("90% c", {"speed": 0.9, "unit": "299792458"}),
                  ("99% c", {"speed": 0.99, "unit": "299792458"}), ("99.99% c", {"speed": 0.9999, "unit": "299792458"})]), "Calculate")
    main = (form + ui.results([("gamma", "Lorentz factor γ", True), ("observer", "Time a stationary observer measures", True), ("gain", "Difference between the two clocks", False),
                               ("length", "Contracted length (along the motion)", False), ("ke", "Kinetic energy per kilogram", False), ("doppler", "Light from ahead / behind", False)]) + ui.CODE)
    body = f'''<h2>What time dilation means</h2>
<p>Einstein's special theory of relativity says that the rate at which a clock ticks depends on how fast it moves relative to you. A clock moving at speed <i>v</i> runs slow by the Lorentz factor:</p>
<div class="cs-formula">Δt = γ · Δτ &nbsp;&nbsp;where&nbsp;&nbsp; γ = 1 / √(1 − v²/c²)</div>
<p>Here Δτ is the <em>proper time</em> — the time measured on the moving clock itself — and Δt is the longer time measured by an observer who sees it go by. Lengths along the direction of motion shrink by the same factor (<em>length contraction</em>), and the kinetic energy of a mass <i>m</i> is (γ − 1)<i>mc²</i>, not the familiar ½<i>mv²</i>, which is only its low-speed limit.</p>
<h2>A worked example, computed above</h2>
<p>At {sig(f("beta") * 100, 4)}% of the speed of light the Lorentz factor is <strong>{sig(f("gamma"), 8)}</strong>. One year on the moving clock therefore corresponds to <strong>{dur(f("observer_s"))}</strong> for a stationary observer — a difference of {dur(f("gain_s"))}. A {sig(ex_vals["length"], 3)} m spaceship measures {sig(f("length_m"), 4)} m long as it flies past, and each kilogram of it carries {sig(f("ke_per_kg"), 4)} joules of kinetic energy.</p>
<h2>Time dilation at different speeds</h2>
<p>The table shows how much the moving clock lags after one year. Everyday speeds change the clock by far too little to notice without an atomic clock; only near the speed of light does the effect become dramatic.</p>
{ui.table(["Moving at", "Speed", "Lorentz factor γ", "Clock difference after 1 year"], trs)}
<h2>How accurate is this calculator?</h2>
<p>γ is evaluated as 1/√((1−β)(1+β)) rather than 1/√(1−β²), so it stays accurate right up to the speed of light, and (γ−1) is computed without cancelling two nearly equal numbers, so the tiny slow-speed effects above are not lost to rounding. Both are checked against 50-digit decimal arithmetic in the library's test suite (Lorentz factor within 3 parts in 10<sup>15</sup> from β = 10<sup>−9</sup> to 1 − 10<sup>−12</sup>).</p>
<p class="cs-note">Limits: this is special relativity for uniform, straight-line motion. Real clocks near massive bodies also feel gravitational time dilation — see the <a href="/black-hole-calculator/">black hole calculator</a> for that, and the GPS correction in the library's <code>relativity</code> package, which combines both.</p>'''
    js = PAGE_PREFIX_JS(TD_DRIVER, TD_TYPES, ["speed", "unit", "dur", "dur_unit", "length", "len_unit"], '''
    var gm=N(k,'gamma'),b=N(k,'beta');
    set('gamma',C.sig(gm,8)); note('gamma','β = v/c = '+C.pct(b,6));
    set('observer',C.duration(N(k,'observer_s'))); note('observer','when '+C.duration(N(k,'tau_s'))+' pass on the moving clock');
    set('gain',C.duration(N(k,'gain_s'))); note('gain','γ − 1 = '+C.sig(N(k,'gamma_minus_1'),5));
    set('length',C.length(N(k,'length_m'),5)); note('length','from '+C.length(N(k,'len_m'),5)+' at rest');
    set('ke',C.sig(N(k,'ke_per_kg'),5)+' J'); note('ke','= '+C.pct(N(k,'gamma_minus_1'),5)+' of its rest energy');
    set('doppler','×'+C.sig(N(k,'doppler_in'),5)+' / ×'+C.sig(N(k,'doppler_out'),5)); note('doppler','frequency shift, source approaching / receding');''')
    return dict(slug="time-dilation-calculator", group="relativity", icon="⏱️", short="Time dilation",
        title="Time Dilation Calculator — Lorentz Factor & Length Contraction", kicker="Special relativity",
        h1="Time Dilation Calculator",
        description="Free time dilation calculator: enter any speed to get the Lorentz factor, dilated time, length contraction and kinetic energy — computed live by verified open-source code.",
        lead="How much slower does a moving clock tick? Enter a speed and get the exact Lorentz factor, the time a stationary observer measures, the length contraction and the relativistic kinetic energy — computed live in your browser.",
        packages=["relativity", "physconst", "physmath"], faq=faq, main=main + body, js=js)

PAGE_PREFIX_JS = ui.page_js

# ============================================================================= black holes
BH_DRIVER = '''import "relativity" as rel
import "physconst" as k
import "physmath" as m
fn kv(name, x) { print(name + "=" + m.sci(x, 11)) }
let scale = {"kg": 1.0, "g": 0.001, "earth": k.M_earth, "sun": k.M_sun}[${unit}]
let M = ${mass} * scale
if M <= 0 { throw {"type": "LarzValueError", "message": "Enter a positive mass."} }
kv("mass_kg", M)
kv("rs", rel.schwarzschild_radius(M))
kv("photon", rel.photon_sphere_radius(M))
kv("isco", rel.isco_radius(M))
kv("density", rel.horizon_mean_density(M))
kv("temp", rel.hawking_temperature(M))
kv("life_s", rel.hawking_lifetime_s(M))
kv("entropy", rel.bekenstein_hawking_entropy_kb(M))
kv("msun", M / k.M_sun)
'''
BH_TYPES = {"mass": "num", "unit": "str"}

def black_hole():
    ex, _ = _run(BH_DRIVER, BH_TYPES, {"mass": 1, "unit": "sun"})
    tbl_src = '''import "relativity" as rel
import "physconst" as k
import "physmath" as m
for row in [["Earth", k.M_earth], ["Jupiter", 1898.13 * pow(10, 24)], ["the Sun", k.M_sun], ["a 10 solar-mass stellar black hole", 10.0 * k.M_sun], ["Sagittarius A* (Milky Way centre, ~4.3 million suns)", 4300000.0 * k.M_sun], ["M87* (imaged by the Event Horizon Telescope, ~6.5 billion suns)", 6500000000.0 * k.M_sun]] {
  print("row|t|" + row[0] + "|" + m.sci(row[1], 8) + "|" + m.sci(rel.schwarzschild_radius(row[1]), 8) + "|" + m.sci(rel.horizon_mean_density(row[1]), 6))
}
let primordial = 1.73 * pow(10, 11)
print("prim=" + m.sci(rel.hawking_lifetime_s(primordial), 6))
print("earth_mm=" + m.sci(rel.schwarzschild_radius(k.M_earth) * 1000.0, 6))
print("earth_rs_temp=" + m.sci(rel.hawking_temperature(k.M_earth), 6))
'''
    kv2, rows, _ = run_native(tbl_src)
    trs = [[esc(r[0]), sig(float(r[1]), 4) + " kg", dist(float(r[2])), sig(float(r[3]), 3) + " kg/m³"] for r in rows["t"]]
    f = lambda k_: float(ex[k_])
    faq = [
        ("What is the Schwarzschild radius?", "It is the radius of the event horizon of a non-rotating black hole of a given mass: r<sub>s</sub> = 2GM/c². Anything that passes inside it — even light — cannot get out. For the Sun it is " + dist(f("rs")) + ", and for the Earth it is " + sig(float(kv2["earth_mm"]), 3) + " millimetres."),
        ("Would the Sun become a black hole if it shrank?", "Only if its entire mass were squeezed inside " + dist(f("rs")) + ". The Sun does not have enough mass to collapse into a black hole on its own; it will end as a white dwarf. Very roughly, stars beginning life with more than about 20 times the Sun's mass can leave black holes behind."),
        ("Can a black hole really evaporate?", "Stephen Hawking showed in 1974 that quantum effects make a black hole radiate like a warm body, with temperature T = ħc³/(8πGMk<sub>B</sub>). That is " + sig(f("temp"), 3) + " K for one solar mass — far colder than the 2.7 K microwave background, so real stellar black holes currently absorb more than they emit and do not evaporate. The effect has never been observed directly."),
        ("How long would a black hole take to evaporate?", "In the simple photon-only model this page uses, t = 5120πG²M³/(ħc⁴). A solar-mass black hole would need about " + sig(f("life_s") / YEAR, 3) + " years — vastly longer than the age of the universe (13.8 billion years). A black hole of about 1.7 × 10<sup>11</sup> kg would last roughly the age of the universe. Real evaporation also emits other particles, so treat the lifetimes as estimates."),
        ("What does the entropy number mean?", "The Bekenstein–Hawking entropy S = k<sub>B</sub>c³A/(4Għ) is proportional to the horizon's area A, and it is enormous: " + sig(f("entropy"), 3) + " k<sub>B</sub> for a solar-mass hole — many orders of magnitude more than the Sun itself. It is a central clue in the search for a theory of quantum gravity."),
    ]
    presets = [("Earth", {"mass": 1, "unit": "earth"}), ("The Sun", {"mass": 1, "unit": "sun"}), ("10 suns", {"mass": 10, "unit": "sun"}), ("Sagittarius A*", {"mass": 4300000, "unit": "sun"}),
               ("M87*", {"mass": 6500000000, "unit": "sun"}), ("1 kilogram", {"mass": 1, "unit": "kg"}), ("Evaporating today (1.73×10¹¹ kg)", {"mass": 173000000000, "unit": "kg"})]
    form = ui.panel("Choose a mass", '<div class="cs-grid">' + ui.field("mass", "Mass", "1", step="any", min="0") +
        ui.select("unit", "Mass unit", [("kg", "kilograms"), ("g", "grams"), ("earth", "Earth masses"), ("sun", "solar masses")], "sun") + "</div>" + ui.chips(presets), "Calculate")
    main = (form + ui.results([("rs", "Event horizon radius rₛ", True), ("photon", "Photon sphere (1.5 rₛ)", False), ("isco", "Innermost stable orbit (3 rₛ)", False),
                               ("density", "Average density inside the horizon", False), ("temp", "Hawking temperature", True), ("life", "Evaporation time (photon-only)", False),
                               ("entropy", "Entropy S / kᵇ", False)]) + ui.CODE)
    body = f'''<h2>What this calculator does</h2>
<p>A black hole of mass <i>M</i> that is not spinning and has no charge is described exactly by Schwarzschild's 1916 solution of Einstein's field equations. Its properties follow from four constants — the gravitational constant <i>G</i>, the speed of light <i>c</i>, Planck's constant ħ and Boltzmann's constant <i>k</i><sub>B</sub>:</p>
<div class="cs-formula">Horizon radius&nbsp;&nbsp; r<sub>s</sub> = 2GM / c²<br>Photon sphere&nbsp;&nbsp; 1.5 r<sub>s</sub> &nbsp;&nbsp;·&nbsp;&nbsp; innermost stable circular orbit&nbsp;&nbsp; 3 r<sub>s</sub><br>Hawking temperature&nbsp;&nbsp; T = ħc³ / (8π G M k<sub>B</sub>)<br>Evaporation time&nbsp;&nbsp; t = 5120 π G² M³ / (ħ c⁴)<br>Entropy&nbsp;&nbsp; S = k<sub>B</sub> c³ A / (4 G ħ), &nbsp;A = 4πr<sub>s</sub>²</div>
<h2>Sizes of familiar and famous black holes</h2>
<p>The calculation is linear: double the mass and the horizon radius doubles. What changes wildly is the density, because volume grows as the cube of the radius — the bigger the black hole, the <em>lower</em> the average density inside its horizon.</p>
{ui.table(["Object squeezed into a black hole", "Mass", "Horizon radius", "Average density"], trs)}
<p>The Sun's horizon radius is {dist(f("rs"))}; the Earth's is under a centimetre ({sig(float(kv2["earth_mm"]), 3)} mm). The supermassive hole at the centre of our galaxy has a horizon about {dist(float(rows["t"][4][2]))} across the radius — a few times the radius of the Sun.</p>
<h2>What is verified</h2>
<p>The horizon radius, Hawking temperature, lifetime, entropy and density are checked against independent calculations for masses from 10<sup>−8</sup> kg to 5 × 10<sup>11</sup> kg, and against published values: the Sun's 2.95 km, the Earth's 8.87 mm, a Hawking temperature of 6.17 × 10<sup>−8</sup> K for one solar mass, a lifetime near 2 × 10<sup>67</sup> years and an entropy near 10<sup>77</sup> k<sub>B</sub>.</p>
<p class="cs-note">Limits: real astrophysical black holes spin, which changes the horizon and the orbits (the Kerr solution); this page treats the non-rotating case. The evaporation time uses the simplest, photon-only model; a complete calculation includes every particle species light enough to be emitted and gives shorter lifetimes.</p>'''
    js = PAGE_PREFIX_JS(BH_DRIVER, BH_TYPES, ["mass", "unit"], '''
    var rs=N(k,'rs');
    set('rs',C.length(rs,5)); note('rs','for a mass of '+C.sig(N(k,'mass_kg'),4)+' kg ('+C.sig(N(k,'msun'),4)+' solar masses)');
    set('photon',C.length(N(k,'photon'),5)); note('photon','light can orbit here (unstably)');
    set('isco',C.length(N(k,'isco'),5)); note('isco','closest stable circular orbit');
    set('density',C.sig(N(k,'density'),4)+' kg/m³'); note('density',N(k,'density')<1000?'less dense than water':'water is 1,000 kg/m³');
    set('temp',C.sig(N(k,'temp'),4)+' K'); note('temp',N(k,'temp')<2.7255?'colder than the 2.7 K microwave background - it absorbs more than it emits':'hotter than the microwave background - it is losing mass');
    var y=N(k,'life_s')/31557600; set('life',C.duration(N(k,'life_s'))); note('life',y>1.38e10?C.sig(y/1.38e10,3)+' times the age of the universe':'shorter than the age of the universe');
    set('entropy',C.sig(N(k,'entropy'),4));''')
    return dict(slug="black-hole-calculator", group="relativity", icon="\U0001f573️", short="Black hole calculator",
        title="Black Hole Calculator — Schwarzschild Radius & Hawking Temperature", kicker="General relativity",
        h1="Black Hole Calculator",
        description="Free black hole calculator: enter a mass to get the Schwarzschild radius, photon sphere, Hawking temperature, evaporation time and entropy. Verified open-source physics.",
        lead="Squeeze any mass inside its Schwarzschild radius and it becomes a black hole. Enter a mass and get the event-horizon radius, the Hawking temperature, the evaporation time, the entropy and more — computed live in your browser.",
        packages=["relativity", "physconst", "physmath"], faq=faq, main=main + body, js=js)

# ============================================================================= relativistic rocket
RK_DRIVER = '''import "relativity" as rel
import "physconst" as k
import "physmath" as m
fn kv(name, x) { print(name + "=" + m.sci(x, 11)) }
let d = ${dist} * {"ly": k.ly, "pc": k.pc, "au": k.AU, "km": 1000.0}[${dist_unit}]
let a = ${accel} * {"g": k.g0, "ms2": 1.0}[${accel_unit}]
if d <= 0 or a <= 0 { throw {"type": "LarzValueError", "message": "Enter a positive distance and acceleration."} }
let trip = rel.rocket_trip(d, a)
let top = trip["top_speed_ms"]
let gmax = trip["gamma_max"]
kv("dist_m", d)
kv("accel", a)
kv("ship_s", trip["ship_time_s"])
kv("earth_s", trip["earth_time_s"])
kv("top_frac", top / k.c)
kv("top_gap", 1.0 / (gmax * gmax * (1.0 + top / k.c)))
kv("gamma_max", gmax)
kv("light_s", d / k.c)
'''
RK_TYPES = {"dist": "num", "dist_unit": "str", "accel": "num", "accel_unit": "str"}

def rocket():
    ex, _ = _run(RK_DRIVER, RK_TYPES, {"dist": 4.37, "dist_unit": "ly", "accel": 1, "accel_unit": "g"})
    dests = [("Proxima Centauri", 4.2465), ("Alpha Centauri", 4.37), ("Sirius", 8.6), ("Tau Ceti", 11.9), ("Trappist-1", 40.7), ("the galactic centre", 26670.0), ("the Andromeda Galaxy", 2537000.0)]
    src = '''import "relativity" as rel
import "physconst" as k
import "physmath" as m
for row in %s {
  let t = rel.rocket_trip(row[1] * k.ly, k.g0)
  print("row|t|" + row[0] + "|" + m.sci(row[1], 8) + "|" + m.sci(t["ship_time_s"], 8) + "|" + m.sci(t["earth_time_s"], 8) + "|" + m.sci(t["top_speed_ms"] / k.c, 10))
}
''' % ("[" + ", ".join('["%s", %s]' % (n, lit(d)) for n, d in dests) + "]")
    _, rows, _ = run_native(src)
    trs = [[esc(r[0]), sig(float(r[1]), 5) + " ly", dur(r[2]), dur(r[3]), pct(r[4], 8)] for r in rows["t"]]
    andro = [r for r in rows["t"] if r[0].startswith("the Andromeda")][0]
    cen = [r for r in rows["t"] if r[0] == "Alpha Centauri"][0]
    gc = [r for r in rows["t"] if r[0].startswith("the galactic")][0]
    f = lambda k_: float(ex[k_])
    faq = [
        ("Can you really reach another galaxy within a human lifetime?", f"According to relativity, yes — for the travellers. Under a constant 1 g acceleration (a comfortable 'Earth gravity' the whole way) with a turnaround at the halfway point, the Andromeda Galaxy is only about {dur(andro[2], 3)} away on the ship's clocks, even though {dur(andro[3], 3)} pass on Earth. The catch is the energy and the fuel, which are far beyond anything we can build."),
        ("Why does the ship's time differ so much from Earth's?", "The faster the ship goes the more its clocks lag behind Earth's, by the Lorentz factor γ. With constant proper acceleration the ship's speed keeps rising toward c, so γ keeps growing, and the ship can cover enormous distances in a modest amount of its own time. Distances also appear contracted from the ship's point of view."),
        ("Does the ship exceed the speed of light?", "No. Its speed approaches c but never reaches it: the ship reaches " + pct(f("top_frac"), 10) + " of c on this trip, and 1 − v/c is still " + sig(f("top_gap"), 3) + ". Each extra bit of acceleration buys less and less extra speed, but a lot more time dilation."),
        ("What does 'proper acceleration' mean?", "It is the acceleration the passengers actually feel, measured by an accelerometer on board. Holding it constant at 1 g gives crew the feel of normal Earth gravity for the whole journey. It is not the acceleration an outside observer computes, which shrinks as the ship approaches light speed."),
        ("Is this the same as a real spacecraft?", "No. It ignores the fuel needed — with any known propulsion, a ship that carries its own reaction mass could not sustain 1 g for years — as well as dust and radiation hazards and the expansion of the universe. Treat it as a demonstration of what relativity permits, not a mission plan."),
    ]
    presets = [("Proxima Centauri", {"dist": 4.2465, "dist_unit": "ly"}), ("Alpha Centauri", {"dist": 4.37, "dist_unit": "ly"}), ("Tau Ceti", {"dist": 11.9, "dist_unit": "ly"}),
               ("Trappist-1", {"dist": 40.7, "dist_unit": "ly"}), ("Galactic centre", {"dist": 26670, "dist_unit": "ly"}), ("Andromeda Galaxy", {"dist": 2537000, "dist_unit": "ly"}),
               ("Mars (opposition, 0.52 AU)", {"dist": 0.52, "dist_unit": "au"})]
    form = ui.panel("Plan a flip-and-burn trip", '<div class="cs-grid">' + ui.field("dist", "Distance", "4.37", step="any", min="0") +
        ui.select("dist_unit", "Distance unit", [("ly", "light-years"), ("pc", "parsecs"), ("au", "astronomical units"), ("km", "kilometres")], "ly") +
        ui.field("accel", "Constant acceleration", "1", step="any", min="0") + ui.select("accel_unit", "Acceleration unit", [("g", "g (9.80665 m/s²)"), ("ms2", "m/s²")], "g") + "</div>" + ui.chips(presets), "Calculate")
    main = (form + ui.results([("ship", "Time on the ship", True), ("earth", "Time on Earth", True), ("top", "Top speed (at the midpoint)", False), ("gamma", "Lorentz factor at the midpoint", False),
                               ("light", "Light needs", False)]) + ui.CODE)
    body = f'''<h2>The relativistic rocket</h2>
<p>Imagine a spaceship that accelerates at a constant rate <i>a</i>, as felt by the people aboard, for the first half of a trip, then flips over and decelerates at the same rate to arrive at rest. Special relativity gives exact formulas for this "flip-and-burn" journey. If <i>d</i> is the distance, define x = a·d / (2c²). Then, for each half of the trip:</p>
<div class="cs-formula">cosh(aτ/c) = 1 + x &nbsp;&nbsp;→&nbsp;&nbsp; ship time τ = (c/a) · acosh(1 + x)<br>Earth time t = (c/a) · √(x(2 + x)) &nbsp;&nbsp;·&nbsp;&nbsp; top speed v = c · √(x(2 + x)) / (1 + x)</div>
<p>The whole trip takes twice each half. Because the ship's speed approaches c, the ship's clocks fall further and further behind Earth's, and long journeys become possible in short ship time.</p>
<h2>Trip times at one g</h2>
<p>A ship holding 1 g (9.80665 m/s²) all the way reaches these destinations in the times below. Alpha Centauri, {sig(float(cen[1]), 3)} light-years away, is {dur(cen[2], 3)} away on the ship and {dur(cen[3], 3)} on Earth; the centre of the Milky Way is {dur(gc[2], 3)} on the ship, though light needs 26,670 years.</p>
{ui.table(["Destination", "Distance", "Ship time", "Earth time", "Top speed (fraction of c)"], trs)}
<h2>Verification</h2>
<p>The trip times and top speeds are compared with 50-digit decimal arithmetic for distances from 10<sup>12</sup> m to 25 million light-years. The function keeps the small quantity x = ad/(2c²) separate instead of forming 1 + x, which would throw away most of the digits for short trips (an early version of the library did exactly that, and the test that compared it with high-precision arithmetic caught it).</p>
<p class="cs-note">Limits: this is special relativity in flat space. It ignores fuel mass, interstellar dust and the ship's own gravity. The expansion of the universe does not enter either: it does not stretch gravitationally bound systems such as our own galaxy and the Local Group, which includes Andromeda.</p>'''
    js = PAGE_PREFIX_JS(RK_DRIVER, RK_TYPES, ["dist", "dist_unit", "accel", "accel_unit"], '''
    set('ship',C.duration(N(k,'ship_s'))); note('ship','as measured by the crew\\'s clocks');
    set('earth',C.duration(N(k,'earth_s'))); note('earth','for someone who stayed home');
    set('top',C.pct(N(k,'top_frac'),10)+' of c'); note('top','1 − v/c = '+C.sig(N(k,'top_gap'),3));
    set('gamma',C.sig(N(k,'gamma_max'),6)); note('gamma','clocks run this many times slower at the midpoint');
    set('light',C.duration(N(k,'light_s'))); note('light','for a beam of light to cover the same distance');''')
    return dict(slug="relativistic-rocket-calculator", group="relativity", icon="\U0001f680", short="Relativistic rocket",
        title="Relativistic Rocket Calculator — Ship Time at 1 g to Any Star", kicker="Special relativity",
        h1="Relativistic Rocket Calculator",
        description="Free relativistic rocket calculator: how long does a 1 g trip to Alpha Centauri or Andromeda take on the ship and on Earth? Exact special-relativity formulas, computed live.",
        lead="Accelerate at 1 g halfway, flip, decelerate the rest. How long does the trip take for the crew, how long for Earth, and how fast does the ship go? Exact special relativity, computed live in your browser.",
        packages=["relativity", "physconst", "physmath"], faq=faq, main=main + body, js=js)

def pages(): return [time_dilation(), black_hole(), rocket()]
