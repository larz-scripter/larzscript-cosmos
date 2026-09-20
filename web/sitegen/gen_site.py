#!/usr/bin/env python3
"""Generate the larzos.com Cosmos pages into web/dist/site (ready to copy to /var/www/larzos).

  python3 web/sitegen/gen_site.py --chrome /path/to/a/live/larzos-tool-page.html --runtime /path/to/dir-with-larzscript-web.{js,wasm}
"""
import argparse, glob, json, os, re, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import pages_relativity, pages_qm, pages_qc, pages_cosmo, hub, seo
seo.check()

ap = argparse.ArgumentParser()
ap.add_argument("--chrome", required=True)
ap.add_argument("--runtime", required=True)
ap.add_argument("--out", default=os.path.join(ROOT, "web", "dist", "site"))
ap.add_argument("--tests", type=int, default=0, help="number of automated checks to quote (0 = run the suite and count)")
a = ap.parse_args()

def count_tests():
    env = dict(os.environ)
    p = subprocess.run([os.path.join(ROOT, "tests", "run_tests.sh")], capture_output=True, text=True, cwd=ROOT, env=env)
    n = sum(int(m) for m in re.findall(r"^(\d+) passed, (\d+) failed$", p.stdout, re.M) for m in [m[0]] ) if False else 0
    total = 0; failed = 0
    for m in re.finditer(r"^(\d+) passed, (\d+) failed$", p.stdout, re.M): total += int(m.group(1)); failed += int(m.group(2))
    assert failed == 0 and total > 0, "the test suite must pass before publishing pages:\n" + p.stdout[-800:]
    return total

tests = a.tests or count_tests()
subprocess.run([sys.executable, os.path.join(ROOT, "web", "build_lib.py")], check=True, capture_output=True)
man = json.load(open(os.path.join(ROOT, "web", "dist", "manifest.json")))
lib_file, lib_hash = man["file"], man["hash"]
chrome = Chrome(a.chrome)

pages = pages_qc.pages() + pages_qm.pages() + pages_relativity.pages() + pages_cosmo.pages()
for p in pages: p['title'], p['description'] = seo.SEO[p['slug']]
out = a.out
shutil.rmtree(out, ignore_errors=True)
os.makedirs(os.path.join(out, "cosmos", "assets", os.path.basename(RUNTIME.rstrip("/"))), exist_ok=True)
A = os.path.join(out, "cosmos", "assets")
for f in ("cosmos.js", "cosmos.css", "cosmos-worker.js"): shutil.copy(os.path.join(ROOT, "web", "assets", f), A)
shutil.copy(os.path.join(ROOT, "web", "dist", lib_file), A)
for f in ("larzscript-web.js", "larzscript-web.wasm"): shutil.copy(os.path.join(a.runtime, f), os.path.join(A, os.path.basename(RUNTIME.rstrip("/"))))

report = []
for p in pages:
    crumbs = [("Larz OS", "/"), ("Cosmos", "/cosmos/"), (p["h1"], f"/{p['slug']}/")]
    h = head(chrome, path=f"/{p['slug']}/", title=p["title"], description=p["description"], crumbs=crumbs, app={"name": p["h1"]}, faq=p["faq"], lib_hash=lib_hash)
    main = (crumbs_html(crumbs) + f'<span class="kicker">{esc(p["kicker"])}</span><h1>{esc(p["h1"])}</h1><p class="lede">{esc(p["lead"])}</p>' + badges(tests) +
            p["main"] + faq_html(p["faq"]) + related_html(p, pages) + source_note(p["packages"]))
    html_out = assemble(chrome, h, main, page_scripts(lib_file, lib_hash, "(function(){" + p["js"] + "})();"))
    d = os.path.join(out, p["slug"]); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(html_out)
    report.append((p["slug"], len(p["title"]), len(p["description"]), len(html_out)))

hb = hub.hub(chrome, pages, tests, lib_file, lib_hash, {})
os.makedirs(os.path.join(out, "cosmos"), exist_ok=True)
open(os.path.join(out, "cosmos", "index.html"), "w", encoding="utf-8").write(hb["html"])
report.append(("cosmos", len(hb["title"]), len(hb["description"]), len(hb["html"])))

urls = ["/cosmos/"] + [f"/{p['slug']}/" for p in pages]
frag = "".join(f'<url><loc>{SITE}{u}</loc><lastmod>{TODAY}</lastmod><changefreq>monthly</changefreq><priority>{"0.8" if u == "/cosmos/" else "0.7"}</priority></url>\n' for u in urls)
open(os.path.join(out, "sitemap-cosmos.fragment.xml"), "w").write(frag)
# cards for the larzos.com /tools/ index, in exactly that page's markup
def card(slug, icon, name, desc, extra=""):
    s = (name + " " + desc).lower()
    return ('<a class="tcard" href="/%s/" data-cat="study" data-s="%s"><span class="ti">%s</span><span class="tb"><span class="tn">%s</span><span class="td">%s</span></span></a>'
           % (slug, esc(s), icon, esc(name), esc(desc)))
cards = card("cosmos", "\U0001f30c", "Larzscript Cosmos", "Quantum computing, relativity and astrophysics calculators running open-source Larzscript in your browser.")
cards += "".join(card(p["slug"], p["icon"], p["h1"], p["lead"].split(". ")[0].rstrip(".") + ".") for p in pages)
open(os.path.join(out, "tools-cards.fragment.html"), "w", encoding="utf-8").write(cards)
json.dump({"urls": urls, "lib": lib_file, "hash": lib_hash, "tests": tests, "pages": [r[0] for r in report]}, open(os.path.join(out, "manifest.json"), "w"), indent=1)
print("%-36s %5s %5s %8s" % ("page", "title", "desc", "bytes"))
for r in report: print("%-36s %5d %5d %8d%s" % (r[0], r[1], r[2], r[3], "   <-- title > 62" if r[1] > 62 else "") + ("   <-- desc > 165" if r[2] > 165 else ""))
print("tests quoted:", tests, "| lib", lib_file)
