import sys, os, json, subprocess, shutil, datetime as dt
sys.path.insert(0, 'src')

ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
os.chdir(ROOT)

def reset_state():
    for f in ["state/reading_log.xlsx", "state/candidates.json", "state/context.json",
              "state/selection.json", "state/deepdive.json", "state/deepdive_input.json",
              "state/resolved.json", "state/attempt.json"]:
        if os.path.exists(f): os.remove(f)
    if os.path.exists("state/archive"): shutil.rmtree("state/archive")
    json.dump({"served": []}, open("state/canon_progress.json", "w"))
    json.dump([], open("state/run_log.json", "w"))

def write_candidates(rotation="new"):
    candidates = [
        {"candidate_id": 0, "title": "PL tracks BC-vs-CB transitions in mice",
         "abstract": "Neuropixels recordings in prelimbic cortex during a go/no-go tone sequence task.",
         "venue": "bioRxiv", "date": "2026-07-02", "doi": "10.1/aaa",
         "url": "https://doi.org/10.1/aaa", "authors": ["A. Smith"],
         "pool": "A", "source_api": "bioRxiv"},
        {"candidate_id": 1, "title": "Cross-temporal decoding of chunk boundaries in human IFG",
         "abstract": "Utah array recordings from IFG during chunk-in-stream detection.",
         "venue": "Nature Neuroscience", "date": "2026-06-30", "doi": "10.1/bbb",
         "url": "https://doi.org/10.1/bbb", "authors": ["C. Kim"],
         "pool": "A", "source_api": "PubMed"},
    ]
    json.dump(candidates, open("state/candidates.json", "w"))
    json.dump({"date": dt.date.today().isoformat(), "rotation": rotation,
              "canon_served": [], "sources": {"OpenAlex (Tier 3)": {"ok": True, "count": 2}}},
             open("state/context.json", "w"))
    json.dump({"count": 0}, open("state/attempt.json", "w"))
    return candidates

def run(cmd):
    return subprocess.run([sys.executable] + cmd, capture_output=True, text=True)


def assert_valid_pdf(path, min_bytes=2000):
    """A real, built PDF is at least a few KB and starts with the PDF magic
    bytes. This catches the class of bug where render_digest silently fails
    to call doc.build() but the file still 'exists' (reportlab may create an
    empty file the moment SimpleDocTemplate is constructed, before .build()
    ever runs) — plain os.path.exists() alone does not catch that."""
    assert os.path.exists(path), f"{path} does not exist"
    size = os.path.getsize(path)
    assert size >= min_bytes, f"{path} is only {size} bytes — render likely did not complete"
    with open(path, "rb") as f:
        assert f.read(5) == b"%PDF-", f"{path} does not start with the PDF magic bytes"

VALID = {
    "editorial": "Two on-paradigm papers today connecting to your BC/CB and IFG work.",
    "sections": {
        "Auditory & prefrontal electrophysiology": [
            {"candidate_id": 0, "relevance_note": "PL units track BC-vs-CB transitions.",
             "corresponding_author": "A. Smith", "university": "Some University", "country": "USA"}],
        "Language, stroke & BCI": [
            {"candidate_id": 1, "relevance_note": "IFG cross-temporal chunk decoding.",
             "corresponding_author": "", "university": "", "country": ""}],
    },
    "paper_of_the_day": {"source": "new", "candidate_id": 1, "canon_entry": None,
        "why_it_matters": ["A", "B", "C"],
        "reflection_question": "How would their cross-temporal decoding window need to change for your mouse task's order-controlled timing?",
        "read_plan": "Read the Introduction and Methods in full; skim Results; read the Discussion's final paragraphs.",
        "corresponding_author": "C. Kim", "university": "MIT", "country": "USA"},
}

print("=== TEST 1: valid selection on first attempt (new-day POTD) ===")
reset_state()
write_candidates(rotation="new")
json.dump(VALID, open("state/selection.json", "w"))
r = run(["src/process_selection.py"])
print(" ", r.stdout.strip().splitlines()[0])
assert r.returncode == 0, r.stdout
assert os.path.exists("state/deepdive_input.json"), "expected deep-dive input for a new-day POTD"
# model writes deepdive.json
json.dump({"why_it_matters": ["deep A", "deep B", "deep C"],
           "reflection_question": "How would their cross-temporal decoding window need to change for your mouse task's order-controlled timing?", "read_plan": "Read the Introduction and Methods in full; skim Results; read the Discussion's final paragraphs."}, open("state/deepdive.json", "w", encoding="utf-8"))
