# Auditory Grouping Daily

A daily PDF research digest + running reading-log spreadsheet, for a
cognitive/systems neuroscience PhD in auditory chunking. Runs on your
existing Claude Pro subscription via a **Claude Code Routine** — no API key,
no separate billing. Discovers new papers across three independent tiers,
curates them against your research profile with real depth (institution,
country, corresponding lab), picks a genuinely-published Paper of the Day
with a 20-minute read plan and a reflection question, and syncs everything
to Google Drive.

## The three-tier discovery architecture

**Tier 1 — guaranteed flagship-journal coverage ("no miss").** Every recent
article from Nature (+ Neuroscience/Communications/Human Behaviour/Reviews),
Science (+ Advances), Cell (+ Neuron/Current Biology/iScience/Cell Reports),
Scientific Reports, PNAS, eLife, Trends in Cognitive Sciences, Trends in
Neurosciences, Annual Review of Neuroscience, and Journal of Neuroscience.
Each journal is checked via **two independent sources** — its own RSS/Atom
feed AND a PubMed query scoped to its ISSN — and the results are unioned, so
neither source alone is a single point of failure (`src/fetch_flagship.py`).

**Tier 2 — deep bioRxiv scan.** Pulls the full daily bioRxiv
neuroscience/animal-behavior listing (not keyword-narrowed at the query
level — bioRxiv's API doesn't support that), then keeps anything matching a
title keyword stem OR a watch-author name. Full, untruncated abstracts
always (bioRxiv's API includes them natively).

**Tier 3 — general broad search.** Keyword-clustered OpenAlex, PubMed (via
`efetch`, so real abstracts and corresponding-author affiliations, not just
titles), and arXiv. The widest, lowest-priority net.

**Plus: verified live search.** The model is explicitly expected to search
beyond these three tiers using its own judgment — the deterministic tiers
are a safety net, not a ceiling. Anything it finds this way must go through
`scripts/verify_identifier.py` (fetches the canonical record from
CrossRef/PubMed by DOI/PMID — the model never types a paper's metadata from
memory) before `scripts/merge_discovered.py` folds it into the day's
candidate list with a real `candidate_id`. This is the mechanism that lets
the model's own judgment find better papers (which is what made an earlier,
fully-agentic version of this project genuinely good) without reopening the
door to writing detailed, confident content about a paper that was never
actually fetched — which is exactly the failure mode a past run hit once,
and why this gate exists.

Single source of truth for what all three tiers search for:
`src/search_config.py` (query clusters, watch-authors, title-match stems,
the flagship journal list). Edit this alongside `profile.md` when your
interests change — `profile.md` is prose for the model's judgment,
`search_config.py` is what the deterministic fetchers actually go looking for.

## Why this won't break the way earlier attempts did

| Failure mode hit before | Fix here |
|---|---|
| Ran locally; skipped when the laptop slept | Runs as a cloud Routine on Anthropic's infrastructure |
| Model freehand-wrote the whole output | Model writes ONLY small JSON objects (selection, deep-dive); a deterministic validator gates both; `render_pdf.py` formats identically every day |
| One flaky source killed the whole run | Every fetch function is isolated; Tier 1's dual-source design makes even *completeness* fault-tolerant, not just uptime |
| A rate-limited source silently looked "healthy" | Source health is now reported by actual candidate count, not just crash/no-crash |
| Uncapped retries | `process_selection.py` hard-caps attempts at 3 with a counter file — enforced by code regardless of how many times the model retries (proven in `tests_offline/test_routine_flow.py` with a model simulated as never producing valid JSON) |
| A preprint was picked as Paper of the Day | Every candidate is tagged `is_preprint`; the validator rejects a preprint POTD outright and requires a canon fallback instead |
| **Wrong-paper misattribution** (detailed, confident bullets written about a different paper than the one titled) | The verification gate: any paper added via the model's own search must resolve through CrossRef/PubMed before it exists as a candidate at all; the schema's explicit world-knowledge policy separates "background/framing from memory" (fine) from "claims about this specific paper's content" (must trace to fetched text) |
| Windows crashed on non-ASCII author names (`cp1252` default encoding) | Every file read/write in `src/` explicitly uses `encoding="utf-8"` |
| A binary file got corrupted during an ad hoc Drive upload | `scripts/b64encode.py` always opens in `'rb'` mode — no ambiguity left for the model to get wrong |

## What happens each day

1. **Fetch (deterministic).** All three tiers, in parallel-isolated fashion.
2. **Seen-filter.** Drops anything already in the reading-log spreadsheet.
3. **Selection (model, bounded).** Reads `profile.md`, `canon_reading_list.md`,
   and `state/candidates.json`; may supplement via verified live search (see
   above); writes `state/selection.json` per `SELECTION_SCHEMA.md`.
4. **Validation gate (deterministic).** `process_selection.py` checks the
   JSON against a fixed schema, including the preprint rule. Invalid → model
   fixes and resubmits (hard-capped at 3 total). Exhausted → deterministic
   keyword fallback digest, never a broken PDF.
5. **Deep dive (model, new-paper days only).** Fetches open-access full text
   (PMC → Unpaywall → CORE → Semantic Scholar → abstract-only) or queries
   Elicit if connected; refines the Paper of the Day's bullets, read plan,
   and reflection question with real depth.
6. **Render (deterministic).** Same newspaper template every day: masthead,
   editorial, sectioned papers with source badges and institution/country
   where available, closing with the Paper of the Day (bullets, read plan,
   reflection question) and a source-health footer showing actual counts.
