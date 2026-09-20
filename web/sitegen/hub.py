from common import *
import ui

GROUPS = [("quantum computing", "Quantum computing", "Simulate real quantum circuits and famous algorithms on up to 10–15 qubits, with exact amplitudes."),
          ("quantum mechanics", "Quantum mechanics", "Atoms, matter waves, confinement and tunneling: the textbook physics, computed exactly."),
          ("relativity", "Relativity", "Special and general relativity: time dilation, black holes and interstellar travel."),
          ("cosmology", "Cosmology", "How old the universe is and how far away distant galaxies are.")]

def hub(chrome, pages, tests, lib_file, lib_hash, examples):
    crumbs = [("Larz OS", "/"), ("Cosmos", "/cosmos/")]
    from seo import SEO
    title, desc = SEO["cosmos"]
    faq = [
        ("What is Larzscript Cosmos?", "An open-source physics toolkit written entirely in the Larzscript programming language: a quantum-circuit simulator, quantum algorithms (Grover, Shor, teleportation, phase estimation), textbook quantum mechanics, special and general relativity, and astrophysics. The calculators on this site run that same code in your browser."),
        ("How do I know the answers are right?", f"The library has {tests} automated checks. Numerical routines are compared with IEEE reference values, the quantum simulator with an independent dense-matrix implementation, relativity with 50-digit decimal arithmetic, and physical results with published values (the Sun's Schwarzschild radius, GPS's +38 microseconds per day, hydrogen's Balmer lines, the Planck-2018 age of the universe). The tests are deliberately broken (mutation-checked) to make sure they can fail."),
        ("Does it run on my device or on a server?", "On your device. The Larzscript interpreter is compiled to WebAssembly and runs in a background thread of your browser; your inputs are never sent anywhere."),
        ("Can I use the library in my own programs?", "Yes — it is MIT-licensed. Install a Larzscript release (a single binary), clone the repository and <code>import \"quantum\" as q</code>. The repository documents every function."),
    ]
    cards = ""
    for gid, gname, gdesc in GROUPS:
        ps = [p for p in pages if p["group"] == gid]
        cards += f'<h2 id="{gid.replace(" ", "-")}">{gname}</h2><p class="cs-note">{gdesc}</p><div class="cs-cards">' + "".join(
            f'<a href="/{p["slug"]}/"><b>{p["icon"]} {esc(p["h1"])}</b><span>{esc(p["lead"].split(". ")[0].rstrip(".") + ".")}</span></a>' for p in ps) + "</div>"
    body = f'''<span class="kicker">Open-source physics</span><h1>Larzscript Cosmos</h1>
<p class="lede">Quantum computing, quantum mechanics, relativity and cosmology — calculators and simulators backed by a verified open-source library written in Larzscript, running live in your browser.</p>
{badges(tests)}
{cards}
<h2>Why you can trust the numbers</h2>
<div class="stats"><div class="stat"><b>{tests}</b><span>automated checks</span></div><div class="stat"><b>8</b><span>Larzscript packages</span></div><div class="stat"><b>10⁻¹⁵</b><span>typical relative accuracy of the maths core</span></div><div class="stat"><b>0</b><span>dependencies — pure Larzscript</span></div></div>
<p>Larzscript ships no <code>sin</code>, <code>cos</code>, <code>exp</code> or <code>ln</code>, and its built-in <code>sqrt</code> is wrong below about 10<sup>−36</sup>. So the project starts by writing a numerical core, <code>physmath</code>, and testing it against IEEE reference values at hundreds of points per function; everything else — the quantum simulator, the relativity formulas, the cosmology integrals — is built and tested on top of it. Independent references are used wherever possible: a separate dense-matrix quantum simulator, 50-digit decimal arithmetic, closed-form cosmology, and published measurements.</p>
<h2>Use the library yourself</h2>
<p>This is a complete program — it prints <code>0.7071|00&gt; + 0.7071|11&gt;</code>, the Bell state — using the same package the <a href="/quantum-circuit-simulator/">circuit simulator</a> runs:</p>
<pre class="cs-code">import "quantum" as q

let s = q.zero(2)          # two qubits, both |0&gt;
q.h(s, 0)                  # Hadamard on qubit 0
q.cnot(s, 0, 1)            # entangle qubit 1 with it
print(q.state_str(s, 4))   # 0.7071|00&gt; + 0.7071|11&gt;
print(q.sample(s, 1000))   # about 500 x 00 and 500 x 11</pre>
<p><a href="{REPO}" target="_blank" rel="noopener">Source code, documentation and tests on GitHub →</a> · <a href="/larzscript/">What is Larzscript?</a> · <a href="/learn-larzscript/">Learn Larzscript</a></p>
{faq_html(faq)}
<div class="related"><h2>More space and science on Larz OS</h2><div class="relgrid"><a href="/rocket-fuel-calculator/"><span>\U0001f680</span>Rocket fuel calculator</a><a href="/asteroid-watch/"><span>☄️</span>Asteroid watch</a><a href="/stack/larzorbits/"><span>\U0001f6f0️</span>LarzOrbits</a><a href="/tools/"><span>\U0001f9f0</span>All free tools</a></div></div>'''
    itemlist = {"@context": "https://schema.org", "@type": "ItemList", "name": "Larzscript Cosmos calculators", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "url": f"{SITE}/{p['slug']}/", "name": p["h1"]} for i, p in enumerate(pages)]}
    code = {"@context": "https://schema.org", "@type": "SoftwareSourceCode", "name": "larzscript-cosmos", "codeRepository": REPO, "programmingLanguage": "Larzscript", "license": "https://opensource.org/licenses/MIT",
            "description": "Quantum-circuit simulator, quantum algorithms, quantum mechanics, relativity and astrophysics in pure Larzscript."}
    h = head(chrome, path="/cosmos/", title=title, description=desc, crumbs=crumbs, faq=faq, extra_ld=[itemlist, code], lib_hash=lib_hash)
    scripts = '<script>window.COSMOS_CONFIG=%s;</script>' % json.dumps({"worker": f"{ASSETS}cosmos-worker.js?v={lib_hash}", "runtime": RUNTIME, "lib": f"{ASSETS}{lib_file}"})
    return dict(html=assemble(chrome, h, crumbs_html(crumbs) + body, scripts), title=title, description=desc)
