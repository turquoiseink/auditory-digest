# SELECTION_SCHEMA.md — the exact JSON the model must write to state/selection.json

## Before writing anything: discovery, not just ranking

`state/candidates.json` already contains three tiers of deterministically
fetched papers:
- **Tier 1 (flagship journals)** — every recent article from Nature/Science/
  Cell/PNAS/eLife and their sister journals, guaranteed via two independent
  sources per journal. `pool: "flagship"`.
- **Tier 2 (deep bioRxiv scan)** — matched by title keyword OR watch-author
  name, full abstracts. `pool: "A"`, `cluster: "biorxiv-deep-scan"`.
- **Tier 3 (general search)** — keyword-clustered OpenAlex/PubMed/arXiv.
  `pool: "A"` or `"B"`.

**You are also expected to search on your own** — the deterministic tiers are
a safety net, not a ceiling. Check specific watch-authors' recent output,
follow up on something a Tier-1/2/3 candidate cites, or search for anything
your own judgment says is missing. If you find a paper this way that ISN'T
already in `candidates.json`:

1. **Never type its title/authors/abstract from memory.** Get its DOI or
   PMID, then run `python3 scripts/verify_identifier.py <doi-or-pmid>` —
   this fetches the CANONICAL record from CrossRef/PubMed and appends it to
   `state/model_discovered.json`. If it doesn't resolve, it's not added, and
   you should not write about it from memory instead — drop it or find the
   correct identifier.
2. Once you're done adding everything you found this way, run
   `python3 scripts/merge_discovered.py` — this folds verified entries into
   `state/candidates.json` with real `candidate_id`s (deduped against what's
   already there).
3. **Re-read the updated `state/candidates.json`** before writing
   `selection.json`, so you have the final candidate_id numbering.

## World knowledge: welcome for context, never for claims about a specific paper

You may and should use your own trained knowledge for **background,
definitions, and framing** — that's what makes the writing good instead of
mechanical. But **every claim about what a specific paper found, argued, or
reported must trace to its fetched abstract/full text** (or, for a canon
classic without fetchable text, be a well-established textbook-level
characterization, not an invented paper-style bullet). If you're not certain
you're describing the actual content of the actual paper in front of you —
say so, or don't include the claim. This is the rule that exists because a
past run once wrote detailed, confident-sounding bullets about the wrong
paper under a correct title. Never repeat that.

## The JSON contract

Write ONLY this object to `state/selection.json`. No markdown, no prose.

```json
{
  "editorial": "3-5 plain sentences: the day's throughline (or an honest note if thin) and one concrete tie to the reader's mouse or human work.",
  "sections": {
    "<one of the allowed section names>": [
      {"candidate_id": 4, "relevance_note": "2-4 sentences naming the exact finding/method/region that connects to their work."}
    ]
  },
  "paper_of_the_day": {
    "source": "new or canon",
    "candidate_id": 4,
    "canon_entry": null,
    "why_it_matters": ["3-4 full-thought bullets", "...", "..."],
    "read_plan": "A concrete ~20-minute reading plan: which sections to read in full, which to skim, what to focus on in each.",
    "reflection_question": "A two-part question building toward an actual experimental-design decision — not a single-clause comprehension check. Must be specific enough that answering it requires having engaged with the paper's method or finding."
  }
}
```

Allowed section names (use these EXACT strings; omit empty sections):
- `Chunking & sequence processing`
- `Auditory & prefrontal electrophysiology`
- `Behavioral & computational modeling`
- `Statistical learning & oddball`
- `Language, stroke & BCI`
- `Circuits, methods & population analysis`
- `Serendipity (outside my paradigm)` ← for genuinely field-defining Tier-1/3
  items outside the reader's paradigm; most days keep 0-2 here
- `Other notable`

## Rules
- At most 14 papers total across all sections.
- `paper_of_the_day.why_it_matters`: 2-5 bullets, none empty, each a full
  thought (1-2 sentences) — reading just the bullets should give a genuine
  sense of the paper's contribution.
- `paper_of_the_day.read_plan` and `.reflection_question` are both required.
  The reflection question should be two linked parts where possible (see the
  example in `profile.md`'s "Notes for the Paper-of-the-Day" section) — it
  will be rejected if it reads as a trivial single-clause recall question.
- If `context.json` rotation is `canon`: set `source="canon"`,
  `candidate_id=null`, and `canon_entry` = the next unserved line from
  `canon_reading_list.md` (verbatim).
- If rotation is `new`: set `source="new"` and a real `candidate_id`; leave
  `canon_entry` null. **The chosen paper must be peer-reviewed/published —
  never a preprint.** Check each candidate's `is_preprint` field. If none of
  today's strong candidates are peer-reviewed, set `source="canon"` instead,
  even on a "new" rotation day — never force a preprint pick.
- Relevance notes must be specific and never generic ("this is relevant to
  your field" is not acceptable) — see `profile.md`'s "Depth expected"
  section for length/content guidance.
- Use plain language for the paradigms ("the mouse sequence-discrimination
  task", "the human chunk-in-stream task") rather than chaining letter/region
  codes as shorthand, and gloss unfamiliar technical terms on first use — see
  `profile.md`'s "Language & naming conventions".
- If a candidate has `affiliation`/`country` populated, feel free to mention
  the lab or country in a relevance note when it's genuinely useful context
  (e.g. a known collaborator's lab, or a notable concentration of work from
  one group) — not as a routine addition to every entry.
