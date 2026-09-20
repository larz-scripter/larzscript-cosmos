from common import esc
from engine import *
import ui

def _run(driver, types, values):
    kv, rows, _ = run_native(fill(driver, types, values))
    return kv, rows

UA_DRIVER = '''import "astro" as a
import "physconst" as k
import "physmath" as m
fn kv(name, x) { print(name + "=" + m.sci(x, 11)) }
let h0 = ${h0}
let om = ${om}
let z = ${z}
if h0 <= 0 or h0 > 200 { throw {"type": "LarzValueError", "message": "Enter a Hubble constant between 1 and 200 km/s/Mpc."} }
if om <= 0 or om > 1 { throw {"type": "LarzValueError", "message": "For a flat universe the matter density must be greater than 0 and at most 1."} }
if z < 0 or z > 1500 { throw {"type": "LarzValueError", "message": "Enter a redshift between 0 and 1500."} }
let year = k.year
let mpc = k.pc * 1000000.0
let dc = a.comoving_distance_mpc(z, h0, om)
let age = a.hubble_age_gyr(h0, om)
kv("age", age)
kv("hubble_time", (mpc / 1000.0 / h0) / year / 1000000000.0)
kv("age_z", a.age_gyr_at_redshift(z, h0, om))
kv("lookback", age - a.age_gyr_at_redshift(z, h0, om))
kv("dc_mpc", dc)
kv("dl_mpc", (1.0 + z) * dc)
kv("da_mpc", dc / (1.0 + z))
kv("dc_gly", dc * mpc / k.ly / 1000000000.0)
kv("dl_gly", (1.0 + z) * dc * mpc / k.ly / 1000000000.0)
kv("vel", 0.0 + h0 * dc)
for i in range(0, 13) {
  let hh = 55.0 + i * 2.5
  print("row|curve|" + m.fixed(hh, 1) + "|" + m.fixed(a.hubble_age_gyr(hh, om), 6))
}
'''
UA_TYPES = {"h0": "num", "om": "num", "z": "num"}

