/* cosmos.js - page-side helpers for the Larzscript Cosmos calculators.
 * Numbers are computed by the real Larzscript packages (running in a Web Worker); this file only
 * builds the program text, parses the printed lines, formats numbers and draws charts. */
(function () {
  "use strict";
  var CFG = window.COSMOS_CONFIG || {};
  var worker = null, seq = 0, pending = {}, bootPromise = null, engineInfo = null;

  /* ------------------------------------------------------------------ engine */
  function failAll(msg) {
    Object.keys(pending).forEach(function (k) {
      var p = pending[k]; delete pending[k];
      if (p.timer) clearTimeout(p.timer);
      (p.reject || function () {})(new Error(msg));
    });
  }
  function stop() { if (worker) { try { worker.terminate(); } catch (e) {} } worker = null; bootPromise = null; }
  function boot() {
    if (bootPromise) return bootPromise;
    bootPromise = new Promise(function (resolve, reject) {
      if (typeof Worker === "undefined") { reject(new Error("This browser cannot run Web Workers.")); return; }
      try { worker = new Worker(CFG.worker); } catch (e) { reject(e); return; }
      pending.boot = { resolve: resolve, reject: reject };
      worker.onmessage = function (ev) {
        var d = ev.data;
        if (d.type === "ready") { engineInfo = d.info; var b = pending.boot; delete pending.boot; if (b) b.resolve(d.info); }
        else if (d.type === "result") { var p = pending[d.id]; if (p) { delete pending[d.id]; clearTimeout(p.timer); p.resolve(d); } }
        else if (d.type === "fatal") { failAll(d.message); stop(); }
      };
      worker.onerror = function (e) { failAll("The engine crashed: " + (e && e.message || "worker error")); stop(); };
      worker.postMessage({ type: "init", runtime: CFG.runtime, lib: CFG.lib });
    });
    bootPromise.catch(function () {});
    return bootPromise;
  }
  /* run(src) -> Promise<{ok, lines, err[], ms, kv, rows}> */
  function run(src, opts) {
    opts = opts || {};
    return boot().then(function () {
      return new Promise(function (resolve, reject) {
        var id = ++seq;
        var timer = setTimeout(function () { delete pending[id]; stop(); reject(new Error("This is taking too long (over " + Math.round((opts.timeout || 120000) / 1000) + " s), so it was stopped. Try a smaller input.")); }, opts.timeout || 120000);
        pending[id] = { resolve: resolve, reject: reject, timer: timer };
        worker.postMessage({ type: "run", id: id, src: src });
      });
    }).then(function (d) {
      var parsed = parse(d.lines);
      parsed.ok = d.rc === 0 && parsed.err.length === 0;
      parsed.ms = d.ms;
      return parsed;
    });
  }
  /* Printed lines: "key=value" -> kv, "row|table|a|b|c" -> rows.table, "ERR: ..." -> err */
  function parse(lines) {
    var kv = {}, rows = {}, err = [], raw = [];
    lines.forEach(function (l) {
      if (l.indexOf("ERR: ") === 0) { err.push(l.slice(5)); return; }
      raw.push(l);
      if (l.indexOf("row|") === 0) { var p = l.split("|"); (rows[p[1]] = rows[p[1]] || []).push(p.slice(2)); return; }
      var i = l.indexOf("=");
      if (i > 0 && /^[A-Za-z_][A-Za-z0-9_]*$/.test(l.slice(0, i))) kv[l.slice(0, i)] = l.slice(i + 1);
    });
    return { kv: kv, rows: rows, err: err, lines: raw };
  }
  function warm() { boot(); }

  /* ------------------------------------------------------------------ program text helpers */
  // Larzscript has no exponent syntax on older runtimes, so numbers are written as plain decimals.
  function lit(x) {
    if (typeof x !== "number" || !isFinite(x)) throw new Error("Enter a valid number.");
    var s = String(x);
    var m = /^(-?)(\d+)(?:\.(\d+))?e([+-]?\d+)$/i.exec(s);
    if (m) {
      var digits = m[2] + (m[3] || ""), pt = m[2].length + parseInt(m[4], 10);
      if (pt <= 0) s = m[1] + "0." + new Array(-pt + 1).join("0") + digits;
      else if (pt >= digits.length) s = m[1] + digits + new Array(pt - digits.length + 1).join("0") + ".0";
      else s = m[1] + digits.slice(0, pt) + "." + digits.slice(pt);
    }
    if (s.indexOf(".") < 0) s += ".0";
    return x < 0 ? "(" + s + ")" : s;
  }
  function str(s) {   // ASCII-only string literal
    return '"' + String(s).replace(/[^\x20-\x7e\n]/g, " ").replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\n/g, "\\n") + '"';
  }
  function int(x) { if (typeof x !== "number" || !isFinite(x) || Math.floor(x) !== x) throw new Error("Enter a whole number."); return String(x); }

  /* ------------------------------------------------------------------ number formatting (display only) */
  var SUP = { "-": "⁻", "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹" };
  function sup(n) { return String(n).split("").map(function (c) { return SUP[c] || c; }).join(""); }
  function num(s) { var x = Number(s); return isFinite(x) ? x : NaN; }
  function sig(x, n) {          // n significant digits, scientific for very large/small: 6.626 x 10^-34
    x = Number(x); n = n || 4;
    if (!isFinite(x)) return "—";
    if (x === 0) return "0";
    var a = Math.abs(x);
    if (a >= 1e-4 && a < 1e6) {
      var d = Math.max(0, n - 1 - Math.floor(Math.log10(a)));
      var t = x.toFixed(Math.min(d, 12));
      if (t.indexOf(".") >= 0) t = t.replace(/0+$/, "").replace(/\.$/, "");
      var neg = t.charAt(0) === "-", body = neg ? t.slice(1) : t, parts = body.split(".");
      parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, " ");
      return (neg ? "-" : "") + parts.join(".");
    }
    var e = Math.floor(Math.log10(a)), m = a / Math.pow(10, e);
    var ms = m.toFixed(n - 1);
    if (parseFloat(ms) >= 10) { ms = (m / 10).toFixed(n - 1); e += 1; }
    return (x < 0 ? "-" : "") + ms + " × 10" + sup(e);
  }
  var DUR = [[1e-9, "ns"], [1e-6, "µs"], [1e-3, "ms"], [1, "s"], [60, "min"], [3600, "hours"], [86400, "days"], [31557600, "years"], [31557600e3, "thousand years"], [31557600e6, "million years"], [31557600e9, "billion years"]];
  function duration(sec, n) {
    sec = Number(sec); if (!isFinite(sec)) return "—";
    var a = Math.abs(sec);
    if (a >= 31557600e12) return sig(sec / 31557600, n || 4) + " years";
    var pick = DUR[0];
    for (var i = 0; i < DUR.length; i++) { if (a >= DUR[i][0]) pick = DUR[i]; }
    return sig(sec / pick[0], n || 4) + " " + pick[1];
  }
  var LEN = [[1e-15, "fm"], [1e-12, "pm"], [1e-9, "nm"], [1e-6, "µm"], [1e-3, "mm"], [1, "m"], [1e3, "km"]];
  function length(m, n) {
    m = Number(m); if (!isFinite(m)) return "—";
    var a = Math.abs(m);
    if (a >= 9460730472580800 * 0.1) return sig(m / 9460730472580800, n || 4) + " light-years";
    if (a >= 149597870700 * 0.1) return sig(m / 149597870700, n || 4) + " AU";
    var pick = LEN[0];
    for (var i = 0; i < LEN.length; i++) { if (a >= LEN[i][0]) pick = LEN[i]; }
    return sig(m / pick[0], n || 4) + " " + pick[1];
  }
  function pct(x, n) { return sig(Number(x) * 100, n || 4) + "%"; }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }

  /* ------------------------------------------------------------------ charts */
  function bars(el, items, opts) {
    opts = opts || {};
    var max = opts.max || items.reduce(function (a, b) { return Math.max(a, b.value); }, 0) || 1;
    el.innerHTML = items.map(function (it) {
      var w = Math.max(0, Math.min(100, it.value / max * 100));
      return '<div class="cs-bar"><span class="cs-bl">' + esc(it.label) + '</span><span class="cs-bt"><i style="width:' + w.toFixed(2) + '%"></i></span><span class="cs-bv">' + (it.text != null ? esc(it.text) : sig(it.value, 3)) + "</span></div>";
    }).join("");
    el.setAttribute("role", "img");
    el.setAttribute("aria-label", opts.label || "Bar chart");
  }
  function niceTicks(lo, hi, count) {
    var span = hi - lo || 1, step = Math.pow(10, Math.floor(Math.log10(span / count))), err = span / count / step;
    step *= err >= 7.5 ? 10 : err >= 3.5 ? 5 : err >= 1.5 ? 2 : 1;
    var out = [], v = Math.ceil(lo / step - 1e-9) * step;
    for (; v <= hi + step * 1e-9; v += step) out.push(+v.toPrecision(12));
    return out;
  }
  /* plot(el, series, {xlabel, ylabel, ymin, ymax, xmin, xmax, label}); series = [{name, pts:[[x,y]..], color, dash, dot:[x,y]}] */
  function plot(el, series, opts) {
    opts = opts || {};
    var W = 640, H = 300, L = 54, R = 16, T = 14, B = 44, xs = [], ys = [];
    series.forEach(function (s) { s.pts.forEach(function (p) { xs.push(p[0]); ys.push(p[1]); }); });
    var x0 = opts.xmin != null ? opts.xmin : Math.min.apply(null, xs), x1 = opts.xmax != null ? opts.xmax : Math.max.apply(null, xs);
    var y0 = opts.ymin != null ? opts.ymin : Math.min.apply(null, ys), y1 = opts.ymax != null ? opts.ymax : Math.max.apply(null, ys);
    if (x1 === x0) x1 = x0 + 1; if (y1 === y0) y1 = y0 + 1;
    var sx = function (x) { return L + (x - x0) / (x1 - x0) * (W - L - R); }, sy = function (y) { return H - B - (y - y0) / (y1 - y0) * (H - B - T); };
    var svg = '<svg viewBox="0 0 ' + W + " " + H + '" class="cs-plot" role="img" aria-label="' + esc(opts.label || "Chart") + '" preserveAspectRatio="xMidYMid meet">';
    niceTicks(y0, y1, 5).forEach(function (t) { svg += '<line x1="' + L + '" x2="' + (W - R) + '" y1="' + sy(t).toFixed(1) + '" y2="' + sy(t).toFixed(1) + '" class="g"/><text x="' + (L - 6) + '" y="' + (sy(t) + 4).toFixed(1) + '" text-anchor="end">' + esc(sig(t, 3)) + "</text>"; });
    niceTicks(x0, x1, 6).forEach(function (t) { svg += '<line x1="' + sx(t).toFixed(1) + '" x2="' + sx(t).toFixed(1) + '" y1="' + T + '" y2="' + (H - B) + '" class="g"/><text x="' + sx(t).toFixed(1) + '" y="' + (H - B + 16) + '" text-anchor="middle">' + esc(sig(t, 3)) + "</text>"; });
    svg += '<rect x="' + L + '" y="' + T + '" width="' + (W - L - R) + '" height="' + (H - B - T) + '" class="frame"/>';
    series.forEach(function (s, i) {
      var d = s.pts.map(function (p, j) { return (j ? "L" : "M") + sx(p[0]).toFixed(1) + " " + sy(p[1]).toFixed(1); }).join(" ");
      svg += '<path d="' + d + '" fill="none" stroke="' + (s.color || ["#00c896", "#6366f1", "#f59e0b", "#f87171"][i % 4]) + '" stroke-width="2.4"' + (s.dash ? ' stroke-dasharray="' + s.dash + '"' : "") + ' stroke-linejoin="round"/>';
      if (s.dot) svg += '<circle cx="' + sx(s.dot[0]).toFixed(1) + '" cy="' + sy(s.dot[1]).toFixed(1) + '" r="5" fill="' + (s.color || "#00c896") + '" stroke="#0b0f1a" stroke-width="2"/>';
    });
    if (opts.xlabel) svg += '<text x="' + ((L + W - R) / 2) + '" y="' + (H - 6) + '" text-anchor="middle" class="ax">' + esc(opts.xlabel) + "</text>";
    if (opts.ylabel) svg += '<text transform="translate(13 ' + ((T + H - B) / 2) + ') rotate(-90)" text-anchor="middle" class="ax">' + esc(opts.ylabel) + "</text>";
    svg += "</svg>";
    if (series.length > 1 || (series[0] && series[0].name)) svg += '<div class="cs-legend">' + series.map(function (s, i) { return '<span><i style="background:' + (s.color || ["#00c896", "#6366f1", "#f59e0b", "#f87171"][i % 4]) + '"></i>' + esc(s.name || "") + "</span>"; }).join("") + "</div>";
    el.innerHTML = svg;
  }

  /* ------------------------------------------------------------------ tool wiring */
  /* tool({ inputs:[ids], button:id, build(values)->{src}, render(parsed, values), status:id, code:id, auto:true }) */
  function tool(cfg) {
    var btn = document.getElementById(cfg.button), status = document.getElementById(cfg.status || "cs-status"), codeEl = cfg.code ? document.getElementById(cfg.code) : null, busy = false, again = false, timer = null;
    function values() {
      var v = {};
      cfg.inputs.forEach(function (id) {
        var el = document.getElementById(id); if (!el) return;
        v[id] = (el.type === "number" || el.type === "range") ? (el.value === "" ? NaN : Number(el.value)) : el.value;
      });
      return v;
    }
    function setStatus(msg, kind) { if (status) { status.textContent = msg || ""; status.className = "cs-status" + (kind ? " " + kind : ""); } }
    function go() {
      if (busy) { again = true; return; }
      var vals = values(), built;
      try { built = cfg.build(vals); } catch (e) { setStatus(e.message, "err"); return; }
      busy = true; if (btn) btn.disabled = true; setStatus("Running Larzscript in your browser…", "run");
      run(built.src, { timeout: cfg.timeout }).then(function (res) {
        if (!res.ok) { setStatus(friendly(res.err[0] || "The calculation failed."), "err"); return; }
        if (codeEl) codeEl.textContent = built.src;
        setStatus("Computed in " + (res.ms < 1000 ? res.ms + " ms" : (res.ms / 1000).toFixed(1) + " s") + " by the Larzscript library, running in your browser.", "ok");
        cfg.render(res, vals);
      }).catch(function (e) { setStatus(e.message, "err"); })
        .then(function () { busy = false; if (btn) btn.disabled = false; if (again) { again = false; go(); } });
    }
    function friendly(m) { return m.replace(/^Larz[A-Za-z]*Error:\s*/, "").replace(/\s*\(line \d+\)\s*$/, ""); }
    if (btn) btn.addEventListener("click", go);
    if (cfg.auto !== false) cfg.inputs.forEach(function (id) {
      var el = document.getElementById(id); if (!el) return;
      el.addEventListener(el.tagName === "SELECT" || el.type === "range" ? "change" : "input", function () { clearTimeout(timer); timer = setTimeout(go, 350); });
    });
    document.querySelectorAll("[data-preset]").forEach(function (b) {
      if (cfg.presetScope && !b.closest(cfg.presetScope)) return;
      b.addEventListener("click", function () {
        var p = JSON.parse(b.getAttribute("data-preset"));
        Object.keys(p).forEach(function (k) { var el = document.getElementById(k); if (el) el.value = p[k]; });
        document.querySelectorAll("[data-preset]").forEach(function (o) { o.classList.toggle("on", o === b); });
        go();
      });
    });
    warm();
    if (cfg.autorun !== false) go();
    return { go: go };
  }

  window.Cosmos = { run: run, boot: boot, warm: warm, stop: stop, parse: parse, lit: lit, str: str, int: int, num: num, sig: sig, duration: duration, length: length, pct: pct, esc: esc, sup: sup, bars: bars, plot: plot, tool: tool, info: function () { return engineInfo; } };
})();
