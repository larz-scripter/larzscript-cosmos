"""Shared building blocks for the larzos.com Cosmos pages: the site chrome, SEO head, components."""
import html, json, os, re, subprocess

SITE = "https://larzos.com"
REPO = "https://github.com/larz-scripter/larzscript-cosmos"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ASSETS = "/cosmos/assets/"
RUNTIME = ASSETS + "runtime-1.41.0/"
TODAY = os.environ.get("COSMOS_DATE", "2026-09-20")

def esc(s): return html.escape(str(s), quote=True)

# ---------------------------------------------------------------- site chrome (copied from a live page)
class Chrome:
    """The shared nav / account bar / analytics / footer / tab bar, taken byte-for-byte from an existing
    larzos.com tool page so new pages look and behave exactly like the rest of the site. The cron jobs that
    inject these blocks are idempotent (marker-based), so pages that already contain them are left alone."""
    def __init__(self, path):
        h = open(path, encoding="utf-8").read()
        body = h.index("<body>") + len("<body>")
        self.top = h[body:h.index("<main")]                    # <nav> + account bar
        self.tail = h[h.index("<!--LZA-->"):]                  # analytics, nav script, footer, tab bar, </body></html>
        css = re.search(r'<link rel="stylesheet" href="/assets/content.css"><style>(.*?)</style>', h, re.S)
        self.css = css.group(1)                                # the tool-page form/grid/faq styles
        self.crit = re.search(r"<!--LZCRIT-->.*?<!--/LZCRIT-->", h, re.S).group(0)
        assert "<nav" in self.top and "<footer" in self.tail and "</html>" in self.tail

# ---------------------------------------------------------------- head + structured data
def ld(obj): return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "</script>"

def head(chrome, *, path, title, description, crumbs, app=None, faq=None, extra_ld=(), lib_hash="", og_type="website"):
    url = SITE + path
    graph = []
    items = [{"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + p} for i, (n, p) in enumerate(crumbs)]
    graph.append({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items})
    if app:
        graph.append({"@context": "https://schema.org", "@type": "WebApplication", "name": app["name"], "url": url,
                      "description": description, "applicationCategory": "EducationalApplication", "operatingSystem": "Any (web browser with WebAssembly)",
                      "browserRequirements": "Requires WebAssembly and Web Workers", "isAccessibleForFree": True,
                      "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
                      "inLanguage": "en", "datePublished": TODAY, "dateModified": TODAY,
                      "creator": {"@type": "Organization", "name": "Larz OS", "url": SITE + "/"},
                      "isBasedOn": {"@type": "SoftwareSourceCode", "name": "larzscript-cosmos", "codeRepository": REPO, "programmingLanguage": "Larzscript", "license": "https://opensource.org/licenses/MIT"}})
    if faq:
        graph.append({"@context": "https://schema.org", "@type": "FAQPage",
                      "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a)}} for q, a in faq]})
    graph.extend(extra_ld)
    t = esc(title); d = esc(description)
    return ('<!doctype html><html lang="en"><head>' + chrome.crit + '<meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1, viewport-fit=cover">'
            f"<title>{t}</title><meta name=\"description\" content=\"{d}\">"
            f'<link rel="canonical" href="{url}">'
            f'<meta property="og:title" content="{t}"><meta property="og:description" content="{d}"><meta property="og:type" content="{og_type}">'
            f'<meta property="og:url" content="{url}"><meta property="og:site_name" content="Larz OS"><meta property="og:locale" content="en_US">'
            f'<meta name="twitter:card" content="summary"><meta name="twitter:title" content="{t}"><meta name="twitter:description" content="{d}">'
            '<meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large">'
            f'<link rel="stylesheet" href="/assets/content.css"><style>{chrome.css}</style>'
            f'<link rel="stylesheet" href="{ASSETS}cosmos.css?v={lib_hash}">'
            f'<link rel="preload" href="{RUNTIME}larzscript-web.wasm" as="fetch" type="application/wasm" crossorigin>'
            + "".join(ld(g) for g in graph) + "</head>")

# ---------------------------------------------------------------- components
def crumbs_html(crumbs):
    parts = ['<a href="/">Larz OS</a>'] + ['<a href="%s">%s</a>' % (p, esc(n)) for n, p in crumbs[1:-1]] + [esc(crumbs[-1][0])]
    return '<nav class="crumbs" aria-label="Breadcrumb">' + '<span>/</span>'.join(parts) + "</nav>"

def badges(tests):
    return ('<div class="cs-badges"><span class="cs-badge"><b>Real Larzscript</b> running in your browser</span>'
            f'<span class="cs-badge"><b>{tests}</b> automated checks</span><span class="cs-badge">Open source · MIT</span>'
            '<span class="cs-badge">No sign-up · nothing leaves your device</span></div>')

def faq_html(items):
    return '<section class="faqs"><h2>Frequently asked questions</h2>' + "".join(
        f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in items) + "</section>"

def related_html(cur, pages, n=6):
    by_group = [p for p in pages if p["slug"] != cur["slug"]]
    same = [p for p in by_group if p["group"] == cur["group"]]
    other = [p for p in by_group if p["group"] != cur["group"]]
    chosen = (same + other)[:n]
    return ('<div class="related"><h2>More Cosmos calculators</h2><div class="relgrid">' +
            "".join(f'<a href="/{p["slug"]}/"><span>{p["icon"]}</span>{esc(p["short"])}</a>' for p in chosen) +
            '</div><p class="relmore"><a href="/cosmos/">All Cosmos calculators →</a> · '
            '<a href="/rocket-fuel-calculator/">Rocket fuel calculator</a> · <a href="/asteroid-watch/">Asteroid watch</a></p></div>')

def source_note(pkg_names):
    pk = ", ".join("<code>%s</code>" % p for p in pkg_names)
    return ('<p class="hint">Every number on this page is computed by the open-source '
            f'<a href="{REPO}" target="_blank" rel="noopener">larzscript-cosmos</a> library ({pk}), written in '
            '<a href="/larzscript/">Larzscript</a>, and checked against independent references in its test suite. '
            f'<a href="{REPO}/blob/main/docs/VERIFICATION.md" target="_blank" rel="noopener">How it is verified →</a></p>')

def page_scripts(lib_file, lib_hash, page_js):
    cfg = json.dumps({"worker": f"{ASSETS}cosmos-worker.js?v={lib_hash}", "runtime": RUNTIME, "lib": f"{ASSETS}{lib_file}"})
    return (f"<script>window.COSMOS_CONFIG={cfg};</script>"
            f'<script src="{ASSETS}cosmos.js?v={lib_hash}"></script><script>{page_js}</script>')

def assemble(chrome, head_html, main_html, scripts_html):
    return head_html + "<body>" + chrome.top + '<main class="cs-main">' + main_html + "</main>" + scripts_html + chrome.tail.replace("<!--LZA-->", "<!--LZA-->", 1)