def universe_age():
    ex, exr = _run(UA_DRIVER, UA_TYPES, {"h0": 67.4, "om": 0.315, "z": 1})
    sh, _ = _run(UA_DRIVER, UA_TYPES, {"h0": 73.0, "om": 0.315, "z": 1})
    eds, _ = _run(UA_DRIVER, UA_TYPES, {"h0": 70, "om": 1.0, "z": 1})
    hi, _ = _run(UA_DRIVER, UA_TYPES, {"h0": 67.4, "om": 0.315, "z": 1100})
    f = lambda d, k_: float(d[k_])
    faq = [
        ("How old is the universe?", f"About 13.8 billion years. The Planck satellite's measurement of the cosmic microwave background, interpreted with the standard flat ΛCDM model (H₀ = 67.4 km/s/Mpc, matter density Ω<sub>m</sub> = 0.315), gives {sig(f(ex, 'age'), 5)} billion years in this calculation — the published value is 13.797 ± 0.023 billion years."),
        ("What is the Hubble constant?", "The rate at which the universe is expanding today: a galaxy at distance d recedes at speed H₀ × d. It is quoted in kilometres per second per megaparsec. A value of 70 means a galaxy 100 megaparsecs away recedes at 7,000 km/s."),
        ("What is the Hubble tension?", f"Two careful ways of measuring H₀ disagree. The early-universe route (the microwave background) gives about 67.4, while the local distance ladder (supernovae calibrated with Cepheid stars) gives about 73.0 — a mismatch of roughly five standard deviations that nobody has explained. Switch between the two presets above: the higher value gives a universe {sig(f(ex, 'age') - f(sh, 'age'), 2)} billion years younger ({sig(f(sh, 'age'), 5)} billion)."),
        ("What is the difference between comoving, luminosity and angular-diameter distance?", f"They answer different questions in an expanding universe. Comoving distance is today's distance to a galaxy (for z = 1: {sig(f(ex, 'dc_gly'), 4)} billion light-years). Luminosity distance is what makes the galaxy look as dim as it does: {sig(f(ex, 'dl_gly'), 4)} billion light-years, larger by 1 + z. Angular-diameter distance, {sig(f(ex, 'da_mpc') / 1000, 4)} Gpc, is what relates its true size to the angle it covers in the sky."),
        ("Can objects be more than 13.8 billion light-years away?", f"Yes. The universe kept expanding while the light travelled, so light-travel time is not the same as distance. The edge of the observable universe is about 46 billion light-years away in comoving terms. In this model the cosmic microwave background (z \u2248 1100) has a comoving distance of {sig(f(hi, 'dc_gly'), 4)} billion light-years, although its light set out when the universe was only about {sig(f(hi, 'age_z') * 1e9, 2)} years old."),
    ]
    presets = [("Planck 2018 (H₀ = 67.4, Ωm = 0.315)", {"h0": 67.4, "om": 0.315}), ("Local measurement (H₀ = 73.0)", {"h0": 73.0, "om": 0.315}), ("Einstein–de Sitter (matter only, H₀ = 70)", {"h0": 70, "om": 1.0}),
               ("Cosmic microwave background (z = 1100)", {"h0": 67.4, "om": 0.315, "z": 1100}), ("Most distant galaxies seen (z = 10)", {"h0": 67.4, "om": 0.315, "z": 10})]
    form = ui.panel("Choose the cosmology", '<div class="cs-grid">' + ui.field("h0", "Hubble constant H₀ (km/s/Mpc)", "67.4", step="any", min="1", max="200") +
        ui.field("om", "Matter density Ωm (flat: ΩΛ = 1 − Ωm)", "0.315", step="any", min="0.01", max="1") + ui.field("z", "Redshift z of a distant galaxy", "1", step="any", min="0", max="1500") + "</div>" + ui.chips(presets), "Calculate")
    main = (form + ui.results([("age", "Age of the universe today", True), ("hubble", "Hubble time 1/H₀", False), ("lookback", "Look-back time to the galaxy", False), ("age_z", "Age of the universe when its light left", False),
                               ("dc", "Comoving distance", True), ("dl", "Luminosity distance", False), ("da", "Angular-diameter distance", False)]) +
            '<div class="cs-panel"><h2>Age of the universe for different Hubble constants</h2><div id="plot"></div><p class="cs-note">At your matter density. The two dots are the local (73) and microwave-background (67.4) measurements.</p></div>' + ui.CODE)
    body = f'''<h2>How the age of the universe is calculated</h2>
<p>In a flat universe containing matter (density parameter Ω<sub>m</sub>) and dark energy (Ω<sub>Λ</sub> = 1 − Ω<sub>m</sub>), the expansion rate at redshift <i>z</i> is H(z) = H₀·E(z) with</p>
<div class="cs-formula">E(z) = √(Ω<sub>m</sub>(1+z)³ + Ω<sub>Λ</sub>)</div>
<p>The comoving distance to a galaxy at redshift z is (c/H₀)·∫<sub>0</sub><sup>z</sup> dz′/E(z′), and the age of the universe is the integral of dt = da/(aH) from the Big Bang to today, both evaluated numerically here by Simpson's rule. For a matter-plus-dark-energy universe the age even has an exact closed form, t = 2/(3H₀√Ω<sub>Λ</sub>)·asinh(√(Ω<sub>Λ</sub>/Ω<sub>m</sub>)), which the library's tests use to check the numerical integration.</p>
<h2>Worked examples, computed above</h2>
<p>With the Planck 2018 parameters the universe is <strong>{sig(f(ex, 'age'), 5)} billion years old</strong> and the Hubble time 1/H₀ is {sig(f(ex, 'hubble_time'), 5)} billion years. A galaxy at redshift 1 has a comoving distance of {sig(f(ex, 'dc_mpc'), 5)} Mpc ({sig(f(ex, 'dc_gly'), 4)} Gly); we see it as it was {sig(f(ex, 'lookback'), 4)} billion years ago, when the universe was {sig(f(ex, 'age_z'), 4)} billion years old.</p>
<p>In a universe of matter alone (Einstein–de Sitter, Ω<sub>m</sub> = 1) with H₀ = 70 the age would be {sig(f(eds, 'age'), 5)} billion years — exactly two thirds of the Hubble time, which clashed with the estimated ages of the oldest stars \u2014 one of the arguments for dark energy that was settled by the supernova observations of 1998.</p>
<h2>What is verified</h2>
<p>Comoving distances are compared with an independent 200,000-step integration for eight combinations of H₀, Ω<sub>m</sub> and redshift up to z = 1100; ages are compared with the exact closed form; and matter-only universes are compared with the exact analytic result 2c/H₀·(1 − 1/√(1+z)). The Planck 2018 age (13.80 Gyr), the comoving distance to z = 1 (3.4 Gpc) and the Hubble-tension ordering are asserted.</p>
<p class="cs-note">Limits: flat ΛCDM without radiation or spatial curvature. Radiation matters only in the first ~50,000 years and changes today's age by a few million years at most; the published Planck age of 13.797 Gyr includes it, this calculation gives {sig(f(ex, 'age'), 5)}.</p>'''
    js = ui.page_js(UA_DRIVER, UA_TYPES, ["h0", "om", "z"], '''
    set('age',C.sig(N(k,'age'),5)+' billion years'); note('age','H₀ = '+v.h0+', Ωm = '+v.om+' (flat)');
    set('hubble',C.sig(N(k,'hubble_time'),5)+' Gyr'); note('hubble','the age if the expansion had never changed');
    set('lookback',C.sig(N(k,'lookback'),5)+' Gyr'); note('lookback','light from z = '+v.z+' set out this long ago');
    set('age_z',C.sig(N(k,'age_z'),5)+' Gyr'); note('age_z','after the Big Bang');
    set('dc',C.sig(N(k,'dc_mpc'),5)+' Mpc'); note('dc','= '+C.sig(N(k,'dc_gly'),5)+' billion light-years, today');
    set('dl',C.sig(N(k,'dl_mpc'),5)+' Mpc'); note('dl','= '+C.sig(N(k,'dl_gly'),5)+' billion light-years (1 + z times larger)');
    set('da',C.sig(N(k,'da_mpc'),5)+' Mpc'); note('da','relates true size to apparent angle');
    var pts=(rows.curve||[]).map(function(r){return [Number(r[0]),Number(r[1])];});
    C.plot($('plot'),[{name:'age of the universe (Gyr)',pts:pts,dot:[Number(v.h0),N(k,'age')]}],{xlabel:'Hubble constant H₀ (km/s/Mpc)',ylabel:'age (billion years)',label:'Age of the universe against the Hubble constant'});''', timeout=180000)
    return dict(slug="universe-age-calculator", group="cosmology", icon="\U0001f30c", short="Age of the universe",
        title="Age of the Universe Calculator — Hubble Constant & Distances", kicker="Cosmology",
        h1="Age of the Universe Calculator",
        description="Free age of the universe calculator: enter the Hubble constant and matter density to get the age, look-back time and comoving, luminosity and angular distances.",
        lead="How old is the universe, and how far away is a galaxy at a given redshift? Enter the Hubble constant and matter density — try the Hubble-tension values side by side — and get the age, look-back time and cosmological distances.",
        packages=["astro", "physconst", "physmath"], faq=faq, main=main + body, js=js)

def pages(): return [universe_age()]
