import sys
sys.path.insert(0, 'src')
from validate_selection import validate, validate_deepdive

candidates = [{"title": f"paper {i}"} for i in range(5)]

GOOD_REFLECTION = ("How would their cross-temporal decoding window need to change to "
                    "resolve your mouse task's order-controlled distractor timing?")
GOOD_READ_PLAN = ("Read the Introduction and Methods in full; skim the Results figures; "
                   "read the final two paragraphs of the Discussion.")

# --- a fully valid selection ---
good = {
    "editorial": "Today's batch leans on prefrontal sequence coding. The IFG decoding paper is worth your time. It maps onto your human chunk-in-stream task.",
    "sections": {
        "Auditory & prefrontal electrophysiology": [
            {"candidate_id": 0, "relevance_note": "PL single units track order-related transition statistics in a design close to my own."}
        ],
        "Serendipity (outside my paradigm)": [
            {"candidate_id": 3, "relevance_note": "Major new cortical recording method, field-defining."}
        ],
    },
    "paper_of_the_day": {
        "source": "new", "candidate_id": 0, "canon_entry": None,
        "why_it_matters": ["Fig 3 shows cross-temporal generalization",
                            "Their SVM pipeline suits your population analysis",
                            "Contrasts template-matching vs statistical learning"],
        "reflection_question": GOOD_REFLECTION,
        "read_plan": GOOD_READ_PLAN,
    },
}
ok, errs = validate(good, candidates)
assert ok, errs
print("PASS — valid selection accepted")

# --- bad candidate_id ---
bad = {**good, "sections": {"Other notable": [{"candidate_id": 99, "relevance_note": "x"}]}}
ok, errs = validate(bad, candidates)
assert not ok and any("out of range" in e for e in errs), errs
print("PASS — out-of-range candidate_id rejected:", [e for e in errs if 'range' in e][0])

# --- bad section name ---
bad = {**good, "sections": {"Auditory Stuff": [{"candidate_id": 0, "relevance_note": "x"}]}}
ok, errs = validate(bad, candidates)
assert not ok and any("not allowed" in e for e in errs)
print("PASS — invalid section name rejected")

# --- missing reflection question ---
bad = {**good, "paper_of_the_day": {**good["paper_of_the_day"], "reflection_question": ""}}
ok, errs = validate(bad, candidates)
assert not ok and any("reflection_question" in e for e in errs)
print("PASS — empty reflection_question rejected")

# --- reflection question without '?' ---
bad = {**good, "paper_of_the_day": {**good["paper_of_the_day"], "reflection_question": "This is a statement long enough to pass the length floor easily."}}
ok, errs = validate(bad, candidates)
assert not ok and any("should be a question" in e for e in errs)
print("PASS — non-question reflection rejected")

# --- reflection question too short/trivial ---
bad = {**good, "paper_of_the_day": {**good["paper_of_the_day"], "reflection_question": "What year?"}}
ok, errs = validate(bad, candidates)
assert not ok and any("too short/trivial" in e for e in errs)
print("PASS — trivially short reflection question rejected")

# --- missing read_plan ---
bad = {**good, "paper_of_the_day": {**good["paper_of_the_day"], "read_plan": ""}}
ok, errs = validate(bad, candidates)
assert not ok and any("read_plan" in e for e in errs)
print("PASS — missing read_plan rejected")

# --- canon POTD needs canon_entry ---
bad = {**good, "paper_of_the_day": {**good["paper_of_the_day"], "source": "canon", "candidate_id": None, "canon_entry": ""}}
ok, errs = validate(bad, candidates)
assert not ok and any("canon_entry required" in e for e in errs)
print("PASS — canon POTD without canon_entry rejected")

# --- too few bullets ---
bad = {**good, "paper_of_the_day": {**good["paper_of_the_day"], "why_it_matters": ["only one"]}}
ok, errs = validate(bad, candidates)
assert not ok and any("why_it_matters" in e for e in errs)
print("PASS — too-few bullets rejected")

# --- empty editorial ---
bad = {**good, "editorial": "   "}
ok, errs = validate(bad, candidates)
assert not ok and any("editorial" in e for e in errs)
print("PASS — empty editorial rejected")

# --- preprint as Paper of the Day rejected ---
candidates_with_preprint = [
    {"title": "paper 0", "is_preprint": True, "source_api": "bioRxiv", "venue": "bioRxiv"},
    {"title": "paper 1"},
]
minimal = {
    "editorial": good["editorial"],
    "sections": {"Other notable": [{"candidate_id": 1, "relevance_note": "x"}]},
    "paper_of_the_day": {"source": "new", "candidate_id": 0, "canon_entry": None,
                          "why_it_matters": ["a", "b"], "reflection_question": GOOD_REFLECTION,
                          "read_plan": GOOD_READ_PLAN},
}
ok, errs = validate(minimal, candidates_with_preprint)
assert not ok and any("is a preprint" in e for e in errs), errs
print("PASS — preprint rejected as Paper of the Day:", [e for e in errs if 'preprint' in e][0])

# --- non-preprint candidate for POTD is fine ---
minimal2 = {**minimal, "paper_of_the_day": {**minimal["paper_of_the_day"], "candidate_id": 1}}
ok2, errs2 = validate(minimal2, candidates_with_preprint)
assert ok2, errs2
print("PASS — non-preprint candidate accepted as Paper of the Day")

# --- deep-dive validator: same rules, standalone ---
good_dd = {"why_it_matters": ["a solid bullet", "another solid bullet"],
           "reflection_question": GOOD_REFLECTION, "read_plan": GOOD_READ_PLAN}
ok3, errs3 = validate_deepdive(good_dd)
assert ok3, errs3
print("PASS — valid deep-dive JSON accepted")

bad_dd = {"why_it_matters": ["a"], "reflection_question": "short?", "read_plan": ""}
ok4, errs4 = validate_deepdive(bad_dd)
assert not ok4 and len(errs4) >= 2  # too few bullets, short question, AND missing read_plan
print("PASS — invalid deep-dive JSON rejected with multiple specific errors")

print("\nAll validator tests passed.")
