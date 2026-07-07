# DEEPDIVE_SCHEMA.md — state/deepdive.json

Only written on "new" Paper-of-the-Day days (canon days skip this step
entirely — `process_selection.py` won't create `deepdive_input.json` then).

Read `state/deepdive_input.json` first — it has the paper's title, abstract,
full text if fetched (`full_text_available: true/false`), and the current
bullets/read-plan/question from the selection step as a starting point.

**If `full_text_available` is false and the Elicit connector is available**,
use it before writing anything: query Elicit for this paper (by title or DOI)
and ask specifically for its methods, key results, and any figures/comparisons
relevant to auditory sequence processing, prefrontal cortex, or sequence
decoding — Elicit can extract grounded, specific findings from the full paper
even when our own fetch couldn't get the text. Use what it returns as your
source material instead of the abstract alone. If Elicit has nothing useful
either, fall back to the abstract and hedge claims appropriately.

**Same world-knowledge rule as selection**: background/definitions/framing
from your own knowledge are welcome; any claim about what THIS paper found
must trace to the fetched text (or Elicit's grounded extraction) — never
written from a general impression of what a paper like this "probably" says.

Write ONLY this object to `state/deepdive.json`. No markdown, no prose.

```json
{
  "why_it_matters": ["3-4 full-thought bullets naming specific methods, figures, or results and how each connects to the reader's mouse or human paradigm"],
  "read_plan": "A concrete ~20-minute reading plan: which sections to read in full, which to skim, and what to focus on in each — refine the selection step's version now that you may have more than the abstract.",
  "reflection_question": "A two-part question building toward an actual experimental-design decision, tied to the reader's own work, ending in ?",
  "corresponding_author": "Optional — only include if reading the full text/Elicit surfaced a more accurate name than the selection step already had; omit or leave empty otherwise",
  "university": "Optional, same rule as above",
  "country": "Optional, same rule as above"
}
```

Guidance:
- Write with real depth: each bullet a full thought (1-2 sentences), not a
  fragment. See `profile.md`'s "Depth expected" section.
- Use plain language for the paradigms and gloss technical terms on first
  use. See `profile.md`'s "Language & naming conventions".
- If `full_text_available` is true, use it — cite specific figures/sections
  where possible, not just the abstract's framing.
- If `full_text_available` is false, work from the abstract (or Elicit's
  extraction), and keep claims appropriately hedged.
- This is meant to be a genuine improvement over the selection step's
  original bullets/read-plan/question — take the extra context and produce
  something more specific, not just a rephrase. If nothing here would
  improve on the current version, it's fine to return it close to
  unchanged — never fabricate specifics to seem more thorough.
