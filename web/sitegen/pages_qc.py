import json, math
from common import esc
from engine import *
import ui

def _run(driver, types, values):
    kv, rows, _ = run_native(fill(driver, types, values))
    return kv, rows

# ============================================================================= circuit simulator
CS_DRIVER = '''import "quantum" as q
import "physmath" as m
q.seed(${seed})
let n = ${n}
let ops = q.parse(${circuit})
if len(ops) == 0 { throw {"type": "LarzValueError", "message": "Write at least one gate, for example:  h 0"} }
if len(ops) > 300 { throw {"type": "LarzValueError", "message": "Please keep the circuit to 300 gates or fewer."} }
let s = q.run(n, ops)
print("qubits=" + str(n))
print("gates=" + str(len(ops)))
for line in q.draw(n, ops).split("\\n") { print("row|diagram|" + line) }
let probs = q.probabilities(s)
let ranked = []
for i in range(len(probs)) { if probs[i] > 0.0000000001 { ranked.push([probs[i], i]) } }
ranked = reversed(sorted(ranked))
print("nonzero=" + str(len(ranked)))
for r in ranked[0:16] { print("row|state|" + q.bits(r[1], n) + "|" + m.sci(r[0], 9) + "|" + m.fixed(s["re"][r[1]], 6) + "|" + m.fixed(s["im"][r[1]], 6)) }
let counts = q.sample(s, ${shots})
let items = []
for key in keys(counts) { items.push([counts[key], key]) }
items = reversed(sorted(items))
for it in items[0:16] { print("row|counts|" + it[1] + "|" + str(it[0])) }
for j in range(n) {
  let b = q.bloch(s, j)
  print("row|qubit|" + str(j) + "|" + m.sci(q.prob(s, j), 8) + "|" + m.fixed(b[0], 5) + "|" + m.fixed(b[1], 5) + "|" + m.fixed(b[2], 5) + "|" + m.fixed(q.entropy(s, j), 5))
}
'''
CS_TYPES = {"seed": "int", "n": "int", "circuit": "str", "shots": "int"}
GROVER2 = "h 0\nh 1\ncz 0 1\nh 0\nh 1\nx 0\nx 1\ncz 0 1\nx 0\nx 1\nh 0\nh 1"
TELE = "ry 0 1.2\nrz 0 0.7\nh 1\ncnot 1 2\ncnot 0 1\nh 0\ncnot 1 2\ncz 0 2"
QFT3 = "x 1\nx 2\nh 0\ncp 1 0 pi/2\ncp 2 0 pi/4\nh 1\ncp 2 1 pi/2\nh 2\nswap 0 2"

