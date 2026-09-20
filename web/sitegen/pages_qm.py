import json
from common import esc
from engine import *
import ui

def _run(driver, types, values):
    kv, rows, _ = run_native(fill(driver, types, values))
    return kv, rows

RGB_JS = r"""
function rgb(nm){var r=0,g=0,b=0;
 if(nm>=380&&nm<440){r=-(nm-440)/60;b=1;}else if(nm>=440&&nm<490){g=(nm-440)/50;b=1;}else if(nm>=490&&nm<510){g=1;b=-(nm-510)/20;}
 else if(nm>=510&&nm<580){r=(nm-510)/70;g=1;}else if(nm>=580&&nm<645){r=1;g=-(nm-645)/65;}else if(nm>=645&&nm<=750){r=1;}else return null;
 var f=nm<420?0.3+0.7*(nm-380)/40:(nm>700?0.3+0.7*(750-nm)/50:1);
 return 'rgb('+[r,g,b].map(function(c){return Math.round(255*Math.pow(c*f,0.8));}).join(',')+')';}
function region(nm){return nm<380?'Ultraviolet':(nm<=750?'Visible light':'Infrared');}
"""

# ============================================================================= hydrogen
HY_DRIVER = '''import "qmech" as qm
import "physconst" as k
import "physmath" as m
fn kv(name, x) { print(name + "=" + m.sci(x, 11)) }
let hi = ${upper}
let lo = ${lower}
let inf = ${infinite} == 1
if hi <= lo { throw {"type": "LarzValueError", "message": "The upper level must be higher than the lower level (the atom emits a photon when an electron drops down)."} }
let wl = qm.hydrogen_wavelength_nm(hi, lo, inf)
kv("wl_nm", wl)
kv("air_nm", qm.vacuum_to_air_nm(wl))
kv("air_ok", wl >= 200.0 and wl <= 2000.0 ? 1.0 : 0.0)
kv("energy_ev", qm.photon_energy_ev(wl * 0.000000001))
kv("freq_thz", k.c / (wl * 0.000000001) / 1000000000000.0)
kv("e_hi", qm.hydrogen_energy_ev(hi, inf))
kv("e_lo", qm.hydrogen_energy_ev(lo, inf))
kv("limit_nm", qm.hydrogen_series_limit_nm(lo, inf))
print("series=" + qm.hydrogen_series(lo))
for n in range(lo + 1, lo + 8) {
  let w = qm.hydrogen_wavelength_nm(n, lo, inf)
  print("row|lines|" + str(n) + "|" + m.sci(w, 9) + "|" + m.sci(qm.vacuum_to_air_nm(w), 9) + "|" + m.sci(qm.photon_energy_ev(w * 0.000000001), 9))
}
for n in range(1, 9) { print("row|levels|" + str(n) + "|" + m.sci(qm.hydrogen_energy_ev(n, inf), 9) + "|" + m.sci(qm.hydrogen_radius_m(n) * 10000000000.0, 6)) }
'''
HY_TYPES = {"upper": "int", "lower": "int", "infinite": "int"}

