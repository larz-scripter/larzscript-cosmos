"""Small HTML builders for calculator forms."""
from common import esc
import json

def field(id, label, value, *, step="any", min=None, max=None, type="number", unit=None, hint=None):
    a = f' step="{step}"' if step else ""
    a += f' min="{min}"' if min is not None else ""
    a += f' max="{max}"' if max is not None else ""
    return (f'<div class="cs-field"><label for="{id}">{esc(label)}</label>'
            f'<input id="{id}" type="{type}" value="{esc(value)}"{a} inputmode="decimal" autocomplete="off">'
            + (f'<div class="u">{hint}</div>' if hint else "") + "</div>")

def select(id, label, options, selected=None, hint=None):
    o = "".join(f'<option value="{esc(v)}"{" selected" if (selected == v) else ""}>{esc(t)}</option>' for v, t in options)
    return (f'<div class="cs-field"><label for="{id}">{esc(label)}</label><select id="{id}">{o}</select>'
            + (f'<div class="u">{hint}</div>' if hint else "") + "</div>")

def chips(items, label="Try an example"):
    b = "".join(f'<button type="button" data-preset=\'{json.dumps(p)}\'>{esc(t)}</button>' for t, p in items)
    return f'<div class="cs-field" style="margin-top:14px"><label>{esc(label)}</label><div class="chips">{b}</div></div>'

def results(items):
    """items: (key, label, accent?) -> a grid of result cards filled by the page script (data-k / data-n)."""
    return '<div class="cs-res" id="cs-res" aria-live="polite">' + "".join(
        f'<div class="b{" acc" if acc else ""}"><div class="k">{esc(lbl)}</div><div class="v" data-k="{k}">—</div><div class="n" data-n="{k}"></div></div>'
        for k, lbl, acc in items) + "</div>"

def panel(title, inner, button="Calculate", note=None):
    return (f'<section class="cs-panel" id="tool"><h2>{esc(title)}</h2>{inner}'
            f'<button class="go" id="go" type="button">{esc(button)} →</button>'
            '<div class="cs-status" id="cs-status" role="status"></div></section>')

CODE = ('<details class="cs-more"><summary>Show the Larzscript program that just ran</summary>'
        '<pre class="cs-code" id="cs-code">Run a calculation to see the exact program.</pre>'
        '<p class="cs-note">This is the real program the page sent to the Larzscript interpreter (compiled to WebAssembly) in your browser. '
        'The library it imports is the same code the automated tests check.</p></details>')

def table(head, rows, cls="lz"):
    th = "".join(f"<th>{h}</th>" for h in head)
    tb = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<div class="cs-tbl"><table class="{cls}"><thead><tr>{th}</tr></thead><tbody>{tb}</tbody></table></div>'

# the small runtime every page script starts with
PAGE_PREFIX = r"""
var C=window.Cosmos;
function fill(tpl,types,vals){return tpl.replace(/\$\{(\w+)\}/g,function(_,k){var t=types[k],v=vals[k];
 if(t==='num')return C.lit(Number(v)); if(t==='int')return C.int(Number(v)); if(t==='str')return C.str(v); throw new Error('bad type '+t);});}
function $(id){return document.getElementById(id);}
function set(k,html){var e=document.querySelector('[data-k="'+k+'"]');if(e)e.innerHTML=html;}
function note(k,html){var e=document.querySelector('[data-n="'+k+'"]');if(e)e.innerHTML=html;}
function N(kv,k){return C.num(kv[k]);}
"""


def page_js(driver, types, inputs, render_body, extra="", prep="", button="go", timeout=None, autorun=True):
    """The page script: fills the driver template from the form, runs it in the worker, renders the result."""
    return PAGE_PREFIX + f"""
var TPL={json.dumps(driver)},TYPES={json.dumps(types)};
C.tool({{inputs:{json.dumps(inputs)},button:"{button}",code:"cs-code",{("timeout:%d," % timeout) if timeout else ""}{"" if autorun else "autorun:false,"}
 build:function(v){{{prep}return {{src:fill(TPL,TYPES,v)}};}},
 render:function(res,v){{var k=res.kv,rows=res.rows;{render_body}
 }}}});{extra}"""