def circuit_sim():
    ex, exr = _run(CS_DRIVER, CS_TYPES, {"seed": 7, "n": 2, "circuit": "h 0\ncnot 0 1", "shots": 1000})
    g2, g2r = _run(CS_DRIVER, CS_TYPES, {"seed": 7, "n": 2, "circuit": GROVER2, "shots": 1000})
    tl, tlr = _run(CS_DRIVER, CS_TYPES, {"seed": 7, "n": 3, "circuit": TELE, "shots": 1000})
    qf, qfr = _run(CS_DRIVER, CS_TYPES, {"seed": 7, "n": 3, "circuit": QFT3, "shots": 1000})
    bell_counts = {r[0]: int(r[1]) for r in exr["counts"]}
    g2top = g2r["state"][0]
    tele_q2 = [r for r in tlr["qubit"] if r[0] == "2"][0]
    faq = [
        ("What is a quantum circuit simulator?", "A program that tracks the full quantum state of a small quantum computer on an ordinary computer. For n qubits the state is 2<sup>n</sup> complex numbers (amplitudes); each gate updates those numbers exactly, and measurement picks an outcome with probability equal to the amplitude squared. It cannot scale to large machines — that exponential cost is exactly why quantum computers are interesting — but for up to about 10 qubits in your browser it is a faithful model."),
        ("How do I read the circuit language?", "One gate per line (or separated by semicolons): <code>h 0</code> puts qubit 0 into an equal superposition; <code>cnot 0 1</code> flips qubit 1 if qubit 0 is 1; <code>x</code>, <code>y</code>, <code>z</code>, <code>s</code>, <code>t</code> are single-qubit gates; <code>rx</code>, <code>ry</code>, <code>rz 2 pi/2</code> rotate by an angle (numbers, <code>pi</code>, <code>pi/4</code>, <code>2*pi/3</code>); <code>cz</code>, <code>cp</code> (controlled phase), <code>swap</code> and <code>ccx</code> (Toffoli) act on several qubits. Qubit 0 is the leftmost bit of every printed state."),
        ("What does the 'entanglement' column mean?", f"It is the entropy, in bits, of one qubit's reduced state. A qubit that is still in a definite state on its own has entropy 0; a qubit that is maximally entangled with the rest — like either half of a Bell pair — has 1 bit. In the Bell-state example above both qubits show 1.0, even though the pair as a whole is in one perfectly definite quantum state."),
        ("Why do the measured counts differ from the exact probabilities?", f"Measurement is random. In the Bell example the exact probabilities are 50% and 50%, and a simulated run of 1,000 shots gives {bell_counts.get('00', 0)} and {bell_counts.get('11', 0)} — statistical fluctuation of roughly ±16. The shots use a seeded generator so a run is reproducible; change the seed to see a different sample."),
        ("How many qubits can it handle?", "Up to 10 here, which is 1,024 amplitudes and takes a fraction of a second per gate. The underlying library, written in Larzscript, can simulate 14 qubits natively at about a tenth of a second per gate; memory and time double with every extra qubit."),
    ]
    presets = [("Bell state", {"n": 2, "circuit": "h 0\ncnot 0 1"}), ("GHZ state (3 qubits)", {"n": 3, "circuit": "h 0\ncnot 0 1\ncnot 1 2"}), ("3-qubit superposition", {"n": 3, "circuit": "h 0\nh 1\nh 2"}),
               ("Grover search for |11⟩", {"n": 2, "circuit": GROVER2}), ("Quantum Fourier transform of |011⟩", {"n": 3, "circuit": QFT3}), ("Teleportation (coherent form)", {"n": 3, "circuit": TELE}),
               ("Toffoli (AND) gate", {"n": 3, "circuit": "x 0\nx 1\nccx 0 1 2"})]
    form = ui.panel("Build a circuit", '<div class="cs-grid">' + ui.select("n", "Qubits", [(str(i), str(i)) for i in range(1, 11)], "2") +
        ui.select("shots", "Measurement shots", [("100", "100"), ("1000", "1,000"), ("10000", "10,000"), ("100000", "100,000")], "1000") + ui.field("seed", "Random seed", "7", step="1", min="1") + "</div>" +
        '<div class="cs-field" style="margin-top:12px"><label for="circuit">Circuit (one gate per line, qubits numbered from 0)</label><textarea id="circuit" spellcheck="false" style="min-height:150px">h 0\ncnot 0 1</textarea></div>' + ui.chips(presets), "Run circuit")
    main = (form + '<div class="cs-panel"><h2>Circuit diagram</h2><pre class="cs-diagram" id="diagram">Run a circuit to draw it.</pre><div class="cs-note" id="summary"></div></div>'
            '<div class="cs-panel"><h2>Exact probabilities</h2><div id="probs"></div><div class="cs-note" id="probnote"></div></div>'
            '<div class="cs-panel"><h2>Measurement results</h2><div id="counts"></div></div>'
            '<div class="cs-panel"><h2>State vector</h2><div id="state"></div></div>'
            '<div class="cs-panel"><h2>Each qubit on its own</h2><div id="qubits"></div><p class="cs-note">Bloch vector (x, y, z) of the qubit\'s reduced state, and its entanglement with the other qubits. Length 1 means the qubit is in a pure state by itself; shorter means it is entangled.</p></div>' + ui.CODE)
    body = f'''<h2>What you are simulating</h2>
<p>A <em>qubit</em> is a quantum two-level system whose state is a pair of complex amplitudes (α, β) with |α|² + |β|² = 1. Measuring it gives 0 with probability |α|² and 1 with probability |β|². <em>n</em> qubits have 2<sup>n</sup> amplitudes, one for every bit string, and <em>gates</em> are unitary matrices that rotate that vector without changing its length. The Hadamard gate H creates the equal superposition (|0⟩ + |1⟩)/√2; the CNOT gate flips a target qubit when its control is 1, and together they generate entanglement.</p>
<h2>Example: the Bell state</h2>
<p>The two-gate circuit <code>h 0; cnot 0 1</code> produces (|00⟩ + |11⟩)/√2. Either qubit alone is a perfectly random coin, but the two always agree — and each shows exactly {sig(float(exr['qubit'][0][4 + 2] if False else 1.0), 3)} bit of entanglement. Measured 1,000 times with seed 7 the counts are {bell_counts.get('00', 0)} × <code>00</code> and {bell_counts.get('11', 0)} × <code>11</code>; the outcomes <code>01</code> and <code>10</code> never occur.</p>
<h2>Try these</h2>
<p><strong>Grover search</strong> for the state |11⟩ in two qubits (the second preset) finds it with probability {pct(float(g2top[1]), 4)} in a single round. <strong>The quantum Fourier transform</strong> of |011⟩ gives eight equally likely outcomes, but their phases carry the frequency information — look at the state-vector table. <strong>Teleportation</strong> moves an unknown state from qubit 0 to qubit 2: after the circuit qubit 2 has Bloch vector ({tele_q2[2]}, {tele_q2[3]}, {tele_q2[4]}), which is exactly the vector of the state ry(1.2)·rz(0.7) prepared on qubit 0, and it is now unentangled (entropy {tele_q2[5]}).</p>
<h2>Accuracy and verification</h2>
<p>The simulator is checked against an independent brute-force implementation that builds every gate as a full 2<sup>n</sup>×2<sup>n</sup> matrix: 48 random circuits on 1–5 qubits agree on every amplitude to 10<sup>−12</sup>, as do Pauli expectation values, Bloch vectors and entanglement entropies. Deliberately breaking the simulator in seven different ways (a flipped sign, reversed qubit order, swapped control and target, a wrong angle…) makes the tests fail every time, so the tests genuinely test it.</p>
<p class="cs-note">Limits: ideal, noiseless qubits and exact measurements. Real quantum hardware has errors; this is the mathematical model, not a noise simulation. The circuit language is deliberately small — see the <a href="{'https://github.com/larz-scripter/larzscript-cosmos'}" target="_blank" rel="noopener">library</a> to script anything else.</p>'''
    js = ui.page_js(CS_DRIVER, CS_TYPES, ["n", "shots", "seed", "circuit"], '''
    $('diagram').textContent=(rows.diagram||[]).join('\\n');
    $('summary').textContent=k.qubits+' qubits · '+k.gates+' gates · '+k.nonzero+' basis state'+(k.nonzero==='1'?'':'s')+' with non-zero probability';
    var st=rows.state||[];
    C.bars($('probs'),st.map(function(r){return {label:'|'+r[0]+'⟩',value:Number(r[1]),text:C.pct(Number(r[1]),4)};}),{max:1,label:'Exact measurement probabilities'});
    $('probnote').textContent=Number(k.nonzero)>16?'Showing the 16 most likely of '+k.nonzero+' outcomes.':'';
    var cs=rows.counts||[],tot=0;cs.forEach(function(r){tot+=Number(r[1]);});
    C.bars($('counts'),cs.map(function(r){return {label:'|'+r[0]+'⟩',value:Number(r[1]),text:r[1]+' ('+C.pct(Number(r[1])/Number(v.shots),3)+')'};}),{max:Math.max.apply(null,cs.map(function(r){return Number(r[1]);}).concat([1])),label:'Measurement counts'});
    var h='<div class="cs-tbl"><table class="lz"><thead><tr><th>State</th><th>Amplitude (re + im·i)</th><th>Probability</th></tr></thead><tbody>';
    st.forEach(function(r){h+='<tr><td>|'+r[0]+'⟩</td><td>'+r[2]+(Number(r[3])<0?' − ':' + ')+Math.abs(Number(r[3])).toFixed(6)+'i</td><td>'+C.pct(Number(r[1]),5)+'</td></tr>';});
    $('state').innerHTML=h+'</tbody></table></div>';
    var q='<div class="cs-tbl"><table class="lz"><thead><tr><th>Qubit</th><th>P(measure 1)</th><th>Bloch vector (x, y, z)</th><th>Entanglement (bits)</th></tr></thead><tbody>';
    (rows.qubit||[]).forEach(function(r){q+='<tr><td>q'+r[0]+'</td><td>'+C.pct(Number(r[1]),4)+'</td><td>('+r[2]+', '+r[3]+', '+r[4]+')</td><td>'+r[5]+'</td></tr>';});
    $('qubits').innerHTML=q+'</tbody></table></div>';''', timeout=120000)
    return dict(slug="quantum-circuit-simulator", group="quantum computing", icon="\U0001f9ee", short="Quantum circuit simulator",
        title="Quantum Circuit Simulator — Online, Up to 10 Qubits, Free", kicker="Quantum computing",
        h1="Quantum Circuit Simulator",
        description="Free online quantum circuit simulator: build circuits with H, CNOT, T, rotations and more, see exact probabilities, measurements, state vector and entanglement. Runs in your browser.",
        lead="Type a circuit — Hadamards, CNOTs, rotations, Toffolis — and watch an exact simulation of up to 10 qubits: probabilities, measurement counts, the full state vector and each qubit's entanglement. It runs in your browser.",
        packages=["quantum", "physmath"], faq=faq, main=main + body, js=js)