7. **Reading log (deterministic).** Appends new rows to
   `state/reading_log.xlsx` (Zotero-lite). Only the **Read** column is yours
   to edit; every run downloads, appends, and never touches existing rows.
8. **Sync + commit (model, as its last actions).** Uploads the PDF to Drive
   `Auditory Grouping Daily/Digests/` and the spreadsheet to
   `.../Reading Log/`, then commits `state/` back to the repo.

**Paper-of-the-Day rotation:** odd days → next unserved canon/foundations
entry; even days → best new (never preprint) paper.

## One-time setup

1. Push this folder to a **private GitHub repo**.
2. Create a **Claude Code Routine** pointed at this repo:
   - Schedule: daily, 01:00 Europe/Berlin.
   - Connectors: **Google Drive** (required), **Elicit** (recommended — used
     for full-text depth on the Paper of the Day when our own fetch can't
     get it).
   - Paste the prompt below verbatim.

### The routine prompt

> You are running the Auditory Grouping Daily digest. Run the exact scripts
> named — don't improvise commands outside this list.
>
> 1. Run `bash scripts/run_daily_prep.sh`. Fetches today's candidates across
>    all three tiers; writes `state/candidates.json` and `state/context.json`.
> 2. Read `state/candidates.json`, `profile.md`, `canon_reading_list.md`,
>    `state/context.json`, and `SELECTION_SCHEMA.md`. You are also expected
>    to search beyond these candidates using your own judgment (specific
>    watch-authors, following up on citations, anything you judge missing).
>    For anything you find this way: run
>    `python3 scripts/verify_identifier.py <doi-or-pmid>` for each one (never
>    type its metadata by hand), then run `python3 scripts/merge_discovered.py`
>    once, then re-read the updated `state/candidates.json`. Then write ONLY
>    `state/selection.json` per the schema.
> 3. Run `python3 src/process_selection.py`.
>    - Exit 0 → step 4 (or step 5 if it printed "canon day, no deep-dive needed").
>    - Exit 1 → fix `state/selection.json` per the printed errors, re-run this script.
>    - Exit 2 → attempts exhausted (hard-capped at 3). Go to step 5 with `--fallback`.
> 4. Read `state/deepdive_input.json` and `DEEPDIVE_SCHEMA.md`. If
>    `full_text_available` is false and Elicit is connected, query it for this
>    paper's methods/results before writing. Write ONLY `state/deepdive.json`.
> 5. Run `python3 src/finalize.py` (or `--fallback` per step 3). Prints
>    `OUTPUT_PDF=...` and `OUTPUT_XLSX=...`.
> 6. Upload both files to Drive using the Drive connector. If it needs
>    base64 content rather than a file path: do NOT read/transform the file
>    yourself (no `cat`, no PowerShell `Get-Content`, no manual `open()` —
>    these can silently corrupt binary files on Windows). Run
>    `python3 scripts/b64encode.py <path>` and use its stdout, unmodified.
>    PDF → "Auditory Grouping Daily/Digests"; xlsx → ".../Reading Log"
>    (overwrite the existing one there).
> 7. Commit and push: `git add state/ && git commit -m "Digest $(date -u +%F)"
>    && git push`. **Never edit or commit anything under `src/`, `scripts/`,
>    or the schema/profile files from within a scheduled run** — those are
>    code, not data; if something there is actually broken, report it in your
>    summary instead of patching it live.

## Tuning (no code changes needed for most of this)
- **`profile.md`** — priorities, watch-authors' framing, tone. Read fresh
  every run.
- **`search_config.py`** — the actual query clusters, watch-author list,
  title-match stems, and flagship journal list the deterministic fetchers
  use. Update this alongside `profile.md`.
- **`canon_reading_list.md`** — foundational papers, served top-to-bottom.
- Retry cap: `MAX_ATTEMPTS` in `src/process_selection.py` (default 3).

## Testing locally
```bash
pip install -r requirements.txt
python3 tests_offline/test_fetch_logic.py       # Tier 2/3 parsing + dedupe
python3 tests_offline/test_fetch_flagship.py    # Tier 1 RSS/Atom/PubMed parsing
python3 tests_offline/test_validator.py         # the schema guardrail
python3 tests_offline/test_verify_and_merge.py  # the verification gate
python3 tests_offline/test_routine_flow.py      # the full state machine
```
`tests_offline/test_fetch_live.py` hits real APIs and needs open internet.

## Honest limitations
- Sci-Hub and automated institutional login are intentionally NOT used.
  Papers with no legal open copy are summarized from the abstract, marked as
  such.
- Institution/country extraction is best-effort: OpenAlex gives clean
  structured institution names; PubMed's raw affiliation string is
  sometimes a full department+address block (truncated for the meta line,
  not cleanly parsed).
- Some flagship-journal RSS feeds may change format or go stale over time —
  Tier 1's PubMed-ISSN side keeps that journal covered even if a specific
  feed breaks, but the feed side may occasionally need a URL update in
  `search_config.py`.
- The live-search-and-verify step is inherently harder to pressure-test
  offline than the deterministic tiers — I can test that verification
  correctly accepts/rejects identifiers, but not "the model behaves well
  when searching live" the same way. Watch a few real runs before fully
  trusting this part.
- A genuinely quiet literature day produces a short digest by design — check
  the footer/`run_log.json` to tell that apart from an actual failure.