def hydrogen():
    ex, exrows = _run(HY_DRIVER, HY_TYPES, {"upper": 3, "lower": 2, "infinite": 0})
    bal = {int(r[0]): r for r in exrows["lines"]}
    kvL, rowsL = _run(HY_DRIVER, HY_TYPES, {"upper": 2, "lower": 1, "infinite": 0})
    kvI, _ = _run(HY_DRIVER, HY_TYPES, {"upper": 3, "lower": 2, "infinite": 1})
    f = lambda k_: float(ex[k_])
    names = {3: "Hα (H-alpha)", 4: "Hβ (H-beta)", 5: "Hγ (H-gamma)", 6: "Hδ (H-delta)", 7: "Hε", 8: "Hζ", 9: "Hη"}
    trs = [[names[n], "3→2".replace("3", str(n)), sig(float(bal[n][1]), 6) + " nm", sig(float(bal[n][2]), 6) + " nm", sig(float(bal[n][3]), 5) + " eV"] for n in range(3, 8)]
    faq = [
        ("How does the Bohr model explain the hydrogen spectrum?", "Niels Bohr proposed in 1913 that the electron can only occupy certain energy levels E<sub>n</sub> = −13.6 eV / n². When it drops from a higher level to a lower one it emits a photon whose energy equals the difference, and because the levels are discrete the emitted light has only certain wavelengths — the atom's spectral lines."),
        ("Why does this page give 656.47 nm for H-alpha when textbooks say 656.28 nm?", f"The textbook 656.28 nm is the wavelength <em>in air</em>; light slows down slightly in air, so its wavelength shrinks. This page reports the vacuum wavelength, {sig(f('wl_nm'), 6)} nm, and converts to air with the standard Edlén formula, giving {sig(f('air_nm'), 6)} nm. Astronomers and spectroscopists must always check which convention a wavelength uses."),
        ("What is the infinite nuclear mass option?", f"The simplest form of the Rydberg formula assumes the nucleus stays perfectly still. In reality the electron and proton orbit their common centre of mass, which changes every level by about 1 part in 1,836 (the ratio of the electron and proton masses). With an infinitely heavy nucleus H-alpha comes out at {sig(float(kvI['wl_nm']), 6)} nm instead of {sig(f('wl_nm'), 6)} nm — the same effect that made deuterium's discovery possible from its slightly shifted lines."),
        ("Is the Bohr model exact?", "It reproduces the gross structure of hydrogen very well — wavelengths agree with measurements to about one part in 100,000 — but real hydrogen also has fine structure, the Lamb shift and hyperfine splitting, which split each line further. Full quantum mechanics (the Schrödinger and Dirac equations, then quantum electrodynamics) is needed to explain those."),
        ("Which hydrogen lines can I see?", "Only transitions ending on level 2 — the Balmer series — fall in the visible range: H-alpha is red, H-beta blue-green, H-gamma and H-delta violet. Transitions to level 1 (the Lyman series) are ultraviolet; those to level 3 and above (Paschen, Brackett) are infrared."),
    ]
    presets = [("Hα (3→2)", {"upper": 3, "lower": 2}), ("Hβ (4→2)", {"upper": 4, "lower": 2}), ("Hγ (5→2)", {"upper": 5, "lower": 2}), ("Lyman α (2→1)", {"upper": 2, "lower": 1}),
               ("Paschen α (4→3)", {"upper": 4, "lower": 3}), ("Brackett α (5→4)", {"upper": 5, "lower": 4}), ("Balmer limit region (12\u21922)", {"upper": 12, "lower": 2})]
    up = [(str(i), str(i)) for i in range(2, 13)]
    lo = [(str(i), str(i)) for i in range(1, 8)]
    form = ui.panel("Choose the transition", '<div class="cs-grid">' + ui.select("upper", "Electron drops from level n =", up, "3") + ui.select("lower", "to level n =", lo, "2") +
        ui.select("infinite", "Nucleus", [("0", "real hydrogen (proton mass)"), ("1", "infinitely heavy nucleus")], "0") + "</div>" + ui.chips(presets), "Calculate")
    main = (form + ui.results([("wl", "Wavelength in vacuum", True), ("air", "Wavelength in air", False), ("energy", "Photon energy", True), ("freq", "Frequency", False), ("region", "Region", False), ("levels", "Energy levels", False)]) +
            '<div class="cs-panel"><h2>The colour of this line</h2><div class="cs-swatch" id="swatch" style="background:#0b0f1a" aria-hidden="true"></div><div class="cs-note" id="swatch-note"></div></div>'
            '<div class="cs-panel"><h2>Other lines in the same series</h2><div id="lines"></div></div>'
            '<div class="cs-panel"><h2>Hydrogen energy levels</h2><div id="levels"></div></div>' + ui.CODE)
    body = f'''<h2>Rydberg formula and the Bohr levels</h2>
<p>An electron in hydrogen can only have certain energies. In the Bohr model the level with principal quantum number <i>n</i> has energy E<sub>n</sub> = −<i>hcR</i> / <i>n</i>², where <i>R</i> is the Rydberg constant. When the electron drops from level <i>n</i><sub>u</sub> to a lower level <i>n</i><sub>l</sub> the atom emits a photon of wavelength <i>λ</i>:</p>
<div class="cs-formula">1/λ = R · (1/n<sub>l</sub>² − 1/n<sub>u</sub>²)&nbsp;&nbsp;&nbsp;·&nbsp;&nbsp;&nbsp;E<sub>photon</sub> = hc/λ</div>
<p>The ground state (<i>n</i> = 1) sits at −13.6 eV, the energy needed to strip the electron away entirely. Each series of lines is named for the level it ends on: Lyman (<i>n</i>=1, ultraviolet), Balmer (<i>n</i>=2, visible), Paschen (<i>n</i>=3, infrared), and so on.</p>
<h2>The Balmer lines, computed above</h2>
<p>For real hydrogen, with the proton's finite mass included, the four visible Balmer lines fall at:</p>
{ui.table(["Line", "Transition", "Vacuum wavelength", "Air wavelength", "Photon energy"], trs)}
<p>The air values match the accepted laboratory wavelengths (656.28, 486.13, 434.05 and 410.17 nm) to within about 0.01 nm, roughly one part in 50,000 \u2014 the accuracy limit of the Bohr model. The series converges to the Balmer limit at {sig(float(exrows["lines"][0][1]) if False else float(ex["limit_nm"]), 6)} nm (vacuum). The Lyman-α line, the strongest line in the universe's hydrogen, is at {sig(float(kvL["wl_nm"]), 6)} nm.</p>
<h2>What is verified</h2>
<p>The ground-state energy matches the CODATA Rydberg energy (13.605693122994 eV) to 10 significant figures for an infinitely heavy nucleus, and the visible Balmer lines, Lyman-α and the Balmer limit agree with measured wavelengths to within the accuracy of the model. The reduced-mass shift and the vacuum-to-air conversion have their own tests.</p>
<p class="cs-note">Limits: this is the Bohr model with a reduced-mass correction. It does not include fine structure, the Lamb shift or hyperfine structure, so wavelengths are good to about 10 parts per million. It is for hydrogen only; hydrogen-like ions have their levels scaled by the nuclear charge squared.</p>'''
    extra = RGB_JS + '''
C.tool.__noop=1;'''
    js = ui.page_js(HY_DRIVER, HY_TYPES, ["upper", "lower", "infinite"], '''
    set('wl',C.sig(N(k,'wl_nm'),7)+' nm'); note('wl','in vacuum');
    if(N(k,'air_ok')){set('air',C.sig(N(k,'air_nm'),7)+' nm'); note('air','in standard air (Edlén formula)');}else{set('air','—'); note('air','air conversion is defined for 200–2000 nm');}
    set('energy',C.sig(N(k,'energy_ev'),6)+' eV'); note('energy','= Eₘ − Eₙ = '+C.sig(N(k,'e_hi'),5)+' − ('+C.sig(N(k,'e_lo'),5)+') eV');
    set('freq',C.sig(N(k,'freq_thz'),6)+' THz'); note('freq','photon frequency');
    var nm=N(k,'wl_nm'); set('region',region(nm)); note('region',k.series+' series');
    set('levels','n = '+v.lower+' → series limit '+C.sig(N(k,'limit_nm'),6)+' nm'); note('levels','shortest wavelength of this series (vacuum)');
    var c=rgb(nm); $('swatch').style.background=c||'#0b0f1a'; $('swatch-note').textContent=c?('Approximate colour of '+C.sig(nm,4)+' nm light on a screen.'):'Invisible to the human eye ('+region(nm).toLowerCase()+').';
    var h='<div class="cs-tbl"><table class="lz"><thead><tr><th>Transition</th><th>Vacuum λ (nm)</th><th>Air λ (nm)</th><th>Energy (eV)</th><th></th></tr></thead><tbody>';
    (rows.lines||[]).forEach(function(r){var w=Number(r[1]),col=rgb(w);h+='<tr><td>'+r[0]+' → '+v.lower+'</td><td>'+C.sig(w,7)+'</td><td>'+(w>=200&&w<=2000?C.sig(Number(r[2]),7):'—')+'</td><td>'+C.sig(Number(r[3]),5)+'</td><td>'+(col?'<span style="display:inline-block;width:28px;height:14px;border-radius:4px;background:'+col+'"></span>':'')+'</td></tr>';});
    $('lines').innerHTML=h+'</tbody></table></div>';
    var l='<div class="cs-tbl"><table class="lz"><thead><tr><th>Level n</th><th>Energy (eV)</th><th>Orbit radius (Å)</th></tr></thead><tbody>';
    (rows.levels||[]).forEach(function(r){l+='<tr><td>'+r[0]+'</td><td>'+C.sig(Number(r[1]),6)+'</td><td>'+C.sig(Number(r[2]),4)+'</td></tr>';});
    $('levels').innerHTML=l+'</tbody></table></div>';''', extra=RGB_JS.replace("function rgb", "function rgb"))
    # the colour helpers must exist before render runs: prepend them
    js = ui.PAGE_PREFIX + RGB_JS + js[len(ui.PAGE_PREFIX):] .replace(RGB_JS, "")
    return dict(slug="hydrogen-spectrum-calculator", group="quantum mechanics", icon="\U0001f308", short="Hydrogen spectrum",
        title="Hydrogen Spectrum Calculator — Balmer, Lyman & Paschen Lines", kicker="Quantum mechanics",
        h1="Hydrogen Spectrum Calculator",
        description="Free hydrogen spectrum calculator: wavelength, energy and colour of any Bohr-model transition — Balmer, Lyman, Paschen series. Verified against CODATA.",
        lead="Pick the level an electron drops from and the level it lands on, and see the exact wavelength, photon energy and colour of the light the hydrogen atom emits — computed live from the Rydberg formula.",
        packages=["qmech", "physconst", "physmath"], faq=faq, main=main + body, js=js)