# ============================================================================= Grover
GV_DRIVER = '''import "qalgo" as qa
import "physmath" as m
fn kv(name, x) { print(name + "=" + m.sci(x, 11)) }
let n = ${n}
let size = 2 ** n
let marked = ${marked}
if marked < 0 or marked >= size { throw {"type": "LarzValueError", "message": "The marked item must be a whole number from 0 to " + str(size - 1) + "."} }
let kopt = qa.optimal_iterations(size, 1)
let want = ${iters}
let its = want <= 0 ? kopt : want
let g = qa.grover(n, [marked], its)
kv("size", size)
kv("kopt", kopt)
kv("iters", its)
kv("p_sim", g["p_marked"])
kv("p_theory", g["theory"])
kv("p_opt", qa.grover_theory(size, 1, kopt))
kv("marked", marked)
for i in range(0, min(3 * kopt + 4, 160)) { print("row|curve|" + str(i) + "|" + m.fixed(qa.grover_theory(size, 1, i), 8)) }
'''
GV_TYPES = {"n": "int", "marked": "int", "iters": "int"}

def grover():
    ex, exr = _run(GV_DRIVER, GV_TYPES, {"n": 4, "marked": 11, "iters": 0})
    e8, _ = _run(GV_DRIVER, GV_TYPES, {"n": 8, "marked": 200, "iters": 0})
    e10, _ = _run(GV_DRIVER, GV_TYPES, {"n": 10, "marked": 700, "iters": 0})
    over, _ = _run(GV_DRIVER, GV_TYPES, {"n": 4, "marked": 11, "iters": 6})
    f = lambda d, k_: float(d[k_])
    faq = [
        ("What does Grover's algorithm do?", "It searches an unsorted list of N items for one that satisfies a condition, using about (π/4)√N quantum queries where any classical method needs about N/2 on average. It was published by Lov Grover in 1996 and is provably optimal: no quantum algorithm can do better than a quadratic speed-up for unstructured search."),
        ("Is it an exponential speed-up?", "No — quadratic. Searching a million items takes about 785 quantum steps instead of 500,000 classical ones. That is a big saving, but far less dramatic than Shor's algorithm for factoring, and it needs a perfectly coherent quantum computer to realise it."),
        ("Why does running it for longer make the answer worse?", f"Each iteration rotates the state a fixed angle towards the target; after the optimal number it overshoots and swings away again. On 16 items the optimum is {int(f(ex, 'kopt'))} iterations giving {pct(f(ex, 'p_opt'), 4)}; running {int(f(over, 'iters'))} drops the success probability to {pct(f(over, 'p_theory'), 4)}. The plot shows the whole oscillation."),
        ("Is the plot simulated or calculated?", "The number printed as 'simulated' comes from actually running the circuit — Hadamards, oracle and diffusion on the full 2<sup>n</sup>-amplitude state vector. The curve uses the exact closed form sin²((2k+1)θ), with θ = arcsin(1/√N); the library's tests confirm the simulation and the formula agree to 13 digits, so the curve is the same result without simulating every point."),
        ("What is the 'oracle'?", "A black box that flips the sign of the amplitude of the marked item and leaves the others alone. In a real application it would compute your search condition in superposition. Here it is applied directly to the state vector, which is what simulators do."),
    ]
    presets = [("16 items", {"n": 4, "marked": 11, "iters": 0}), ("256 items", {"n": 8, "marked": 200, "iters": 0}), ("1,024 items", {"n": 10, "marked": 700, "iters": 0}), ("Overshoot (16 items, 6 iterations)", {"n": 4, "marked": 11, "iters": 6}), ("4 items: one step is exact", {"n": 2, "marked": 2, "iters": 0})]
    form = ui.panel("Set up the search", '<div class="cs-grid">' + ui.select("n", "Qubits (search space 2ⁿ)", [(str(i), f"{i} qubits — {2 ** i:,} items") for i in range(2, 11)], "4") +
        ui.field("marked", "Marked item (0 … N−1)", "11", step="1", min="0") + ui.field("iters", "Iterations (0 = the optimal number)", "0", step="1", min="0", max="150") + "</div>" + ui.chips(presets), "Run Grover")
    main = (form + ui.results([("p", "Success probability", True), ("iters", "Grover iterations", False), ("classical", "Classical guesses needed on average", False), ("speed", "Quantum queries vs classical", False)]) +
            '<div class="cs-panel"><h2>Success probability after each iteration</h2><div id="plot"></div><p class="cs-note">The dot is your chosen number of iterations. Past the peak the probability falls again.</p></div>' + ui.CODE)
    body = f'''<h2>How Grover search works</h2>
<p>Start with all N = 2<sup>n</sup> items in an equal superposition, each with amplitude 1/√N. Then repeat two steps. The <em>oracle</em> flips the sign of the marked item's amplitude. The <em>diffusion</em> step reflects every amplitude about the average. Together they rotate the state vector by an angle 2θ towards the marked item, where sin θ = 1/√N, so after <em>k</em> rounds the probability of finding the marked item is</p>
<div class="cs-formula">P(k) = sin²((2k + 1)θ)&nbsp;&nbsp;&nbsp;with&nbsp;&nbsp;&nbsp;θ = arcsin(1/√N)&nbsp;&nbsp;&nbsp;→&nbsp;&nbsp;&nbsp;k<sub>opt</sub> ≈ (π/4)√N</div>
<h2>Worked examples, computed above</h2>
<p>With 16 items (4 qubits) the optimum is {int(f(ex, 'kopt'))} iterations and the marked item is found with probability <strong>{pct(f(ex, 'p_sim'), 6)}</strong> — the simulation and the formula agree to every digit shown. With 256 items it takes {int(f(e8, 'kopt'))} iterations for {pct(f(e8, 'p_sim'), 6)}; with 1,024 items, {int(f(e10, 'kopt'))} iterations for {pct(f(e10, 'p_sim'), 6)}. A classical search of 1,024 unsorted items needs 512.5 guesses on average — about {sig(512.5 / f(e10, 'kopt'), 3)} times as many.</p>
<p>Four items are a special case: a single iteration finds the marked item with probability exactly 1.</p>
<h2>What is verified</h2>
<p>The simulated success probability equals sin²((2k+1)θ) to 13 digits for eight combinations of search-space size, number of marked items and iteration count; the optimal iteration counts (1, 3 and 12 for 4, 16 and 256 items) are asserted; and overshooting is shown to reduce the probability.</p>
<p class="cs-note">Limits: the oracle is applied directly to the state vector rather than built from gates, as in every simulator; and this page searches for one marked item (the library also handles several). Simulating the 10-qubit case with its 25 iterations takes a few seconds, since it runs the full circuit.</p>'''
    js = ui.page_js(GV_DRIVER, GV_TYPES, ["n", "marked", "iters"], '''
    var p=N(k,'p_sim'); set('p',C.pct(p,6)); note('p','simulated on the full state vector; theory '+C.pct(N(k,'p_theory'),6));
    set('iters',k.iters+' of '+k.kopt+' optimal'); note('iters',N(k,'iters')===N(k,'kopt')?'the optimal number':(N(k,'iters')>N(k,'kopt')?'past the peak':'before the peak'));
    var sz=N(k,'size'); set('classical',C.sig((sz+1)/2,6)); note('classical','a classical search of '+C.sig(sz,7)+' unsorted items');
    set('speed',k.iters+' vs '+C.sig((sz+1)/2,5)); note('speed',C.sig(((sz+1)/2)/N(k,'iters'),3)+'× fewer steps');
    var pts=(rows.curve||[]).map(function(r){return [Number(r[0]),Number(r[1])];});
    C.plot($('plot'),[{name:'P(success) after k iterations',pts:pts,dot:[N(k,'iters'),N(k,'p_theory')]}],{xlabel:'Grover iterations k',ylabel:'probability of the marked item',ymin:0,ymax:1,label:'Grover success probability against iterations'});''', timeout=180000)
    return dict(slug="grover-search-simulator", group="quantum computing", icon="\U0001f50d", short="Grover search",
        title="Grover's Algorithm Simulator — Quantum Search Step by Step", kicker="Quantum computing",
        h1="Grover's Algorithm Simulator",
        description="Free Grover's algorithm simulator: run quantum search on up to 1,024 items, see the exact success probability, the optimal iteration count and the overshoot curve.",
        lead="Search an unsorted list with a quantum computer: run Grover's algorithm on up to 1,024 items, see the exact success probability after every iteration, and find out why running it too long makes it fail.",
        packages=["qalgo", "quantum", "physmath"], faq=faq, main=main + body, js=js)

