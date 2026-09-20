#!/usr/bin/env python3
"""Static checks on the generated pages: structure, ids, structured data, links, SEO limits."""
import html.parser, json, os, re, sys, urllib.request
SITE = sys.argv[1]
man = json.load(open(os.path.join(SITE, "manifest.json")))
problems = []
def bad(page, msg): problems.append("%s: %s" % (page, msg))
VOID = {"meta", "link", "br", "img", "input", "hr", "source", "path", "line", "circle", "rect", "text", "stop"}
class P(html.parser.HTMLParser):
    def __init__(s): super().__init__(); s.stack = []; s.ids = {}; s.err = []; s.links = []; s.h1 = 0; s.in_main = False
    def handle_starttag(s, t, a):
        a = dict(a)
        if t == "main": s.in_main = True
        if t == "h1": s.h1 += 1
        if "id" in a: s.ids[a["id"]] = s.ids.get(a["id"], 0) + 1
        if t == "a" and "href" in a: s.links.append(a["href"])
        if t not in VOID and t not in ("script", "style"): s.stack.append(t)
    def handle_endtag(s, t):
        if t in VOID: return
        if t in ("script", "style"): return
        if s.stack and s.stack[-1] == t: s.stack.pop()
        elif t in s.stack:
            # tolerate optional-close (p, li, td...) only
            while s.stack and s.stack[-1] != t: 
                x = s.stack.pop()
                if x not in ("p", "li", "td", "th", "tr", "option"): s.err.append("unclosed <%s> before </%s>" % (x, t))
            if s.stack: s.stack.pop()
        else: s.err.append("stray </%s>" % t)
new_paths = set(man["urls"])
seen_titles = {}
for slug in man["pages"]:
    path = os.path.join(SITE, slug, "index.html")
    h = open(path, encoding="utf-8").read()
    p = P(); p.feed(h)
    for e in p.err[:5]: bad(slug, "HTML: " + e)
    if p.h1 != 1: bad(slug, "expected exactly one <h1>, found %d" % p.h1)
    dup = [i for i, c in p.ids.items() if c > 1]
    if dup: bad(slug, "duplicate ids " + str(dup))
    import html as _h
    title = _h.unescape(re.search(r"<title>(.*?)</title>", h).group(1)); desc = _h.unescape(re.search(r'name="description" content="(.*?)"', h).group(1))
    if title in seen_titles: bad(slug, "duplicate title with " + seen_titles[title])
    seen_titles[title] = slug
    if not (40 <= len(title) <= 62): bad(slug, "title length %d" % len(title))
    if not (110 <= len(desc) <= 165): bad(slug, "description length %d" % len(desc))
    canon = re.search(r'rel="canonical" href="(.*?)"', h).group(1)
    exp = "https://larzos.com/" + ("" if slug == "" else slug + "/")
    if canon != exp: bad(slug, "canonical %s != %s" % (canon, exp))
    # structured data
    lds = re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S)
    types = []
    for b in lds:
        try: o = json.loads(b); types.append(o.get("@type"))
        except Exception as e: bad(slug, "JSON-LD does not parse: %s" % e)
    for need in ("BreadcrumbList", "FAQPage") + (("WebApplication",) if slug != "cosmos" else ("ItemList", "SoftwareSourceCode")):
        if need not in types: bad(slug, "missing JSON-LD " + need)
    for b in lds:
        o = json.loads(b)
        if o.get("@type") == "FAQPage":
            for q in o["mainEntity"]:
                if q["name"] not in re.sub(r"\s+", " ", h): bad(slug, "FAQ question in JSON-LD not visible on the page: " + q["name"][:50])
    # ids the page script depends on
    js = "\n".join(re.findall(r"<script>(.*?)</script>", h, re.S))
    for m in re.finditer(r"set\('(\w+)'", js):
        if 'data-k="%s"' % m.group(1) not in h: bad(slug, "script sets data-k=%s which is not in the page" % m.group(1))
    for m in re.finditer(r'inputs:(\[[^\]]*\])', js):
        for i in json.loads(m.group(1)):
            if p.ids.get(i) != 1: bad(slug, "script reads input #%s which is missing" % i)
    for m in re.finditer(r"\$\('(\w[\w-]*)'\)", js):
        if m.group(1) not in p.ids: bad(slug, "script uses #%s which is missing" % m.group(1))
    # presets only reference existing inputs, and a preset value for a <select> must be one of its options
    opts = {m.group(1): re.findall(r'<option value="([^"]*)"', m.group(2)) for m in re.finditer(r'<select id="(\w+)">(.*?)</select>', h, re.S)}
    for m in re.finditer(r"data-preset='(\{.*?\})'", h):
        for k, v in json.loads(m.group(1)).items():
            if k not in p.ids: bad(slug, "preset sets unknown input #" + k)
            elif k in opts and str(v) not in opts[k]: bad(slug, "preset sets #%s to %r, which is not one of its options %s" % (k, v, opts[k]))
    # links to NEW pages must be to pages we generate (links to existing pages are verified live below)
    for l in p.links:
        if l.startswith("/") and any(l.startswith("/" + x) for x in ("cosmos",)) and not l.startswith("/cosmos/assets"):
            if l.split("#")[0] not in new_paths: bad(slug, "link into /cosmos/ that is not generated: " + l)
# external internal links must exist on the live site
checked = set()
for slug in man["pages"]:
    h = open(os.path.join(SITE, slug, "index.html"), encoding="utf-8").read()
    for l in set(re.findall(r'href="(/[^"#?]*)"', h)):
        if l in new_paths or l in checked or l.startswith("/cosmos/assets") or l == "/": continue
        checked.add(l)
        try:
            r = urllib.request.urlopen(urllib.request.Request("https://larzos.com" + l, method="HEAD", headers={"User-Agent": "cosmos-check"}), timeout=15)
            if r.status >= 400: bad("links", "%s -> HTTP %d" % (l, r.status))
        except Exception as e: bad("links", "%s -> %s" % (l, e))
print("pages checked:", len(man["pages"]), "| existing-site links verified live:", len(checked))
print("PROBLEMS:" if problems else "no problems"); [print("  -", x) for x in problems]
sys.exit(1 if problems else 0)