# ============================================================================= de Broglie
DB_DRIVER = '''import "qmech" as qm
import "relativity" as rel
import "physconst" as k
import "physmath" as m
fn kv(name, x) { print(name + "=" + m.sci(x, 11)) }
let who = ${particle}
let mass = {"electron": k.m_e, "proton": k.m_p, "neutron": k.m_n, "baseball": 0.145, "person": 70.0, "custom": ${mass_custom}}[who]
if mass <= 0 { throw {"type": "LarzValueError", "message": "Enter a positive mass."} }
let mode = ${mode}
let speed = 0.0
let lam = 0.0
if mode == "speed" {
  speed = ${speed} * ${speed_unit}
  if speed <= 0 or speed >= k.c { throw {"type": "LarzValueError", "message": "Enter a speed above 0 and below the speed of light."} }
  lam = qm.de_broglie_relativistic(mass, speed)
} else {
  let charge = {"electron": k.e, "proton": k.e}.get(who)
  if charge == nil { throw {"type": "LarzValueError", "message": "Only the electron and the proton can be accelerated through a voltage in this calculator."} }
  let volts = ${volts}
  if volts <= 0 { throw {"type": "LarzValueError", "message": "Enter a positive accelerating voltage."} }
  lam = qm.de_broglie_from_voltage_relativistic(mass, charge, volts)
  speed = rel.speed_from_kinetic_energy(mass, charge * volts)
}
kv("mass", mass)
kv("speed", speed)
kv("beta", speed / k.c)
kv("lambda_m", lam)
kv("lambda_nonrel", qm.de_broglie_wavelength(mass, speed))
kv("momentum", k.h / lam)
kv("ke_j", rel.kinetic_energy_j(mass, speed))
kv("ke_ev", rel.kinetic_energy_j(mass, speed) / k.eV)
kv("vs_bohr", lam / k.a0)
kv("vs_proton", lam / 0.00000000000000084)
'''
DB_TYPES = {"particle": "str", "mass_custom": "num", "mode": "str", "speed": "num", "speed_unit": "num", "volts": "num"}