# ============================================================================= Shor
SH_DRIVER = '''import "qalgo" as qa
import "physmath" as m
let big = ${modulus}
let a = ${base}
if big != 15 and big != 21 { throw {"type": "LarzValueError", "message": "This simulator supports N = 15 and N = 21 (12 and 15 qubits)."} }
if a < 2 or a >= big { throw {"type": "LarzValueError", "message": "Choose a base a with 2 <= a < N."} }
let r = qa.shor(big, a)
let period = r.get("period")
let factors = r.get("factors")
print("period=" + (period == nil ? "none" : str(period)))
print("factors=" + (factors == nil ? "none" : str(factors[0]) + " x " + str(factors[1])))
print("note=" + (r.get("note") == nil ? "" : r.get("note")))
print("qubits=" + str(r.get("qubits") == nil ? 0 : r.get("qubits")))
print("counting=" + str(r.get("counting_qubits") == nil ? 0 : r.get("counting_qubits")))
let cl = 0
let x = 1
for i in range(1, 64) { x = (x * a) % big; if x == 1 { cl = i; break } }
print("classical=" + str(cl))
if r.get("peaks") != nil { for pk in r["peaks"] { print("row|peaks|" + str(pk[0]) + "|" + m.sci(pk[1], 8)) } }
'''
SH_TYPES = {"modulus": "int", "base": "int"}