def pdf_path_from_stdout(stdout):
    for line in stdout.splitlines():
        if line.startswith("OUTPUT_PDF="):
            return line.split("=", 1)[1]
    return None


r2 = run(["src/finalize.py"])
print(" ", r2.stdout.strip().splitlines()[-1])
assert r2.returncode == 0, r2.stdout
assert "OUTPUT_PDF=" in r2.stdout
assert_valid_pdf(pdf_path_from_stdout(r2.stdout))
xlsx_seen = __import__("reading_log").load_seen("state/reading_log.xlsx")
assert len(xlsx_seen) == 2
print("  PASS: attempt 1 valid -> deep-dive -> finalize -> real PDF + 2 log rows")

print("=== TEST 2: re-run same day -> dedupe (no new rows) ===")
write_candidates(rotation="new")  # re-fetch would normally seen-filter; simulate same 2 papers still present
json.dump(VALID, open("state/selection.json", "w"))
run(["src/process_selection.py"])
json.dump({"why_it_matters": ["x", "y"], "reflection_question": "How would their cross-temporal decoding window need to change for your mouse task's order-controlled timing?", "read_plan": "Read the Introduction and Methods in full; skim Results; read the Discussion's final paragraphs."}, open("state/deepdive.json", "w", encoding="utf-8"))
run(["src/finalize.py"])
xlsx_seen2 = __import__("reading_log").load_seen("state/reading_log.xlsx")
assert len(xlsx_seen2) == 2, f"expected still 2, got {len(xlsx_seen2)}"
print("  PASS: no duplicate rows on re-run")

print("=== TEST 3: hard-capped retries — model NEVER produces valid JSON ===")
reset_state()
candidates = write_candidates(rotation="new")
BAD = {"editorial": "", "sections": {"Nope": [{"candidate_id": 99, "relevance_note": ""}]},
       "paper_of_the_day": {"source": "nonsense"}}
codes = []
for i in range(5):  # simulate the routine stubbornly retrying 5 times
    json.dump(BAD, open("state/selection.json", "w"))
    r = run(["src/process_selection.py"])
    codes.append(r.returncode)
print("  exit codes across 5 attempts:", codes)
# 3 total submissions allowed: attempts 1-2 say "fix and retry" (1),
# attempt 3 is the last chance and correctly says "exhausted" (2), not a 4th invite.
assert codes == [1, 1, 2, 2, 2], f"expected [1,1,2,2,2], got {codes}"
r = run(["src/finalize.py", "--fallback"])
assert r.returncode == 0 and "OUTPUT_PDF=" in r.stdout
assert_valid_pdf(pdf_path_from_stdout(r.stdout))
print("  PASS: cap enforced at exactly 3 real attempts regardless of retries; fallback works with a real PDF")

print("=== TEST 4: canon day skips deep-dive entirely ===")
reset_state()
write_candidates(rotation="canon")
CANON_SEL = {**VALID, "paper_of_the_day": {"source": "canon", "candidate_id": None,
             "canon_entry": "Saffran, Aslin & Newport (1996, Science)",
             "why_it_matters": ["A", "B"],
             "reflection_question": "How would their cross-temporal decoding window need to change for your mouse task's order-controlled timing?",
             "read_plan": "Read the Introduction and Methods in full; skim Results; read the Discussion's final paragraphs.",
             "corresponding_author": "", "university": "", "country": ""}}
json.dump(CANON_SEL, open("state/selection.json", "w", encoding="utf-8"))
r = run(["src/process_selection.py"])
assert r.returncode == 0
assert not os.path.exists("state/deepdive_input.json"), "canon day should skip deep-dive input"
r2 = run(["src/finalize.py"])
assert r2.returncode == 0 and "OUTPUT_PDF=" in r2.stdout
assert_valid_pdf(pdf_path_from_stdout(r2.stdout))
print("  PASS: canon day path (no full-text deep-dive) works end-to-end with a real PDF")

print("\nALL ROUTINE-FLOW INTEGRATION TESTS PASSED")