def de_broglie():
    ex, _ = _run(DB_DRIVER, DB_TYPES, {"particle": "electron", "mass_custom": 1, "mode": "volts", "speed": 1, "speed_unit": 1, "volts": 100000})
    tbl_src = '''import "qmech" as qm
import "physconst" as k
import "physmath" as m
for v in [50.0, 100.0, 1000.0, 10000.0, 100000.0, 200000.0, 300000.0] {
  print("row|v|" + m.sci(v, 6) + "|" + m.sci(qm.de_broglie_from_voltage(k.m_e, k.e, v), 8) + "|" + m.sci(qm.de_broglie_from_voltage_relativistic(k.m_e, k.e, v), 8))
}
print("ball=" + m.sci(qm.de_broglie_wavelength(0.145, 40.0), 6))
print("thermal_n=" + m.sci(qm.de_broglie_wavelength(k.m_n, 2200.0), 6))
print("h_e_1ev=" + m.sci(qm.de_broglie_from_voltage(k.m_e, k.e, 1.0), 6))
'''
    kv2, rows, _ = run_native(tbl_src)
    trs = [[sig(float(r[0]), 6) + " V", sig(float(r[1]) * 1e12, 5) + " pm", sig(float(r[2]) * 1e12, 5) + " pm", pct(float(r[1]) / float(r[2]) - 1, 3)] for r in rows["v"]]
    f = lambda k_: float(ex[k_])
    faq = [
        ("What is the de Broglie wavelength?", "Louis de Broglie proposed in 1924 that every particle has a wavelength λ = h/p, where h is Planck's constant and p the particle's momentum. Electrons, neutrons and even whole atoms show wave interference, and the wavelength is what sets the size of diffraction patterns."),
        ("Why does a baseball not show wave behaviour?", "Its wavelength is absurdly small. A 0.145 kg baseball at 40 m/s has λ = " + sig(float(kv2["ball"]), 3) + " m — about 10<sup>19</sup> times smaller than a proton — so no experiment could ever detect its wave nature."),
        ("What accelerating voltage do electron microscopes use, and what wavelength results?", "Transmission electron microscopes typically run at 80–300 kV. At 100 kV the wavelength is " + sig(f("lambda_m") * 1e12, 4) + " pm — about " + sig(1 / f("vs_bohr"), 2) + " times smaller than a hydrogen atom's Bohr radius — which is why electron microscopes can resolve individual atoms while optical microscopes (λ ≈ 500,000 pm) cannot."),
        ("Why does the relativistic value differ from the simple formula?", "At 100 kV an electron already moves at " + pct(f("beta"), 3) + " of the speed of light. The simple non-relativistic wavelength h/√(2meV) then comes out " + pct(f("lambda_nonrel") / f("lambda_m") - 1, 2) + " too long. This page uses relativistic momentum, p = γmv, so it stays correct at any speed."),
        ("What is a thermal neutron's wavelength?", "A neutron moving at 2,200 m/s — the typical speed at room temperature — has λ = " + sig(float(kv2["thermal_n"]) * 1e10, 4) + " Å, about the spacing between atoms in a crystal, which is why neutron diffraction reveals crystal structure."),
    ]
    presets = [("100 kV electron (TEM)", {"particle": "electron", "mode": "volts", "volts": 100000}), ("300 kV electron", {"particle": "electron", "mode": "volts", "volts": 300000}),
               ("100 V electron", {"particle": "electron", "mode": "volts", "volts": 100}), ("Thermal neutron 2200 m/s", {"particle": "neutron", "mode": "speed", "speed": 2200, "speed_unit": "1"}),
               ("Baseball 40 m/s", {"particle": "baseball", "mode": "speed", "speed": 40, "speed_unit": "1"}), ("Person walking 1.4 m/s", {"particle": "person", "mode": "speed", "speed": 1.4, "speed_unit": "1"}),
               ("Proton at 1% c", {"particle": "proton", "mode": "speed", "speed": 0.01, "speed_unit": "299792458"})]
    form = ui.panel("Choose a particle and how it moves", '<div class="cs-grid">' +
        ui.select("particle", "Particle", [("electron", "electron"), ("proton", "proton"), ("neutron", "neutron"), ("baseball", "baseball (0.145 kg)"), ("person", "person (70 kg)"), ("custom", "custom mass…")], "electron") +
        ui.field("mass_custom", "Custom mass (kg)", "1", step="any", min="0", hint="used only when “custom” is selected") +
        ui.select("mode", "Specify by", [("volts", "accelerating voltage (electron/proton)"), ("speed", "speed")], "volts") +
        ui.field("volts", "Accelerating voltage (V)", "100000", step="any", min="0") + ui.field("speed", "Speed", "2200", step="any", min="0") +
        ui.select("speed_unit", "Speed unit", [("1", "m/s"), ("1000", "km/s"), ("299792458", "fraction of c"), ("0.2777777777777778", "km/h")], "1") + "</div>" + ui.chips(presets), "Calculate")
    main = (form + ui.results([("lambda", "de Broglie wavelength λ", True), ("nonrel", "Non-relativistic λ (for comparison)", False), ("speed", "Speed", False), ("momentum", "Momentum", False),
                               ("ke", "Kinetic energy", False), ("scale", "Compared with an atom", False)]) + ui.CODE)
    body = f'''<h2>Matter waves</h2>
<p>Quantum mechanics says that particles behave as waves, with a wavelength set by their momentum:</p>
<div class="cs-formula">λ = h / p&nbsp;&nbsp;&nbsp;with&nbsp;&nbsp;&nbsp;p = γ m v&nbsp;&nbsp;&nbsp;(relativistic momentum)</div>
<p>For a charged particle accelerated through a voltage <i>V</i>, the momentum follows from its energy, <i>pc</i> = √(<i>KE</i>(<i>KE</i> + 2<i>mc</i>²)) with <i>KE</i> = <i>eV</i>, so λ = <i>hc</i> / √(<i>eV</i>(<i>eV</i> + 2<i>mc</i>²)). This is the formula electron-microscope designers use.</p>
<h2>Electron wavelengths, computed above</h2>
<p>The table compares the simple formula λ = h/√(2meV) with the relativistic one. They agree at low voltage and part ways as the electron nears the speed of light — at 300 kV the simple formula is {pct(float(rows["v"][-1][1]) / float(rows["v"][-1][2]) - 1, 2)} off.</p>
{ui.table(["Accelerating voltage", "Simple formula", "Relativistic (correct)", "Simple formula too long by"], trs)}
<p>At {sig(ex_v(ex, "volts") if False else 100000, 6)} V an electron has a wavelength of <strong>{sig(f("lambda_m") * 1e12, 5)} pm</strong> ({sig(f("lambda_m") * 1e10, 4)} Å), moving at {pct(f("beta"), 4)} of the speed of light with {sig(f("ke_ev") / 1000, 4)} keV of kinetic energy.</p>
<h2>What is verified</h2>
<p>The electron-microscope wavelengths at 100, 200, 300 and 1,000 kV are compared with an independent calculation; the thermal-neutron, 100 V and 54 V (Davisson–Germer) values are checked against published figures; and the speed-based and voltage-based relativistic forms are tested to agree to 12 digits.</p>
<p class="cs-note">Limits: this gives the wavelength of a free particle with a definite momentum. It says nothing about diffraction geometry, and a "custom mass" is treated as a point particle.</p>'''
    js = ui.page_js(DB_DRIVER, DB_TYPES, ["particle", "mass_custom", "mode", "speed", "speed_unit", "volts"], '''
    var lam=N(k,'lambda_m'); set('lambda',C.length(lam,5)); note('lambda','= '+C.sig(lam*1e10,5)+' Å = '+C.sig(lam,5)+' m');
    var nr=N(k,'lambda_nonrel'); set('nonrel',C.length(nr,5)); note('nonrel',Math.abs(nr/lam-1)<1e-6?'the same to 6 digits (low speed)':C.pct(nr/lam-1,3)+' '+(nr>lam?'too long':'too short'));
    set('speed',C.sig(N(k,'speed'),6)+' m/s'); note('speed','= '+C.pct(N(k,'beta'),5)+' of the speed of light');
    set('momentum',C.sig(N(k,'momentum'),5)+' kg·m/s'); note('momentum','p = h / λ');
    set('ke',C.sig(N(k,'ke_ev'),5)+' eV'); note('ke','= '+C.sig(N(k,'ke_j'),5)+' J');
    var vb=N(k,'vs_bohr'); set('scale',C.sig(vb,4)+' × the Bohr radius'); note('scale',vb<1?'smaller than a hydrogen atom':(vb>1e8?'much larger than an atom - but see: this is a macroscopic object':'about '+C.sig(vb,2)+' atoms across'));''',
        prep="if(v.particle!=='custom')v.mass_custom=1; if(v.mode==='speed'){if(!(v.volts>0))v.volts=1;} else {if(!(v.speed>0)){v.speed=1;}}\n")
    return dict(slug="de-broglie-wavelength-calculator", group="quantum mechanics", icon="\U0001f30a", short="de Broglie wavelength",
        title="de Broglie Wavelength Calculator — Electrons, Neutrons & More", kicker="Quantum mechanics",
        h1="de Broglie Wavelength Calculator",
        description="Free de Broglie wavelength calculator with relativistic momentum: electrons at any voltage (electron microscopes), neutrons, protons, even a baseball. Computed live.",
        lead="Every particle is also a wave. Choose a particle and a speed or accelerating voltage to get its de Broglie wavelength — with relativistic momentum, so electron-microscope voltages come out right.",
        packages=["qmech", "relativity", "physconst", "physmath"], faq=faq, main=main + body, js=js)