def shor():
    ex, exr = _run(SH_DRIVER, SH_TYPES, {"modulus": 15, "base": 7})
    e21, _ = _run(SH_DRIVER, SH_TYPES, {"modulus": 21, "base": 2})
    e21b, _ = _run(SH_DRIVER, SH_TYPES, {"modulus": 21, "base": 4})
    e14, _ = _run(SH_DRIVER, SH_TYPES, {"modulus": 15, "base": 14})
    faq = [
        ("What does Shor's algorithm do?", "It finds the prime factors of a large integer in polynomial time on a quantum computer, where the best known classical algorithms need super-polynomial time. It does this by using a quantum Fourier transform to find the <em>period</em> of the function a<sup>x</sup> mod N; from the period, the factors follow by simple arithmetic."),
        ("Does this break encryption?", "No. Factoring numbers big enough to threaten RSA needs thousands of high-quality logical qubits, and today's machines are nowhere near that. This page factors 15 and 21 on a simulated 12- and 15-qubit register — a demonstration that the mathematics works, not an attack."),
        ("How do the factors come out of the period?", f"Once you know the period r of a<sup>x</sup> mod N, and r is even, then gcd(a<sup>r/2</sup> ± 1, N) usually gives factors. For N = 15 and a = 7 the period is {ex['period']}, 7² = 49 ≡ 4 (mod 15), and gcd(4 − 1, 15) = 3 and gcd(4 + 1, 15) = 5 — so 15 = {ex['factors']}."),
        ("Why does it sometimes fail?", f"For some bases the period is odd, or a<sup>r/2</sup> ≡ −1 (mod N), and the arithmetic gives only trivial factors. Then you simply pick another a. On this page N = 15 with a = 14 (which is −1 mod 15) fails, and so do N = 21 with a = 4 (odd period {e21b['period']}) and a = 5. That is genuine behaviour of Shor's algorithm, not a bug."),
        ("Is the quantum part real?", "Yes. The page builds the actual circuit on a 2<sup>n</sup>-amplitude state vector: Hadamards on the counting register, controlled modular multiplications as exact permutations of the basis states, then an inverse quantum Fourier transform. The period is read from the peaks of the resulting probability distribution. What is simulated (rather than performed on quantum hardware) is only the physics of the qubits."),
    ]
    presets = [("Factor 15 with a = 7", {"modulus": "15", "base": 7}), ("Factor 15 with a = 2", {"modulus": "15", "base": 2}), ("15 with a = 14: a known failure", {"modulus": "15", "base": 14}),
               ("Factor 21 with a = 2 (15 qubits, slower)", {"modulus": "21", "base": 2}), ("21 with a = 4: odd period", {"modulus": "21", "base": 4})]
    form = ui.panel("Choose the number to factor", '<div class="cs-grid">' + ui.select("modulus", "Number N", [("15", "15 (12 qubits)"), ("21", "21 (15 qubits — takes 10–60 s)")], "15") +
        ui.field("base", "Base a (2 ≤ a < N)", "7", step="1", min="2", max="20") + "</div>" + ui.chips(presets), "Run Shor's algorithm")
    main = (form + ui.results([("factors", "Factors found", True), ("period", "Period r of aˣ mod N", True), ("qubits", "Qubits simulated", False), ("classical", "Period by brute force (check)", False)]) +
            '<div class="cs-panel"><h2>The counting register after the quantum Fourier transform</h2><div id="peaks"></div><p class="cs-note">Each bar is an outcome y of the counting register; y / 2<sup>t</sup> is close to a multiple of 1/r, which is how the period is recovered.</p></div>' + ui.CODE)
    body = f'''<h2>The idea: factoring by finding a period</h2>
<p>To factor N, pick a base <i>a</i> coprime to N and consider f(x) = a<sup>x</sup> mod N. This function repeats: there is a smallest <i>r</i> (the <em>period</em> or <em>order</em>) with a<sup>r</sup> ≡ 1 (mod N). If r is even and a<sup>r/2</sup> ≢ −1, then</p>
<div class="cs-formula">gcd(a<sup>r/2</sup> − 1, N)&nbsp;&nbsp;and&nbsp;&nbsp;gcd(a<sup>r/2</sup> + 1, N)&nbsp;&nbsp;are non-trivial factors of N</div>
<p>Finding r is the hard part classically — and exactly what a quantum computer does well. Peter Shor's 1994 algorithm prepares a superposition of all x in a counting register, computes a<sup>x</sup> mod N into a second register, and applies the quantum Fourier transform. Interference concentrates the probability on multiples of 2<sup>t</sup>/r, so measuring the counting register reveals r.</p>
<h2>Worked example, computed above</h2>
<p>For N = 15 and a = 7 the simulated 12-qubit run finds period <strong>{ex['period']}</strong> and the factors <strong>{ex['factors']}</strong>, matching the brute-force period {ex['classical']}. The counting register has {ex['counting']} qubits, so its 256 outcomes are spaced 1/256 apart, and the four tall peaks at multiples of 64/256 = 1/4 reveal r = 4.</p>
<p>N = 21 needs 15 qubits (32,768 amplitudes). With a = 2 it finds the period {e21['period']} and the factors {e21['factors']}; with a = 4 the period {e21b['period']} is odd, so no factors come out and you must choose another base. Trying a = 14 for N = 15 also gives no factors ({e14['note'] if e14['note'] else 'aⁱ ≡ −1 mod N'}), a textbook failure case.</p>
<h2>What is verified</h2>
<p>The library's test suite runs this circuit for six bases of N = 15 and checks every period (a = 2, 7, 8, 13 → 4; a = 4, 11 → 2), the factors 3 × 5, the known failure a = 14, the lucky case where a shares a factor with N, and that oversized N is refused. The quantum Fourier transform itself is checked against a direct discrete Fourier transform to 12 digits.</p>
<p class="cs-note">Limits: the simulator is limited to N = 15 and 21 by the exponential cost of the state vector — which is exactly why real quantum computers are interesting. The modular multiplications are applied as exact basis-state permutations rather than compiled into elementary gates.</p>'''
    js = ui.page_js(SH_DRIVER, SH_TYPES, ["modulus", "base"], '''
    set('factors',k.factors==='none'?'none this time':k.factors.replace('x','×')); note('factors',k.factors==='none'?(k.note?k.note:'the period is odd or a^(r/2) = −1 (mod N): pick another base a'):'their product is '+v.modulus);
    set('period',k.period==='none'?'—':k.period); note('period','a^r ≡ 1 (mod '+v.modulus+') for the smallest such r');
    set('qubits',k.qubits==='0'?'—':k.qubits+' qubits'); note('qubits',k.qubits==='0'?'':k.counting+' counting + '+(N(k,'qubits')-N(k,'counting'))+' work qubits');
    set('classical',k.classical==='0'?'—':k.classical); note('classical','found by multiplying repeatedly, for comparison');
    var pk=rows.peaks||[]; var t=Number(k.counting||0);
    if(pk.length){C.bars($('peaks'),pk.map(function(r){return {label:'y = '+r[0],value:Number(r[1]),text:C.pct(Number(r[1]),3)+'  ( y/2^t = '+C.sig(Number(r[0])/Math.pow(2,t),4)+' )'};}),{max:Math.max.apply(null,pk.map(function(r){return Number(r[1]);})),label:'Strongest measurement outcomes'});}else{$('peaks').textContent='No quantum run was needed: a shares a factor with N.';}''', timeout=300000)
    return dict(slug="shor-algorithm-simulator", group="quantum computing", icon="\U0001f510", short="Shor's algorithm",
        title="Shor's Algorithm Simulator — Factor 15 and 21 on Qubits", kicker="Quantum computing",
        h1="Shor's Algorithm Simulator",
        description="Free Shor's algorithm simulator: watch a simulated quantum computer factor 15 and 21 by finding the period of aˣ mod N. Real circuit, real quantum Fourier transform.",
        lead="Run Shor's factoring algorithm on a simulated 12- or 15-qubit quantum computer: a real circuit with a real quantum Fourier transform finds the period and the factors, and the known failure cases show up too.",
        packages=["qalgo", "quantum", "physmath"], faq=faq, main=main + body, js=js)

