#!/usr/bin/env python3
"""
kb_cli.py – Command-line interface for the Economics Knowledge Base

Usage:
  python kb_cli.py list                        # List sources and wiki articles
  python kb_cli.py ingest "Title" "content"    # Add raw source (or @filepath)
  python kb_cli.py compile                     # Build wiki from raw/
  python kb_cli.py ask "your question"         # Q&A against wiki
  python kb_cli.py lint                        # Health check
"""
import sys, re, json, argparse
from pathlib import Path
import anthropic

BASE = Path(__file__).parent
RAW  = BASE / "raw";  RAW.mkdir(exist_ok=True)
WIKI = BASE / "wiki"; WIKI.mkdir(exist_ok=True)
client = anthropic.Anthropic()

def _call(prompt, system="", max_tokens=3000):
    r = client.messages.create(
        model="claude-sonnet-4-20250514", max_tokens=max_tokens,
        system=system or "You are a helpful expert assistant.",
        messages=[{"role":"user","content":prompt}])
    return r.content[0].text

def _raw_ctx():
    parts=[f"=== {p.name} ===\n{p.read_text()}" for p in sorted(RAW.glob("*")) if p.is_file()]
    return "\n\n".join(parts) or "(empty)"

def _wiki_ctx():
    parts=[f"=== {p.name} ===\n{p.read_text()}" for p in sorted(WIKI.glob("*.md"))]
    return "\n\n".join(parts) or "(empty)"

def cmd_list():
    print("\n── Raw Sources ──────────────────────")
    for p in sorted(RAW.glob("*")): print(f"  📄 {p.name}  ({p.stat().st_size}B)")
    print("\n── Wiki Articles ────────────────────")
    for p in sorted(WIKI.glob("*.md")): print(f"  📝 {p.name}  ({len(p.read_text().split())} words)")
    print()

def cmd_ingest(title, content):
    safe = re.sub(r"[^a-zA-Z0-9_\- ]","",title).strip().replace(" ","_")
    fname = f"{safe}.md"
    (RAW/fname).write_text(f"# {title}\n\n{content}\n")
    print(f"[OK] Saved → raw/{fname}")

def cmd_compile():
    raw = _raw_ctx()
    if raw == "(empty)": print("[WARN] No sources."); return
    print("Compiling wiki…")
    system = "You are a finance knowledge-base compiler. Return ONLY valid JSON."
    prompt = f"""Raw sources:\n\n{raw}\n\n
Write one focused Markdown article per concept using [[WikiLink]] cross-references.
Include INDEX.md. Return ONLY JSON: {{\"filename.md\": \"content\", ...}}"""
    rj = _call(prompt, system=system, max_tokens=4500)
    rj = re.sub(r"^```[a-z]*\n?","",rj.strip()); rj = re.sub(r"\n?```$","",rj.strip())
    for fname, content in json.loads(rj).items():
        (WIKI/fname).write_text(content); print(f"  Wrote wiki/{fname}")
    print("[OK] Done.")

def cmd_ask(q):
    wiki = _wiki_ctx()
    if "empty" in wiki: print("[WARN] Wiki empty. Compile first."); return
    print(f"\nQ: {q}\n")
    print(_call(f"Wiki:\n\n{wiki}\n\nQuestion: {q}",
                system="Finance research assistant. Cite wiki article names.", max_tokens=1200))

def cmd_lint():
    wiki = _wiki_ctx()
    if "empty" in wiki: print("[WARN] Wiki empty."); return
    print(_call(f"Wiki:\n\n{wiki}\n\nAudit: missing links, thin articles, gaps, quality score 1-10.",
                system="Rigorous knowledge-base auditor.", max_tokens=1200))

p = argparse.ArgumentParser(); sub = p.add_subparsers(dest="cmd")
sub.add_parser("list")
pi = sub.add_parser("ingest"); pi.add_argument("title"); pi.add_argument("content")
sub.add_parser("compile")
pa = sub.add_parser("ask"); pa.add_argument("question")
sub.add_parser("lint")
args = p.parse_args()

if   args.cmd == "list":    cmd_list()
elif args.cmd == "ingest":
    c = Path(args.content[1:]).read_text() if args.content.startswith("@") else args.content
    cmd_ingest(args.title, c)
elif args.cmd == "compile": cmd_compile()
elif args.cmd == "ask":     cmd_ask(args.question)
elif args.cmd == "lint":    cmd_lint()
else: p.print_help()
