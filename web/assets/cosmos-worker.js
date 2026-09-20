/* cosmos-worker.js - runs the Larzscript WebAssembly interpreter off the main thread, so a 15-qubit
 * Shor simulation never freezes the page. Protocol (postMessage):
 *   page -> worker  {type:"init", runtime:"/cosmos/assets/runtime/", lib:"/cosmos/assets/cosmos-lib.<hash>.js"}
 *   worker -> page  {type:"ready", info:{hash, commit, packages, bytes}}   (or {type:"fatal", message})
 *   page -> worker  {type:"run", id, src}
 *   worker -> page  {type:"result", id, rc, lines:[...printed lines, "ERR: ..." for errors], ms}
 * The interpreter is persistent: modules stay imported between runs, so only the first run pays. */
"use strict";
var M = null, out = [];

function fatal(message) { self.postMessage({ type: "fatal", message: String(message) }); }

// The lexer caps a string literal at 8192 characters, so library files are written in small chunks.
function evalSource(src) { return M.ccall("larz_eval_source", "number", ["string"], [src]); }

function install(lib) {
  var names = Object.keys(lib);
  for (var n = 0; n < names.length; n++) {
    var file = JSON.stringify(names[n] + ".lz"), src = lib[names[n]];
    if (evalSource("write_file(" + file + ", \"\")") !== 0) throw new Error("could not create " + names[n]);
    for (var i = 0; i < src.length; i += 2000) {
      if (evalSource("append_file(" + file + ", " + JSON.stringify(src.slice(i, i + 2000)) + ")") !== 0) throw new Error("could not write " + names[n]);
    }
  }
}

self.onmessage = function (ev) {
  var d = ev.data;
  if (d.type === "init") {
    try {
      importScripts(d.runtime + "larzscript-web.js", d.lib);
      Larzscript({
        print: function (s) { out.push(String(s)); },
        printErr: function (s) { out.push("ERR: " + s); },
        locateFile: function (f) { return d.runtime + f; }
      }).then(function (mod) {
        M = mod;
        install(self.COSMOS_LIB);
        out.length = 0;
        self.postMessage({ type: "ready", info: self.COSMOS_LIB_INFO });
      }).catch(function (e) { fatal("engine failed to start: " + (e && e.message || e)); });
    } catch (e) { fatal("engine failed to load: " + (e && e.message || e)); }
  } else if (d.type === "run") {
    if (!M) { self.postMessage({ type: "result", id: d.id, rc: 1, lines: ["ERR: engine not ready"], ms: 0 }); return; }
    out.length = 0;
    var t0 = Date.now(), rc;
    try { rc = evalSource(d.src); } catch (e) { rc = 1; out.push("ERR: " + (e && e.message || e)); }
    self.postMessage({ type: "result", id: d.id, rc: rc, lines: out.slice(), ms: Date.now() - t0 });
  }
};