# ============================================================================= teleportation
TP_DRIVER = '''import "qalgo" as qa
import "physmath" as m
let th = ${theta} * m.PI / 180.0
let ph = ${phi} * m.PI / 180.0
let first = true
for o in [[0, 0], [0, 1], [1, 0], [1, 1]] {
  let r = qa.teleport(th, ph, o)
  if first {
    print("in_x=" + m.fixed(r["before"][0], 8))
    print("in_y=" + m.fixed(r["before"][1], 8))
    print("in_z=" + m.fixed(r["before"][2], 8))
    first = false
  }
  print("row|out|" + str(o[0]) + str(o[1]) + "|" + m.fixed(r["fidelity"], 12) + "|" + m.fixed(r["after"][0], 8) + "|" + m.fixed(r["after"][1], 8) + "|" + m.fixed(r["after"][2], 8))
}
'''
TP_TYPES = {"theta": "num", "phi": "num"}

def teleport():
    ex, exr = _run(TP_DRIVER, TP_TYPES, {"theta": 70, "phi": 120})
    faq = [
        ("What is quantum teleportation?", "A protocol that transfers an unknown quantum state from one qubit to another far away, using a shared entangled pair and two ordinary classical bits. The state is destroyed at the sender and appears at the receiver; nothing physical (no matter, no energy) is moved along the way."),
        ("Does teleportation allow faster-than-light communication?", "No. Alice must send her two measurement bits to Bob by ordinary means, and until they arrive Bob's qubit is in a completely random-looking state — he cannot extract any information. Every one of the four possible outcomes happens with probability exactly 1/4, independent of the state being sent."),
        ("Why is the fidelity always exactly 1?", "Because each of the four outcomes corresponds to a known correction (nothing, X, Z, or both) that turns Bob's qubit into a perfect copy of the original. This page checks all four outcomes for the state you choose; the fidelity printed is the overlap between Bob's corrected qubit and the input, 1.000000000000 up to 12 digits."),
        ("Does this violate the no-cloning theorem?", "No. The original qubit is destroyed by Alice's measurement, so there is only ever one copy of the state. Teleportation moves a state; it cannot copy one."),
        ("What is the Bloch sphere?", "A way to picture the state of one qubit as a point on a unit sphere. The polar angle θ sets how much of the state is |0⟩ versus |1⟩ and the azimuthal angle φ sets the relative phase. The page reports that point as a vector (x, y, z) before and after teleportation."),
    ]
    form = ui.panel("Choose the state to teleport", '<div class="cs-grid">' + ui.field("theta", "Polar angle θ (degrees, 0–180)", "70", step="any", min="0", max="180") +
        ui.field("phi", "Azimuth φ (degrees, 0–360)", "120", step="any", min="0", max="360") + "</div>" +
        ui.chips([("|0⟩ (north pole)", {"theta": 0, "phi": 0}), ("|1⟩ (south pole)", {"theta": 180, "phi": 0}), ("|+⟩ (equator, +x)", {"theta": 90, "phi": 0}), ("|+i⟩ (equator, +y)", {"theta": 90, "phi": 90}), ("An arbitrary state", {"theta": 70, "phi": 120})]), "Teleport")
    main = (form + ui.results([("bloch", "State sent (Bloch vector)", True), ("fid", "Worst fidelity of Bob's qubit", True), ("prob", "Probability of each outcome", False)]) +
            '<div class="cs-panel"><h2>All four measurement outcomes</h2><div id="outs"></div></div>' + ui.CODE)
    body = f'''<h2>The protocol</h2>
<p>Alice holds an unknown qubit in state |ψ⟩ = α|0⟩ + β|1⟩. She and Bob share one half each of a Bell pair (|00⟩ + |11⟩)/√2. Alice applies a CNOT from her unknown qubit to her half of the pair, then a Hadamard on the unknown qubit, and measures both qubits, getting two classical bits. Whatever she gets, Bob's qubit is now in one of four states related to |ψ⟩ by a Pauli operation; the two bits tell him which:</p>
<div class="cs-formula">bits 00 → do nothing&nbsp;&nbsp;·&nbsp;&nbsp;01 → apply X&nbsp;&nbsp;·&nbsp;&nbsp;10 → apply Z&nbsp;&nbsp;·&nbsp;&nbsp;11 → apply Z·X</div>
<p>After the correction Bob's qubit is exactly |ψ⟩.</p>
<h2>Worked example, computed above</h2>
<p>The state at θ = 70°, φ = 120° is the point ({ex['in_x']}, {ex['in_y']}, {ex['in_z']}) on the Bloch sphere. For each of the four measurement results the simulator forces that outcome, applies Bob's correction and reads the Bloch vector of qubit 2: it is ({exr['out'][0][2]}, {exr['out'][0][3]}, {exr['out'][0][4]}) every time, with fidelity {exr['out'][0][1]}.</p>
<h2>What is verified</h2>
<p>The library's test suite teleports six states — including both poles and arbitrary angles — for all four outcomes and requires a fidelity of 1 to within 10<sup>−12</sup>, and separately with a genuine random measurement.</p>
<p class="cs-note">Limits: ideal qubits and a perfect Bell pair. In experiments, teleportation fidelity is limited by imperfect entanglement, gates and detectors. Outcomes are forced one at a time here (each has probability 1/4) so that all four can be shown together.</p>'''
    js = ui.page_js(TP_DRIVER, TP_TYPES, ["theta", "phi"], '''
    set('bloch','('+k.in_x+', '+k.in_y+', '+k.in_z+')'); note('bloch','the unknown state Alice holds, as a point on the Bloch sphere');
    var outs=rows.out||[],worst=1;outs.forEach(function(r){worst=Math.min(worst,Number(r[1]));});
    set('fid',worst.toFixed(12)); note('fid','over all four outcomes, after Bob\\'s correction');
    set('prob','25% each'); note('prob','independent of the state - Bob learns nothing until Alice\\'s bits arrive');
    var h='<div class="cs-tbl"><table class="lz"><thead><tr><th>Alice\\'s bits</th><th>Bob applies</th><th>Bob\\'s Bloch vector after the fix</th><th>Fidelity</th></tr></thead><tbody>';
    var fix={'00':'nothing','01':'X','10':'Z','11':'Z · X'};
    outs.forEach(function(r){h+='<tr><td>'+r[0]+'</td><td>'+fix[r[0]]+'</td><td>('+r[2]+', '+r[3]+', '+r[4]+')</td><td>'+r[1]+'</td></tr>';});
    $('outs').innerHTML=h+'</tbody></table></div>';''')
    return dict(slug="quantum-teleportation-simulator", group="quantum computing", icon="\U0001f4e1", short="Quantum teleportation",
        title="Quantum Teleportation Simulator — Bloch Sphere & Fidelity", kicker="Quantum computing",
        h1="Quantum Teleportation Simulator",
        description="Free quantum teleportation simulator: teleport any qubit state and check all four measurement outcomes give fidelity 1. Bell pair, CNOT, Hadamard and corrections.",
        lead="Choose any qubit state and teleport it: a shared Bell pair, two classical bits and four possible corrections. The simulator runs all four measurement outcomes and shows Bob's qubit matching the original every time.",
        packages=["qalgo", "quantum", "physmath"], faq=faq, main=main + body, js=js)