def ex_v(*a): return 0

# ============================================================================= particle in a box
BX_DRIVER = '''import "qmech" as qm
import "physconst" as k
import "physmath" as m
fn kv(name, x) { print(name + "=" + m.sci(x, 11)) }
let mass = {"electron": k.m_e, "proton": k.m_p, "neutron": k.m_n, "custom": ${mass_custom}}[${particle}]
let L = ${length} * ${len_unit}
let n = ${n}
if mass <= 0 or L <= 0 { throw {"type": "LarzValueError", "message": "Enter a positive mass and box length."} }
if ${x1} < 0 or ${x2} > 1 or ${x1} >= ${x2} { throw {"type": "LarzValueError", "message": "Choose a region with 0 <= start < end <= 1 (fractions of the box)."} }
kv("L", L)
kv("e_n_ev", qm.box_energy_ev(n, mass, L))
kv("e_n_j", qm.box_energy_j(n, mass, L))
if n > 1 {
  let e2 = qm.box_energy_j(n, mass, L) - qm.box_energy_j(n - 1, mass, L)
  kv("photon_m", k.h * k.c / e2)
  kv("photon_ev", e2 / k.eV)
}
kv("p_region", qm.box_probability(n, L, ${x1} * L, ${x2} * L))
kv("p_classical", ${x2} - ${x1})
for i in range(1, 9) { print("row|levels|" + str(i) + "|" + m.sci(qm.box_energy_ev(i, mass, L), 9) + "|" + m.sci(qm.box_energy_j(i, mass, L), 9)) }
for j in range(0, 101) { print("row|density|" + m.fixed(j / 100.0, 2) + "|" + m.fixed(qm.box_density(n, L, j / 100.0 * L) * L, 6)) }
'''
BX_TYPES = {"particle": "str", "mass_custom": "num", "length": "num", "len_unit": "num", "n": "int", "x1": "num", "x2": "num"}

