# web - the larzos.com/cosmos calculators

Builds the browser calculators from this repository. Nothing here is needed to use the library.

```
web/build_lib.py            bundles packages/*/main.lz (byte for byte) into dist/cosmos-lib.<hash>.js
web/assets/cosmos-worker.js runs the Larzscript WebAssembly interpreter in a Web Worker and installs the bundle
web/assets/cosmos.js        page-side helpers: builds programs, parses printed output, formats numbers, draws charts
web/assets/cosmos.css       components layered on larzos.com's /assets/content.css
web/sitegen/                page definitions and the generator (gen_site.py)
web/constants.json          the constants table, emitted by tools/gen_constants.py (used to generate test references)
```

```sh
python3 web/sitegen/gen_site.py \
    --chrome  <a saved larzos.com tool page, for the shared nav/footer>  \
    --runtime <dir containing larzscript-web.js and larzscript-web.wasm> # from a Larzscript release (larzscript-web.zip)
python3 web/sitegen/check_static.py web/dist/site       # structure, ids, JSON-LD, presets, SEO lengths, live links
```

Design notes:

- Each page owns a Larzscript "driver" program with `${placeholders}`. The browser fills it from the form (`Cosmos.lit` writes numbers as plain decimals) and sends it to the worker; the build fills it with the default inputs and runs it with the native interpreter, so **every number in the page text is computed by the library**, and the text cannot drift from the tool.
- Programs print `key=value` and `row|table|a|b|c` lines; the page only formats them. All physics stays in Larzscript.
- The interpreter is persistent in the worker, so packages are imported once; a slow calculation (Shor on 15 qubits) never blocks the page.
