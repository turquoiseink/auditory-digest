import sys, os, json, importlib
sys.path.insert(0, 'src')
sys.path.insert(0, 'scripts')

ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
os.chdir(ROOT)

def reset():
    for f in ["state/candidates.json", "state/model_discovered.json"]:
        if os.path.exists(f): os.remove(f)

reset()

import verify_identifier as vi

# --- mock CrossRef: a real-looking DOI resolves ---
class FakeResp:
    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self._json = json_data
    def json(self):
        return self._json

CROSSREF_OK = {
    "message": {
        "title": ["Prefrontal cortex tracks transition probabilities in mice"],
        "abstract": "<jats:p>We recorded prelimbic single units during a go/no-go task.</jats:p>",
        "author": [{"given": "Alice", "family": "Smith"}, {"given": "Bob", "family": "Jones"}],
        "container-title": ["Neuron"],
        "published": {"date-parts": [[2026, 7, 1]]},
        "type": "journal-article",
    }
}
orig_get = vi.requests.get
vi.requests.get = lambda url, **kw: FakeResp(200, CROSSREF_OK)
rec = vi._from_crossref("10.1016/j.neuron.2026.01.001")
vi.requests.get = orig_get
assert rec is not None and rec["title"] == "Prefrontal cortex tracks transition probabilities in mice"
assert "prelimbic single units" in rec["abstract"]
assert rec["authors"] == ["Alice Smith", "Bob Jones"]
assert rec["is_preprint"] is False
print("PASS — CrossRef verification returns canonical metadata, not model-typed text")

# --- mock CrossRef: identifier does NOT resolve (404) ---
vi.requests.get = lambda url, **kw: FakeResp(404, {})
rec2 = vi._from_crossref("10.9999/nonexistent")
vi.requests.get = orig_get
assert rec2 is None
print("PASS — unresolvable DOI correctly returns None (nothing fabricated)")

# --- full CLI flow: verify_identifier.py appends to model_discovered.json ---
vi.requests.get = lambda url, **kw: FakeResp(200, CROSSREF_OK)
sys.argv = ["verify_identifier.py", "10.1016/j.neuron.2026.01.001"]
rc = vi.main()
vi.requests.get = orig_get
assert rc == 0
discovered = json.load(open("state/model_discovered.json", encoding="utf-8"))
assert len(discovered) == 1 and discovered[0]["title"].startswith("Prefrontal cortex")
print("PASS — verify_identifier.py CLI appends verified record to model_discovered.json")

# --- CLI flow: unverifiable identifier does not get added, exits nonzero ---
vi.requests.get = lambda url, **kw: FakeResp(404, {})
sys.argv = ["verify_identifier.py", "10.9999/fake"]
rc2 = vi.main()
vi.requests.get = orig_get
assert rc2 == 1
discovered2 = json.load(open("state/model_discovered.json", encoding="utf-8"))
assert len(discovered2) == 1, "should still be 1 — the bad identifier must not have been added"
print("PASS — CLI refuses to add an unverifiable identifier")

# --- merge_discovered.py: folds into candidates.json with real sequential ids ---
existing_candidates = [
    {"candidate_id": 0, "title": "Some other paper", "doi": "10.1/aaa"},
    {"candidate_id": 1, "title": "Another paper", "doi": "10.1/bbb"},
]
json.dump(existing_candidates, open("state/candidates.json", "w", encoding="utf-8"))

import merge_discovered as md
importlib.reload(md)
rc3 = md.main()
assert rc3 == 0
merged = json.load(open("state/candidates.json", encoding="utf-8"))
assert len(merged) == 3, f"expected 3 candidates after merge, got {len(merged)}"
assert merged[2]["candidate_id"] == 2
assert merged[2]["title"].startswith("Prefrontal cortex")
assert not os.path.exists("state/model_discovered.json"), "should be cleaned up after merge"
print("PASS — merge_discovered.py assigns sequential candidate_id and cleans up")

# --- merge_discovered.py: duplicate (same DOI as an existing candidate) is skipped ---
json.dump(existing_candidates, open("state/candidates.json", "w", encoding="utf-8"))
json.dump([{"title": "Some other paper", "doi": "10.1/aaa", "abstract": "dup"}],
          open("state/model_discovered.json", "w", encoding="utf-8"))
importlib.reload(md)
md.main()
merged2 = json.load(open("state/candidates.json", encoding="utf-8"))
assert len(merged2) == 2, f"duplicate should have been skipped, got {len(merged2)} candidates"
print("PASS — merge_discovered.py skips a duplicate already present via a deterministic tier")

reset()
print("\nAll verify/merge tests passed.")