def box():
    ex, exr = _run(BX_DRIVER, BX_TYPES, {"particle": "electron", "mass_custom": 1, "length": 1, "len_unit": 1e-9, "n": 1, "x1": 0.25, "x2": 0.75})
    ex3, _ = _run(BX_DRIVER, BX_TYPES, {"particle": "electron", "mass_custom": 1, "length": 1, "len_unit": 1e-9, "n": 3, "x1": 0.25, "x2": 0.75})
    exA, _ = _run(BX_DRIVER, BX_TYPES, {"particle": "electron", "mass_custom": 1, "length": 1, "len_unit": 1e-10, "n": 2, "x1": 0.25, "x2": 0.75})
    exP, _ = _run(BX_DRIVER, BX_TYPES, {"particle": "proton", "mass_custom": 1, "length": 10, "len_unit": 1e-15, "n": 2, "x1": 0.25, "x2": 0.75})
    f = lambda k_: float(ex[k_])
    lv = exr["levels"]
    faq = [
        ("What is the particle-in-a-box model?", "It is the simplest exactly solvable quantum system: a particle confined between two impenetrable walls a distance L apart. The Schrödinger equation gives standing-wave solutions and energies E<sub>n</sub> = n²h²/(8mL²), showing in the plainest possible way why confinement produces discrete energy levels."),
        ("Why can't the particle have zero energy?", "Confining a particle to a region forces its momentum to be uncertain (Heisenberg's uncertainty principle), so it can never be perfectly at rest. The lowest allowed energy, E<sub>1</sub>, is the zero-point energy. For an electron in a 1 nm box it is " + sig(f("e_n_ev"), 4) + " eV."),
        ("Why does the energy grow as n²?", "Higher states have more half-wavelengths fitting into the box, hence shorter wavelength and larger momentum. Energy goes as momentum squared, and the wavelength is 2L/n, so E is proportional to n². The gaps between levels therefore widen: E<sub>n+1</sub> − E<sub>n</sub> = (2n+1)E<sub>1</sub>."),
        ("How does this model appear in real technology?", "Quantum wells, wires and dots in semiconductors are box-like traps for electrons; their sizes set the colour of quantum-dot light. Conjugated dye molecules are often modelled as a one-dimensional box for their pi electrons, and nuclear physics uses a similar picture for nucleons in a nucleus."),
        ("What is the classical limit?", "As n grows, the density |ψ|² oscillates so fast that any region of finite width holds the classical fraction of probability. A quick check: on this page raise n to 50 and the probability in the middle half approaches 50%."),
    ]
    presets = [("Electron in 1 nm", {"particle": "electron", "length": 1, "len_unit": "0.000000001"}), ("Electron in an atom-sized 1 Å box", {"particle": "electron", "length": 1, "len_unit": "0.0000000001"}),
               ("Proton in a nucleus (10 fm)", {"particle": "proton", "length": 10, "len_unit": "0.000000000000001"}), ("Electron in a 10 nm quantum dot", {"particle": "electron", "length": 10, "len_unit": "0.000000001"})]
    form = ui.panel("Set the box", '<div class="cs-grid">' +
        ui.select("particle", "Particle", [("electron", "electron"), ("proton", "proton"), ("neutron", "neutron"), ("custom", "custom mass…")], "electron") +
        ui.field("mass_custom", "Custom mass (kg)", "1", step="any", min="0") + ui.field("length", "Box length", "1", step="any", min="0") +
        ui.select("len_unit", "Length unit", [("0.000000001", "nanometres"), ("0.0000000001", "Ångströms"), ("0.000000000001", "picometres"), ("0.000000000000001", "femtometres"), ("0.000001", "micrometres")], "0.000000001") +
        ui.field("n", "Quantum number n", "1", step="1", min="1", max="200") + ui.field("x1", "Region starts at (fraction of L)", "0.25", step="any", min="0", max="1") +
        ui.field("x2", "Region ends at (fraction of L)", "0.75", step="any", min="0", max="1") + "</div>" + ui.chips([(t, p) for t, p in presets]), "Calculate")
    main = (form + ui.results([("en", "Energy of level n", True), ("photon", "Photon emitted for n → n−1", False), ("prob", "Probability of finding it in the region", True), ("classical", "Classical (uniform) expectation", False)]) +
            '<div class="cs-panel"><h2>Probability density for level n</h2><div id="plot"></div></div><div class="cs-panel"><h2>The first eight levels</h2><div id="levels"></div></div>' + ui.CODE)
    body = f'''<h2>Energy levels of a particle in a box</h2>
<p>Put a particle of mass <i>m</i> in a one-dimensional box of length <i>L</i> with hard walls. Its allowed wavefunctions are sine waves that vanish at both walls, ψ<sub>n</sub>(x) = √(2/L) sin(nπx/L), with energies</p>
<div class="cs-formula">E<sub>n</sub> = n² h² / (8 m L²)&nbsp;&nbsp;&nbsp;·&nbsp;&nbsp;&nbsp;|ψ<sub>n</sub>(x)|² = (2/L) sin²(nπx/L)</div>
<p>The probability of finding the particle between <i>x</i><sub>1</sub> and <i>x</i><sub>2</sub> is the exact integral of |ψ|², which this page evaluates in closed form — no numerical integration.</p>
<h2>Numbers to remember</h2>
<p>An electron in a box 1 nm wide has a ground-state energy of {sig(f("e_n_ev"), 4)} eV; shrink the box to an atom-sized 1 Å and it jumps a hundredfold to {sig(float(exA["e_n_ev"]) / 4, 4)} eV, because E scales as 1/L². In the third level the electron of the 1 nm box has {sig(float(ex3["e_n_ev"]), 4)} eV, exactly 9 times the ground state. A proton in a 10 fm nucleus-sized box has E<sub>1</sub> = {sig(float(exP["e_n_ev"]) / 4 / 1e6, 4)} MeV — the scale of nuclear binding energies. (The 1 nm and 1 \u00c5 values and the n\u00b2 scaling are asserted in the library's test suite.)</p>
<p>The ground state puts {pct(f("p_region"), 4)} of the probability in the middle half of the box, compared with 50% for a classical particle bouncing uniformly between the walls: a quantum particle in its lowest state prefers the centre.</p>
<h2>What is verified</h2>
<p>Energies are checked against the textbook values (0.376 eV for an electron in 1 nm, 37.6 eV in 1 Å), the scaling E<sub>n</sub> = n²E<sub>1</sub>, normalisation (total probability exactly 1 for every n), the exact ground-state result 1/3 + √3/(2π) = 0.609 for the middle third, and the nodes of the higher states.</p>
<p class="cs-note">Limits: an infinitely deep, one-dimensional, non-relativistic box. Real wells are finite (the particle leaks into the walls — see the <a href="/quantum-tunneling-calculator/">tunneling calculator</a>) and real particles move in three dimensions, where the energies add: E = (n<sub>x</sub>² + n<sub>y</sub>² + n<sub>z</sub>²)h²/(8mL²) for a cubic box.</p>'''
    js = ui.page_js(BX_DRIVER, BX_TYPES, ["particle", "mass_custom", "length", "len_unit", "n", "x1", "x2"], '''
    set('en',C.sig(N(k,'e_n_ev'),5)+' eV'); note('en','= '+C.sig(N(k,'e_n_j'),5)+' J, level n = '+v.n);
    if(k.photon_m){set('photon',C.length(N(k,'photon_m'),5)); note('photon','photon energy '+C.sig(N(k,'photon_ev'),5)+' eV');}else{set('photon','—'); note('photon','level 1 is the lowest: nothing to drop to');}
    set('prob',C.pct(N(k,'p_region'),5)); note('prob','between '+C.sig(v.x1,3)+' L and '+C.sig(v.x2,3)+' L');
    set('classical',C.pct(N(k,'p_classical'),5)); note('classical','a classical particle is equally likely anywhere');
    var pts=(rows.density||[]).map(function(r){return [Number(r[0]),Number(r[1])];});
    C.plot($('plot'),[{name:'quantum, n = '+v.n,pts:pts},{name:'classical (uniform)',pts:[[0,1],[1,1]],color:'#f59e0b',dash:'6 5'}],{xlabel:'position x / L',ylabel:'L · |ψ|² (1 = classical)',ymin:0,label:'Probability density of the particle in a box'});
    var h='<div class="cs-tbl"><table class="lz"><thead><tr><th>n</th><th>Energy (eV)</th><th>Energy (J)</th><th>E / E₁</th></tr></thead><tbody>',e1=Number((rows.levels||[[0,1]])[0][1]);
    (rows.levels||[]).forEach(function(r){h+='<tr><td>'+r[0]+'</td><td>'+C.sig(Number(r[1]),5)+'</td><td>'+C.sig(Number(r[2]),5)+'</td><td>'+C.sig(Number(r[1])/e1,4)+'</td></tr>';});
    $('levels').innerHTML=h+'</tbody></table></div>';''',
        prep="if(v.particle!=='custom')v.mass_custom=1;\n")
    return dict(slug="particle-in-a-box-calculator", group="quantum mechanics", icon="\U0001f4e6", short="Particle in a box",
        title="Particle in a Box Calculator — Energy Levels & Probability", kicker="Quantum mechanics",
        h1="Particle in a Box Calculator",
        description="Free particle-in-a-box calculator: energy levels Eₙ = n²h²/8mL², photon wavelengths, probability density plot and exact region probabilities. Verified physics.",
        lead="Confine an electron, proton or any mass between two walls and see its quantised energy levels, the probability density of any state and the exact probability of finding it in any region.",
        packages=["qmech", "physconst", "physmath"], faq=faq, main=main + body, js=js)

