"""
Personal Knowledge Base System — Behavioral Finance 
"""

import os, json, re
from pathlib import Path
from flask import Flask, request, jsonify, render_template_string
import google.generativeai as genai

app   = Flask(__name__)
genai.configure(api_key="AIzaSyAKU4CuDDmG0S1ZWwmS2r8rS9_xSej7SOU")
MODEL = "gemini-2.0-flash"

BASE = Path(__file__).parent
RAW  = BASE / "raw";  RAW.mkdir(exist_ok=True)
WIKI = BASE / "wiki"; WIKI.mkdir(exist_ok=True)

# ── helpers ────────────────────────────────────────────────────────────────────

def _raw_ctx():
    parts = [f"=== {p.name} ===\n{p.read_text()}" for p in sorted(RAW.glob("*")) if p.is_file()]
    return "\n\n".join(parts) or "(empty)"

def _wiki_ctx():
    parts = [f"=== {p.name} ===\n{p.read_text()}" for p in sorted(WIKI.glob("*.md"))]
    return "\n\n".join(parts) or "(wiki empty – compile first)"

def _call(prompt: str, max_tokens: int = 3000) -> str:
    model = genai.GenerativeModel(MODEL)
    resp = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=0.3,
        ),
    )
    return resp.text

def _strip_fences(s: str) -> str:
    s = re.sub(r"^```[a-z]*\n?", "", s.strip())
    return re.sub(r"\n?```$", "", s.strip())

# ── core operations ────────────────────────────────────────────────────────────

def do_compile():
    raw = _raw_ctx()
    prompt = f"""You are a knowledge-base compiler for a finance research wiki.
Transform the raw source documents below into a set of linked Markdown articles.
Return ONLY valid JSON — no markdown fences, no prose outside the JSON.

Raw source documents:
{raw}

Instructions:
1. Identify distinct concepts and write one focused Markdown article per concept.
2. Use [[WikiLink]] syntax wherever one article should link to another.
3. Each article: brief definition, key points, important relationships, open questions.
4. Also write an INDEX.md that lists every article with a one-sentence description and [[links]].
5. Keep articles substantive but concise (150-300 words each).

Return ONLY a JSON object where keys are filenames (e.g. "Prospect_Theory.md") and values are the full Markdown content.
Example: {{"INDEX.md": "# Index\\n...", "Prospect_Theory.md": "# Prospect Theory\\n..."}}"""

    raw_json = _strip_fences(_call(prompt, max_tokens=4500))
    articles = json.loads(raw_json)
    for fname, content in articles.items():
        (WIKI / fname).write_text(content)
    return list(articles.keys())

def do_qa(question: str) -> str:
    wiki = _wiki_ctx()
    prompt = f"""You are a precise finance research assistant with access to a personal knowledge base wiki.
Answer questions using ONLY the provided wiki content.
Cite which wiki article supports each claim by naming it in your answer.
Be specific and concise.

Wiki knowledge base:
{wiki}

Question: {question}"""
    return _call(prompt, max_tokens=1200)

def do_lint() -> str:
    wiki = _wiki_ctx()
    if "empty" in wiki:
        return "Wiki is empty — compile first."
    prompt = f"""You are a rigorous knowledge-base auditor. Review this finance wiki and be specific and actionable.

Wiki:
{wiki}

Report on:
1. Missing cross-links between related concepts
2. Articles that are too thin or incomplete
3. Factual inconsistencies or contradictions
4. Gaps: important concepts not yet covered
5. Overall quality score 1-10 with justification

Format as a clean Markdown health report."""
    return _call(prompt, max_tokens=1200)

# ── HTML ───────────────────────────────────────────────────────────────────────

PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>FinanceKB – Behavioral Economics Knowledge Base</title>
<style>
:root{--bg:#0c0f1a;--surface:#131929;--card:#1a2238;--border:#252f45;--purple:#7c3aed;--purple-l:#a78bfa;--purple-d:#5b21b6;--text:#e2e8f0;--muted:#64748b;--code-bg:#0f1520}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;display:flex}
nav{width:240px;min-width:240px;background:var(--surface);border-right:1px solid var(--border);display:flex;flex-direction:column;padding:20px 12px;gap:2px}
.logo{padding:4px 10px 16px;border-bottom:1px solid var(--border);margin-bottom:8px}
.logo-title{font-size:1.05rem;font-weight:700;color:var(--purple-l)}
.logo-sub{font-size:.72rem;color:var(--muted);margin-top:2px}
.nav-section{font-size:.65rem;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);padding:10px 10px 4px}
.nav-btn{display:flex;align-items:center;gap:9px;padding:8px 10px;border-radius:7px;border:none;background:none;color:#94a3b8;cursor:pointer;font-size:.85rem;width:100%;text-align:left;transition:all .15s}
.nav-btn:hover{background:var(--card);color:var(--text)}
.nav-btn.active{background:var(--purple-d);color:#fff}
.nav-footer{margin-top:auto;padding-top:12px;border-top:1px solid var(--border);font-size:.7rem;color:var(--muted);line-height:1.6;padding-left:10px}
main{flex:1;padding:32px 36px;max-width:860px;overflow-y:auto}
.panel{display:none}.panel.active{display:block}
.pg-title{font-size:1.45rem;font-weight:700;margin-bottom:4px}
.pg-sub{color:var(--muted);font-size:.85rem;margin-bottom:24px}
.card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:20px;margin-bottom:16px}
.card-label{font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;color:var(--purple-l);font-weight:600;margin-bottom:10px}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px}
.stat{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:16px;text-align:center}
.stat-n{font-size:1.9rem;font-weight:700;color:var(--purple-l)}
.stat-l{font-size:.73rem;color:var(--muted);margin-top:3px}
.tags{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
.tag{background:var(--border);color:var(--purple-l);border-radius:4px;padding:2px 9px;font-size:.73rem;font-weight:500}
textarea,input[type=text]{width:100%;background:var(--bg);border:1px solid var(--border);border-radius:8px;color:var(--text);padding:10px 13px;font-size:.88rem;resize:vertical;transition:border-color .15s;font-family:inherit}
textarea:focus,input:focus{outline:none;border-color:var(--purple)}
.btn{padding:9px 20px;border-radius:8px;border:none;cursor:pointer;font-size:.85rem;font-weight:600;transition:all .15s;display:inline-flex;align-items:center;gap:7px}
.btn-p{background:var(--purple);color:#fff}.btn-p:hover{background:var(--purple-d)}
.btn-s{background:var(--border);color:var(--text)}.btn-s:hover{background:#2d3a55}
.btn:disabled{opacity:.45;cursor:not-allowed}
.btn-row{display:flex;justify-content:flex-end;margin-top:10px}
.out{background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:14px 16px;font-size:.84rem;line-height:1.75;white-space:pre-wrap;min-height:60px;max-height:500px;overflow-y:auto;font-family:inherit}
.file-row{display:flex;align-items:center;gap:10px;padding:9px 13px;background:var(--bg);border:1px solid var(--border);border-radius:7px;margin-bottom:6px;font-size:.83rem}
.file-ico{color:var(--purple-l)}.file-name{flex:1;font-weight:500}.file-sz{color:var(--muted);font-size:.75rem}
.wiki-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:20px}
.wiki-card{background:var(--card);border:1px solid var(--border);border-radius:9px;padding:14px;cursor:pointer;transition:border-color .15s}
.wiki-card:hover{border-color:var(--purple)}
.wiki-card-name{font-weight:600;font-size:.88rem;color:var(--purple-l)}
.wiki-card-preview{font-size:.76rem;color:var(--muted);margin-top:5px;line-height:1.45;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}
.spin{display:inline-block;width:13px;height:13px;border:2px solid #ffffff44;border-top-color:#fff;border-radius:50%;animation:sp .6s linear infinite}
@keyframes sp{to{transform:rotate(360deg)}}
.badge{display:inline-flex;align-items:center;gap:5px;font-size:.76rem;padding:3px 10px;border-radius:20px;font-weight:500}
.badge-ok{background:#064e3b;color:#6ee7b7}
.qa-entry{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:16px;margin-bottom:14px}
.qa-q{color:var(--purple-l);font-weight:600;font-size:.88rem;margin-bottom:10px}
</style>
</head>
<body>
<nav>
  <div class="logo">
    <div class="logo-title">📈 FinanceKB</div>
    <div class="logo-sub">Behavioral Finance Wiki</div>
  </div>
  <div class="nav-section">Knowledge Base</div>
  <button class="nav-btn active" data-panel="dashboard" onclick="nav(this)">📊 Dashboard</button>
  <button class="nav-btn" data-panel="ingest" onclick="nav(this)">📥 Ingest Sources</button>
  <button class="nav-btn" data-panel="compile" onclick="nav(this)">⚙️ Compile Wiki</button>
  <button class="nav-btn" data-panel="wiki" onclick="nav(this)">📚 Browse Wiki</button>
  <div class="nav-section">Tools</div>
  <button class="nav-btn" data-panel="qa" onclick="nav(this)">💬 Ask Questions</button>
  <button class="nav-btn" data-panel="lint" onclick="nav(this)">🔍 Health Check</button>
  <div class="nav-footer">INDENG 231 · Project 2<br>Topic: Behavioral Finance<br>&amp; Market Anomalies<br><br>Powered by Gemini (free)</div>
</nav>
<main>

<!-- DASHBOARD -->
<div id="panel-dashboard" class="panel active">
  <div class="pg-title">Dashboard</div>
  <div class="pg-sub">Overview of your Behavioral Finance knowledge base</div>
  <div class="stats">
    <div class="stat"><div class="stat-n" id="s-raw">–</div><div class="stat-l">Raw Sources</div></div>
    <div class="stat"><div class="stat-n" id="s-wiki">–</div><div class="stat-l">Wiki Articles</div></div>
    <div class="stat"><div class="stat-n" id="s-words">–</div><div class="stat-l">Total Words</div></div>
  </div>
  <div class="card">
    <div class="card-label">About This Knowledge Base</div>
    <p style="font-size:.87rem;line-height:1.75;color:#cbd5e0">
      This system implements Karpathy's LLM-powered personal knowledge base for
      <strong style="color:var(--purple-l)">Behavioral Economics &amp; Market Anomalies</strong>.
      Raw academic sources are ingested, compiled into a linked Markdown wiki by Gemini, and queried
      using natural-language Q&amp;A — no manual writing required.
    </p>
    <div class="tags">
      <span class="tag">Prospect Theory</span><span class="tag">EMH</span>
      <span class="tag">Momentum</span><span class="tag">Disposition Effect</span>
      <span class="tag">CAPM</span><span class="tag">Factor Investing</span>
      <span class="tag">Investor Sentiment</span><span class="tag">Limits to Arbitrage</span>
    </div>
  </div>
  <div class="card">
    <div class="card-label">Workflow</div>
    <ol style="font-size:.84rem;line-height:2.1;color:#cbd5e0;padding-left:18px">
      <li>Add raw sources (papers, notes) in <strong>Ingest Sources</strong></li>
      <li>Click <strong>Compile Wiki</strong> — Gemini writes linked .md articles</li>
      <li>Read articles in <strong>Browse Wiki</strong> (also Obsidian-compatible)</li>
      <li>Ask technical questions in <strong>Ask Questions</strong></li>
      <li>Find gaps with <strong>Health Check</strong></li>
    </ol>
  </div>
</div>

<!-- INGEST -->
<div id="panel-ingest" class="panel">
  <div class="pg-title">Ingest Sources</div>
  <div class="pg-sub">Paste papers, notes, or article summaries as raw Markdown</div>
  <div class="card">
    <div class="card-label">Add New Source</div>
    <div style="display:flex;flex-direction:column;gap:10px">
      <input type="text" id="i-title" placeholder="Source title (e.g. Shiller 1981 Excess Volatility)">
      <textarea id="i-body" rows="9" placeholder="Paste content here — paper summary, notes, key findings..."></textarea>
      <div class="btn-row">
        <button class="btn btn-p" onclick="saveSource()">
          <span id="sp-add" style="display:none" class="spin"></span>💾 Save Source
        </button>
      </div>
      <div id="add-msg"></div>
    </div>
  </div>
  <div class="card">
    <div class="card-label">Existing Raw Sources</div>
    <div id="raw-list">Loading…</div>
  </div>
</div>

<!-- COMPILE -->
<div id="panel-compile" class="panel">
  <div class="pg-title">Compile Wiki</div>
  <div class="pg-sub">Have Gemini read all raw sources and write linked wiki articles</div>
  <div class="card">
    <div class="card-label">What Happens</div>
    <p style="font-size:.84rem;line-height:1.75;color:#cbd5e0">
      Gemini reads every file in <code style="background:var(--code-bg);padding:1px 5px;border-radius:3px">raw/</code>,
      identifies key concepts, and writes one focused Markdown article per concept using
      <code style="background:var(--code-bg);padding:1px 5px;border-radius:3px">[[WikiLink]]</code> cross-references.
      An <code style="background:var(--code-bg);padding:1px 5px;border-radius:3px">INDEX.md</code> is auto-generated.
      All files are saved to <code style="background:var(--code-bg);padding:1px 5px;border-radius:3px">wiki/</code>
      and are Obsidian-compatible.
    </p>
  </div>
  <div class="card">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">
      <div>
        <div class="card-label" style="margin-bottom:3px">Run Compilation</div>
        <div id="raw-count" style="font-size:.8rem;color:var(--muted)">– source files</div>
      </div>
      <button class="btn btn-p" id="btn-compile" onclick="runCompile()">
        <span id="sp-compile" style="display:none" class="spin"></span>⚙️ Compile Now
      </button>
    </div>
    <div id="compile-out" class="out" style="display:none"></div>
  </div>
</div>

<!-- WIKI -->
<div id="panel-wiki" class="panel">
  <div class="pg-title">Browse Wiki</div>
  <div class="pg-sub">Read the LLM-compiled linked Markdown articles</div>
  <div class="wiki-grid" id="wiki-grid">Loading…</div>
  <div id="wiki-viewer" style="display:none">
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
        <strong id="wiki-fn" style="color:var(--purple-l);font-size:.95rem"></strong>
        <button class="btn btn-s" onclick="closeWiki()">✕ Close</button>
      </div>
      <div id="wiki-body" class="out"></div>
    </div>
  </div>
</div>

<!-- Q&A -->
<div id="panel-qa" class="panel">
  <div class="pg-title">Ask Questions</div>
  <div class="pg-sub">Natural-language queries answered from the compiled wiki</div>
  <div class="card">
    <div class="card-label">Question</div>
    <textarea id="qa-q" rows="3" placeholder="e.g. How does the disposition effect relate to prospect theory? What explains the momentum anomaly?"></textarea>
    <div class="btn-row" style="margin-top:10px">
      <button class="btn btn-p" id="btn-qa" onclick="ask()">
        <span id="sp-qa" style="display:none" class="spin"></span>💬 Ask
      </button>
    </div>
  </div>
  <div id="qa-hist"></div>
</div>

<!-- LINT -->
<div id="panel-lint" class="panel">
  <div class="pg-title">Wiki Health Check</div>
  <div class="pg-sub">Gemini audits the wiki for gaps, missing links, and improvements</div>
  <div class="card">
    <div style="display:flex;justify-content:space-between;align-items:center">
      <p style="font-size:.84rem;color:#cbd5e0;max-width:480px">
        Checks for thin articles, missing cross-links, contradictions, and suggests new articles
        to fill knowledge gaps in the behavioral finance domain.
      </p>
      <button class="btn btn-p" id="btn-lint" onclick="runLint()">
        <span id="sp-lint" style="display:none" class="spin"></span>🔍 Run Audit
      </button>
    </div>
  </div>
  <div id="lint-card" style="display:none" class="card">
    <div class="card-label">Audit Report</div>
    <div id="lint-out" class="out"></div>
  </div>
</div>

</main>
<script>
function nav(btn){
  document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b=>b.classList.remove('active'));
  const name=btn.dataset.panel;
  document.getElementById('panel-'+name).classList.add('active');
  btn.classList.add('active');
  if(name==='dashboard')loadStats();
  if(name==='ingest')loadRaw();
  if(name==='wiki')loadWikiGrid();
  if(name==='compile')loadRawCount();
}
async function loadStats(){
  const d=await(await fetch('/api/stats')).json();
  document.getElementById('s-raw').textContent=d.raw;
  document.getElementById('s-wiki').textContent=d.wiki;
  document.getElementById('s-words').textContent=(d.words/1000).toFixed(1)+'k';
}
loadStats();
async function loadRaw(){
  const d=await(await fetch('/api/raw')).json();
  const el=document.getElementById('raw-list');
  if(!d.files.length){el.innerHTML='<div style="color:var(--muted);font-size:.83rem">No sources yet.</div>';return;}
  el.innerHTML=d.files.map(f=>`<div class="file-row"><span class="file-ico">📄</span><span class="file-name">${f.name}</span><span class="file-sz">${(f.size/1024).toFixed(1)} KB</span></div>`).join('');
}
async function saveSource(){
  const title=document.getElementById('i-title').value.trim();
  const body=document.getElementById('i-body').value.trim();
  if(!title||!body){alert('Title and content required.');return;}
  const btn=event.currentTarget;btn.disabled=true;
  document.getElementById('sp-add').style.display='inline-block';
  const d=await(await fetch('/api/raw',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title,content:body})})).json();
  btn.disabled=false;document.getElementById('sp-add').style.display='none';
  document.getElementById('i-title').value='';document.getElementById('i-body').value='';
  document.getElementById('add-msg').innerHTML=`<span class="badge badge-ok">✓ Saved as ${d.filename}</span>`;
  loadRaw();
}
async function loadRawCount(){
  const d=await(await fetch('/api/stats')).json();
  document.getElementById('raw-count').textContent=d.raw+' source file(s) ready';
}
async function runCompile(){
  const btn=document.getElementById('btn-compile');
  btn.disabled=true;document.getElementById('sp-compile').style.display='inline-block';
  const out=document.getElementById('compile-out');out.style.display='block';
  out.textContent='Compiling… Gemini is reading your sources and writing articles. This takes ~20s…';
  try{
    const d=await(await fetch('/api/compile',{method:'POST'})).json();
    out.textContent=d.error?'Error: '+d.error:'✓ Wiki compiled! Articles written:\n\n'+d.files.join('\n');
  }catch(e){out.textContent='Error: '+e;}
  btn.disabled=false;document.getElementById('sp-compile').style.display='none';
}
async function loadWikiGrid(){
  const d=await(await fetch('/api/wiki')).json();
  const el=document.getElementById('wiki-grid');
  if(!d.files.length){el.innerHTML='<div style="color:var(--muted);font-size:.84rem;grid-column:1/-1">Wiki is empty — compile first.</div>';return;}
  el.innerHTML=d.files.map(f=>`<div class="wiki-card" onclick="openWiki('${f.name}')"><div class="wiki-card-name">📄 ${f.name}</div><div class="wiki-card-preview">${esc(f.preview)}</div></div>`).join('');
}
async function openWiki(name){
  const d=await(await fetch('/api/wiki/'+encodeURIComponent(name))).json();
  document.getElementById('wiki-fn').textContent=name;
  document.getElementById('wiki-body').textContent=d.content;
  const v=document.getElementById('wiki-viewer');v.style.display='block';
  v.scrollIntoView({behavior:'smooth'});
}
function closeWiki(){document.getElementById('wiki-viewer').style.display='none';}
async function ask(){
  const q=document.getElementById('qa-q').value.trim();if(!q)return;
  const btn=document.getElementById('btn-qa');btn.disabled=true;
  document.getElementById('sp-qa').style.display='inline-block';
  document.getElementById('qa-q').value='';
  const hist=document.getElementById('qa-hist');
  const entry=document.createElement('div');entry.className='qa-entry';
  entry.innerHTML=`<div class="qa-q">Q: ${esc(q)}</div><div class="out">Thinking…</div>`;
  hist.prepend(entry);
  const d=await(await fetch('/api/qa',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q})})).json();
  entry.querySelector('.out').textContent=d.answer||d.error;
  btn.disabled=false;document.getElementById('sp-qa').style.display='none';
}
async function runLint(){
  const btn=document.getElementById('btn-lint');btn.disabled=true;
  document.getElementById('sp-lint').style.display='inline-block';
  const card=document.getElementById('lint-card');card.style.display='block';
  const out=document.getElementById('lint-out');out.textContent='Auditing wiki…';
  const d=await(await fetch('/api/lint',{method:'POST'})).json();
  out.textContent=d.report||d.error;
  btn.disabled=false;document.getElementById('sp-lint').style.display='none';
}
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
</script>
</body>
</html>"""

# ── routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index(): return PAGE

@app.route("/api/stats")
def stats():
    raw  = list(RAW.glob("*"))
    wiki = list(WIKI.glob("*.md"))
    words = sum(len(f.read_text().split()) for f in wiki)
    return jsonify(raw=len(raw), wiki=len(wiki), words=words)

@app.route("/api/raw", methods=["GET"])
def list_raw():
    return jsonify(files=[{"name":p.name,"size":p.stat().st_size}
                           for p in sorted(RAW.glob("*")) if p.is_file()])

@app.route("/api/raw", methods=["POST"])
def add_raw():
    data = request.get_json()
    safe = re.sub(r"[^a-zA-Z0-9_\- ]", "", data["title"]).strip().replace(" ", "_")
    fname = f"{safe}.md"
    (RAW / fname).write_text(f"# {data['title']}\n\n{data['content']}\n")
    return jsonify(filename=fname)

@app.route("/api/compile", methods=["POST"])
def compile_route():
    try:    return jsonify(files=do_compile())
    except Exception as e: return jsonify(error=str(e)), 500

@app.route("/api/wiki")
def list_wiki():
    files = []
    for p in sorted(WIKI.glob("*.md")):
        text = p.read_text(); preview = ""
        for line in text.splitlines():
            s = line.strip()
            if s and not s.startswith("#"): preview = s[:130]; break
        files.append({"name": p.name, "preview": preview})
    return jsonify(files=files)

@app.route("/api/wiki/<fname>")
def get_wiki(fname):
    p = WIKI / fname
    return jsonify(content=p.read_text()) if p.exists() else (jsonify(error="not found"), 404)

@app.route("/api/qa", methods=["POST"])
def qa_route():
    try:    return jsonify(answer=do_qa(request.get_json()["question"]))
    except Exception as e: return jsonify(error=str(e)), 500

@app.route("/api/lint", methods=["POST"])
def lint_route():
    try:    return jsonify(report=do_lint())
    except Exception as e: return jsonify(error=str(e)), 500

if __name__ == "__main__":
    app.run(debug=False, port=5050)