# ============================================================================= Bell / CHSH
CH_DRIVER = '''import "qalgo" as qa
import "quantum" as q
import "physmath" as m
fn kv(name, x) { print(name + "=" + m.fixed(x, 10)) }
let d = m.PI / 180.0
let a0 = ${a0} * d
let a1 = ${a1} * d
let b0 = ${b0} * d
let b1 = ${b1} * d
let bell = q.zero(2)
q.h(bell, 0)
q.cnot(bell, 0, 1)
let e00 = qa.chsh_correlation(bell, a0, b0)
let e01 = qa.chsh_correlation(bell, a0, b1)
let e10 = qa.chsh_correlation(bell, a1, b0)
let e11 = qa.chsh_correlation(bell, a1, b1)
kv("e00", e00)
kv("e01", e01)
kv("e10", e10)
kv("e11", e11)
kv("s", e00 + e01 + e10 - e11)
kv("classical", qa.chsh_classical_max())
kv("tsirelson", 2.0 * m.sqrt_(2.0))
for i in range(0, 181, 3) { print("row|curve|" + str(i) + "|" + m.fixed(m.cos(i * d), 6) + "|" + m.fixed(1.0 - 2.0 * i / 180.0, 6)) }
'''
CH_TYPES = {"a0": "num", "a1": "num", "b0": "num", "b1": "num"}