# ============================================================================= tunneling
TN_DRIVER = '''import "qmech" as qm
import "physconst" as k
import "physmath" as m
fn kv(name, x) { print(name + "=" + m.sci(x, 11)) }
let mass = {"electron": k.m_e, "proton": k.m_p, "neutron": k.m_n}[${particle}]
let es = {"ev": k.eV, "kev": 1000.0 * k.eV, "mev": 1000000.0 * k.eV}[${eunit}]
let e = ${energy} * es
let v0 = ${barrier} * es
let w = ${width} * ${wunit}
if e <= 0 or v0 <= 0 or w <= 0 { throw {"type": "LarzValueError", "message": "Energy, barrier height and width must all be positive."} }
let t = qm.tunneling_probability(e, v0, w, mass)
kv("t", t)
kv("above", e > v0 ? 1.0 : 0.0)
if e < v0 {
  let kap = qm.tunneling_kappa(e, v0, mass)
  kv("kappa", kap)
  kv("depth", 1.0 / kap)
  kv("wkb", 16.0 * e * (v0 - e) / (v0 * v0) * m.exp(-2.0 * kap * w))
  kv("per_width", m.exp(-2.0 * kap * 0.0000000001))
}
for i in range(0, 61) {
  let wi = w * 2.0 * i / 60.0 + 0.0000000000000000000000000000001
  let ti = qm.tunneling_probability(e, v0, wi, mass)
  print("row|curve|" + m.sig(wi / w, 6) + "|" + m.fixed(ti > 0.0000000000000000000000000000000000001 ? m.log10(ti) : -37.0, 5))
}
'''
TN_TYPES = {"particle": "str", "energy": "num", "barrier": "num", "eunit": "str", "width": "num", "wunit": "num"}

