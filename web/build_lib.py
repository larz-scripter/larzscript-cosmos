#!/usr/bin/env python3
"""Bundle packages/*/main.lz into one JS file the browser worker installs into the WebAssembly
interpreter's in-memory filesystem. The sources are the repository's real files, byte for byte -
the browser runs exactly the code the tests verified.

  python3 web/build_lib.py            -> web/dist/cosmos-lib.<hash>.js  (+ manifest.json)"""
import hashlib, json, os, re, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORDER = ["physmath", "physconst", "complex", "quantum", "qalgo", "qmech", "relativity", "astro"]
libs = {}
for name in ORDER:
    src = open(os.path.join(ROOT, "packages", name, "main.lz"), encoding="utf-8").read()
    bad = [c for c in src if ord(c) > 126 or (ord(c) < 32 and c not in "\n\t")]
    assert not bad, "%s has non-ASCII/control characters: %r" % (name, bad[:5])   # keeps the string-literal transport trivial
    libs[name] = src
h = hashlib.sha256(json.dumps(libs, sort_keys=True).encode()).hexdigest()[:10]
try:
    commit = subprocess.check_output(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
except Exception:
    commit = "unknown"
body = "self.COSMOS_LIB = %s;\nself.COSMOS_LIB_INFO = %s;\n" % (
    json.dumps(libs, separators=(",", ":")), json.dumps({"hash": h, "commit": commit, "packages": ORDER, "bytes": sum(len(v) for v in libs.values())}))
os.makedirs(os.path.join(ROOT, "web", "dist"), exist_ok=True)
for old in os.listdir(os.path.join(ROOT, "web", "dist")):
    if old.startswith("cosmos-lib."): os.remove(os.path.join(ROOT, "web", "dist", old))
out = os.path.join(ROOT, "web", "dist", "cosmos-lib.%s.js" % h)
open(out, "w", encoding="utf-8").write(body)
json.dump({"hash": h, "file": os.path.basename(out), "commit": commit, "bytes": len(body), "packages": ORDER}, open(os.path.join(ROOT, "web", "dist", "manifest.json"), "w"))
print("built", os.path.basename(out), len(body), "bytes;", sum(len(v) for v in libs.values()), "bytes of Larzscript in", len(libs), "packages")