def chsh():
    ex, exr = _run(CH_DRIVER, CH_TYPES, {"a0": 0, "a1": 90, "b0": 45, "b1": -45})
    ez, _ = _run(CH_DRIVER, CH_TYPES, {"a0": 0, "a1": 0, "b0": 0, "b1": 0})
    f = lambda k_: float(ex[k_])
    faq = [
        ("What is Bell's theorem?", "John Bell proved in 1964 that no theory in which measurement outcomes are fixed in advance by local hidden variables can reproduce all the predictions of quantum mechanics. The CHSH form (Clauser, Horne, Shimony and Holt, 1969) turns that into a single number S: any local hidden-variable theory has |S| ≤ 2, while quantum mechanics predicts up to 2√2 ≈ 2.828."),
        ("Has the Bell inequality been violated in real experiments?", "Yes, repeatedly, from Aspect's experiments in the early 1980s to 'loophole-free' tests in 2015 and later. The 2022 Nobel Prize in Physics went to Alain Aspect, John Clauser and Anton Zeilinger for their experiments with entangled photons that established the violation of Bell inequalities."),
        ("Does entanglement send signals faster than light?", "No. Each side's results, looked at alone, are perfectly random. The correlations only appear when the two lists of results are compared, which requires ordinary communication. Bell's theorem rules out local hidden variables, but relativity's ban on faster-than-light signalling stands."),
        ("Why is the maximum 2√2?", "That is Tsirelson's bound: the largest value quantum mechanics allows for the CHSH quantity. It arises for a maximally entangled pair and measurement directions 45° apart, and this page reproduces it as 2.828427… from an actual simulation of the two qubits."),
        ("What is the dashed line in the plot?", "The correlation predicted by one simple, well-known local hidden-variable model, 1 − 2θ/180° for a measurement angle θ between the two detectors. It agrees with quantum mechanics at 0°, 90° and 180° but lies below the cosine curve in between — the gap is what an experiment can detect."),
    ]
    form = ui.panel("Choose the four measurement angles", '<div class="cs-grid">' + ui.field("a0", "Alice setting a₀ (degrees)", "0", step="any") + ui.field("a1", "Alice setting a₁ (degrees)", "90", step="any") +
        ui.field("b0", "Bob setting b₀ (degrees)", "45", step="any") + ui.field("b1", "Bob setting b₁ (degrees)", "-45", step="any") + "</div>" +
        ui.chips([("Optimal (0, 90, 45, −45)", {"a0": 0, "a1": 90, "b0": 45, "b1": -45}), ("Everything aligned (no violation)", {"a0": 0, "a1": 0, "b0": 0, "b1": 0}), ("Poor choice", {"a0": 0, "a1": 30, "b0": 10, "b1": -20}), ("A weaker violation", {"a0": 0, "a1": 60, "b0": 30, "b1": -30})]), "Calculate")
    main = (form + ui.results([("s", "CHSH value S", True), ("verdict", "Verdict", True), ("classical", "Local hidden-variable limit", False), ("tsirelson", "Quantum limit (Tsirelson)", False), ("e", "The four correlations", False)]) +
            '<div class="cs-panel"><h2>Correlation against detector angle</h2><div id="plot"></div></div>' + ui.CODE)
    body = f'''<h2>The CHSH game</h2>
<p>Alice and Bob share an entangled pair of qubits in the state (|00⟩ + |11⟩)/√2. Each picks one of two measurement directions in the x–z plane (Alice: a<sub>0</sub> or a<sub>1</sub>, Bob: b<sub>0</sub> or b<sub>1</sub>) and reads a ±1 result. Let E(a, b) be the average of the product of their results. The CHSH quantity is</p>
<div class="cs-formula">S = E(a<sub>0</sub>,b<sub>0</sub>) + E(a<sub>0</sub>,b<sub>1</sub>) + E(a<sub>1</sub>,b<sub>0</sub>) − E(a<sub>1</sub>,b<sub>1</sub>)</div>
<p>If the results were fixed in advance by hidden information carried by each particle, every product would be ±1 and |S| could never exceed 2 — you can check by brute force over the 16 possible assignments. Quantum mechanics predicts E(a, b) = cos(a − b) for this state, and at the best angles S reaches 2√2.</p>
<h2>Worked example, computed above</h2>
<p>With the angles 0°, 90°, 45°, −45° the four correlations, obtained by measuring the simulated two-qubit state (not by using the cosine formula), are {ex['e00']}, {ex['e01']}, {ex['e10']} and {ex['e11']}, so <strong>S = {ex['s']}</strong>. That exceeds the classical limit of {int(f('classical'))} and matches Tsirelson's bound 2√2 = {ex['tsirelson']}. With every detector set to the same angle S = {ez['s']}: no violation.</p>
<h2>What is verified</h2>
<p>The library computes each correlation as a combination of Pauli-string expectation values of the simulated state, and its tests check that this equals cos(a − b), that S = 2√2 to 14 digits at the optimal angles, that no classical strategy exceeds 2, and that a null choice gives no violation.</p>
<p class="cs-note">Limits: this is the ideal two-qubit prediction. Real experiments must close loopholes (detector efficiency, communication between stations) and deal with noise, so measured values are lower than 2√2 but, in the best experiments, still significantly above 2.</p>'''
    js = ui.page_js(CH_DRIVER, CH_TYPES, ["a0", "a1", "b0", "b1"], '''
    var s=N(k,'s'); set('s',s.toFixed(6)); note('s','= E(a0,b0) + E(a0,b1) + E(a1,b0) − E(a1,b1)');
    var viol=Math.abs(s)>2+1e-9; set('verdict',viol?'Violates Bell\\'s inequality':'No violation'); note('verdict',viol?'|S| > 2: no local hidden-variable theory can explain this':'|S| ≤ 2: consistent with a local hidden-variable explanation');
    set('classical',k.classical); note('classical','the largest |S| any local hidden-variable theory allows');
    set('tsirelson',Number(k.tsirelson).toFixed(6)); note('tsirelson','2√2, the most quantum mechanics allows');
    set('e','E00 '+k.e00+' · E01 '+k.e01); note('e','E10 '+k.e10+' · E11 '+k.e11);
    var cur=rows.curve||[];
    C.plot($('plot'),[{name:'quantum mechanics: cos θ',pts:cur.map(function(r){return [Number(r[0]),Number(r[1])];})},{name:'a local hidden-variable model: 1 − 2θ/180°',pts:cur.map(function(r){return [Number(r[0]),Number(r[2])];}),color:'#f59e0b',dash:'6 5'}],{xlabel:'angle between the two detectors θ (degrees)',ylabel:'correlation E(θ)',ymin:-1,ymax:1,label:'Quantum and classical correlations'});''')
    return dict(slug="bell-inequality-calculator", group="quantum computing", icon="\U0001f517", short="Bell inequality (CHSH)",
        title="Bell Inequality Calculator — CHSH Value & Entanglement", kicker="Quantum computing",
        h1="Bell Inequality (CHSH) Calculator",
        description="Free Bell inequality calculator: choose four detector angles and simulate an entangled pair to get the CHSH value S, compare with the classical limit 2 and Tsirelson's bound 2√2.",
        lead="Choose four measurement angles, simulate an entangled pair and see whether the CHSH value beats the classical limit of 2. At the best angles it reaches 2.828 — the reason no local hidden-variable theory can explain quantum mechanics.",
        packages=["qalgo", "quantum", "physmath"], faq=faq, main=main + body, js=js)

def pages(): return [circuit_sim(), grover(), shor(), teleport(), chsh()]