def tunneling():
    ex, _ = _run(TN_DRIVER, TN_TYPES, {"particle": "electron", "energy": 1, "barrier": 2, "eunit": "ev", "width": 0.2, "wunit": 1e-9})
    exS, _ = _run(TN_DRIVER, TN_TYPES, {"particle": "electron", "energy": 1, "barrier": 5, "eunit": "ev", "width": 0.5, "wunit": 1e-9})
    exP, _ = _run(TN_DRIVER, TN_TYPES, {"particle": "proton", "energy": 1, "barrier": 2, "eunit": "ev", "width": 0.2, "wunit": 1e-9})
    f = lambda k_: float(ex[k_])
    faq = [
        ("What is quantum tunneling?", "A quantum particle can pass through a barrier that a classical particle of the same energy could never cross. Its wavefunction does not drop to zero inside the barrier; it decays exponentially, and if the barrier is thin enough a little of it emerges on the other side. The transmission probability is what this calculator computes."),
        ("Why does the electron tunnel so much more easily than the proton?", f"Tunneling depends exponentially on the particle's mass through κ = √(2m(V₀−E))/ħ. For the same energy and barrier (1 eV electron, 2 eV barrier, 0.2 nm) the electron transmits {pct(f('t'), 3)}, while a proton would transmit only {sig(float(exP['t']), 3)} — a factor of about 10<sup>{int(round(__import__('math').log10(f('t') / float(exP['t']))))}</sup> smaller."),
        ("Where does tunneling matter in real life?", "It powers the Sun (protons tunnel through their mutual electric repulsion to fuse), causes alpha decay, makes flash memory work, sets the leakage current of the smallest transistors, and lets scanning tunneling microscopes image individual atoms by measuring a current that changes by roughly a factor of 10 for every ångström of gap."),
        ("Is the particle really 'inside' the barrier, and does it take time?", "Between the walls the particle has no definite position; only the probability of finding it there is meaningful, and it falls off with depth as e<sup>−κ x</sup>. How long tunneling takes is a subtle, still-debated question; what is settled is that no signal travels faster than light."),
        ("What does E > V₀ mean here?", "If the particle's energy exceeds the barrier height there is no tunneling, but a quantum particle can still be reflected, and the transmission oscillates with the barrier width, reaching exactly 100% at special widths — the resonances a classical particle never shows."),
    ]
    presets = [("Electron 1 eV vs 2 eV, 0.2 nm", {"particle": "electron", "energy": 1, "barrier": 2, "eunit": "ev", "width": 0.2, "wunit": "0.000000001"}),
               ("STM-like: electron, 4 eV above, 0.5 nm gap", {"particle": "electron", "energy": 1, "barrier": 5, "eunit": "ev", "width": 0.5, "wunit": "0.000000001"}),
               ("Same barrier, a proton", {"particle": "proton", "energy": 1, "barrier": 2, "eunit": "ev", "width": 0.2, "wunit": "0.000000001"}),
               ("Thin transistor oxide: electron 1 eV vs 3 eV, 1 nm", {"particle": "electron", "energy": 1, "barrier": 3, "eunit": "ev", "width": 1, "wunit": "0.000000001"}),
               ("Nuclear scale: proton 3 MeV vs 10 MeV, 10 fm", {"particle": "proton", "energy": 3, "barrier": 10, "eunit": "mev", "width": 10, "wunit": "0.000000000000001"})]
    form = ui.panel("Set the particle and the barrier", '<div class="cs-grid">' +
        ui.select("particle", "Particle", [("electron", "electron"), ("proton", "proton"), ("neutron", "neutron")], "electron") +
        ui.field("energy", "Particle energy", "1", step="any", min="0") + ui.field("barrier", "Barrier height", "2", step="any", min="0") +
        ui.select("eunit", "Energy unit", [("ev", "eV"), ("kev", "keV"), ("mev", "MeV")], "ev") + ui.field("width", "Barrier width", "0.2", step="any", min="0") +
        ui.select("wunit", "Width unit", [("0.000000001", "nanometres"), ("0.0000000001", "Ångströms"), ("0.000000000001", "picometres"), ("0.000000000000001", "femtometres")], "0.000000001") + "</div>" + ui.chips(presets), "Calculate")
    main = (form + ui.results([("t", "Transmission probability", True), ("pct", "As a percentage", False), ("depth", "Penetration depth 1/κ", False), ("wkb", "Thick-barrier estimate", False)]) +
            '<div class="cs-panel"><h2>How transmission falls as the barrier gets wider</h2><div id="plot"></div><p class="cs-note">Vertical axis: log₁₀ of the transmission probability, so a drop of 1 means ten times less. Horizontal axis: barrier width as a multiple of the width you entered; the dot marks your barrier.</p></div>' + ui.CODE)
    body = f'''<h2>Transmission through a rectangular barrier</h2>
<p>A particle of energy <i>E</i> meets a rectangular barrier of height <i>V</i><sub>0</sub> &gt; <i>E</i> and width <i>a</i>. Solving the Schrödinger equation on both sides and inside the barrier and matching the wavefunction at the edges gives the exact transmission probability</p>
<div class="cs-formula">T = 1 / (1 + V<sub>0</sub>² sinh²(κa) / (4E(V<sub>0</sub>−E)))&nbsp;&nbsp;&nbsp;with&nbsp;&nbsp;&nbsp;κ = √(2m(V<sub>0</sub>−E)) / ħ</div>
<p>For a thick barrier (κa ≫ 1) this collapses to T ≈ 16E(V<sub>0</sub>−E)/V<sub>0</sub>² · e<sup>−2κa</sup>, the exponential law behind every tunneling device. When E &gt; V<sub>0</sub> the sinh becomes a sine and T oscillates between values below 1 and exactly 1.</p>
<h2>Worked example, computed above</h2>
<p>A 1 eV electron meets a 2 eV barrier 0.2 nm thick (about one atomic layer). The decay constant is κ = {sig(f("kappa") / 1e10, 4)} Å⁻¹, so the wave reaches only {sig(f("depth") * 1e10, 3)} Å into the barrier before falling by a factor of e — and yet <strong>{pct(f("t"), 4)}</strong> of the electrons get through. For a bigger barrier (5 eV, 0.5 nm) the transmission is {sig(float(exS["t"]), 3)}, and the thick-barrier estimate {sig(float(exS["wkb"]), 3)} already agrees to {pct(abs(float(exS["wkb"]) / float(exS["t"]) - 1), 2)}.</p>
<h2>What is verified</h2>
<p>The transmission is compared with an independent Python evaluation at five parameter sets to 14 significant digits; it is checked to be continuous across E = V<sub>0</sub>, to fall monotonically with width, to reach exactly 100% at the above-barrier resonance ka = π, and to match the thick-barrier formula. Very thick barriers use the asymptotic form so nothing overflows.</p>
<p class="cs-note">Limits: a one-dimensional rectangular barrier and a single non-relativistic particle. Real barriers have smooth shapes (use the WKB integral over the actual profile) and real tunneling in solids involves many electrons and the band structure.</p>'''
    js = ui.page_js(TN_DRIVER, TN_TYPES, ["particle", "energy", "barrier", "eunit", "width", "wunit"], '''
    var T=N(k,'t'); set('t',T>=0.001?C.sig(T,5):C.sig(T,4)); note('t',N(k,'above')?'the particle has more energy than the barrier: no tunneling, but reflection is still possible':'probability that one particle gets through');
    set('pct',C.pct(T,4)); note('pct',T<1e-9?'about 1 in '+C.sig(1/T,3):'');
    if(k.depth){set('depth',C.length(N(k,'depth'),4)); note('depth','the wave falls to 1/e of its size this far into the barrier');set('wkb',C.sig(N(k,'wkb'),4)); note('wkb','16E(V₀−E)/V₀² · e^(−2κa), the large-width form');}
    else{set('depth','—'); note('depth','no decay: E > V₀');set('wkb','—'); note('wkb','applies only when E < V₀');}
    var pts=(rows.curve||[]).map(function(r){return [Number(r[0]),Number(r[1])];});
    C.plot($('plot'),[{name:'log₁₀ T',pts:pts,dot:[1,Math.log10(Math.max(T,1e-37))]}],{xlabel:'barrier width / your width',ylabel:'log₁₀(transmission)',label:'Transmission versus barrier width'});''')
    return dict(slug="quantum-tunneling-calculator", group="quantum mechanics", icon="\U0001f6aa", short="Quantum tunneling",
        title="Quantum Tunneling Calculator — Barrier Transmission Probability", kicker="Quantum mechanics",
        h1="Quantum Tunneling Calculator",
        description="Free quantum tunneling calculator: exact transmission probability of an electron, proton or neutron through a rectangular barrier, with a width curve. Verified physics.",
        lead="How likely is a particle to pass straight through a barrier it does not have the energy to climb? Set the particle, energy, barrier height and width, and get the exact quantum transmission probability.",
        packages=["qmech", "physconst", "physmath"], faq=faq, main=main + body, js=js)

def pages(): return [hydrogen(), de_broglie(), box(), tunneling()]
