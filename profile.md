# Research Profile — Auditory Grouping Daily

This file is read verbatim by the daily selection step. Edit any time; no
code changes needed. It defines (a) who the reader is, (b) how to judge
relevance, and (c) the two-tier priority structure.

---

## Who I am

Cognitive / systems neuroscience PhD in the **Jacob Lab** (Simon N. Jacob,
Translational NeuroTechnology Laboratory, Dept. of Neurosurgery, TUM; and
Graduate School of Systemic Neurosciences, LMU Munich). I study **auditory
grouping** — the dynamic parsing of auditory streams and the **chunking** of
sounds into sequences — with **electrophysiology** in both mice and humans,
plus behavioural and computational modelling. I do everything myself:
experimental design, hardware and audio timing, training, spike sorting,
analysis, and modelling. So relevance is broad, spanning experimental and
computational systems neuroscience.

### Mouse work
C57BL/6, head-fixed, **go/no-go** licking task (optical lick-meter, NIMH
MonkeyLogic; sessions extracted from `.bhv2`→`.h5`). Stimuli are **Two-Tone
Harmonic Complexes (TTHCs)**, 1:2 harmonic ratio, chords A/B/C at fundamentals
**5.0/7.5/11.3 kHz** (0.75-octave spacing, chosen so second harmonics don't
overlap neighbouring fundamentals), kept in the **3–19 kHz** range to survive
C57BL/6 progressive high-frequency hearing loss. Chord duration **150 ms**,
inter-chord interval **150 ms**, 5 ms cosine on/off ramps. Current target
**BC**; staged distractor curriculum: **BB → CC → adaptive-block BB/CC →
CB → BA/AC/BD/DB**, then embedding the target in longer random streams.

**Protocol history (matters for judging what's "solved" vs. still open):**
Protocol 6 established the closed-loop adaptive distractor-selection system
(see below) and reached BC-vs-CB discrimination. Protocol 7 tested whether
**slowing the pacing removes a primacy bias** (mice over-weighting the first
chord) — but mice wouldn't spontaneously lick under pure operant condition
-ing at this slower pace. **Protocol 8 ("Slow") is the currently-running
revision**: Pavlovian-first pretraining, still probing the same slow-pacing/
primacy-bias question. Still-unsolved items per the lab's own requirements
list: generalising the licked response across different preceding chords
(ABC = BBC), and generalising independent of the target's position in a
longer stream (BC = XBC = XXBC).

**Adaptive distractor-difficulty algorithm** (the "difficulty thermostat"):
per-distractor false-alarm rate is tracked with a Laplace prior
(`N_pres,i₀=2, N_FA,i₀=1`), converted to a selection probability, then
clamped to `[0.15, 0.75]` and renormalised — so a distractor the mouse
currently confuses with the target gets oversampled, but no distractor ever
disappears or dominates entirely.

**Two new task variants I'm actively developing right now:**
1. a **pure-tone version** (single tones instead of two-tone harmonic
   complexes as the sequence elements);
2. a **sound-location version** where each sequence element is defined by
   spatial location instead of pitch — i.e. sequences of locations, not
   sequences of frequencies.
Papers on pure-tone sequence coding, spatial/location auditory sequence
processing, and interaural/spatial cue encoding are therefore currently
elevated in relevance, not just background.

Recording from **prelimbic cortex (PL)**, later **auditory cortex (AC)**,
with **Neuropixels 2.0**. Outcome coding: a **decision window** around the
last-chord onset vs. a separate **response window** after a pause — **SDT/d′
uses decision-window responses only (fhit/fa)**, isolating anticipatory
discrimination from reward-consumption licking (hit/lfa). Lick artefacts
outside 5 ms–10 s are filtered.

**Hardware/methods detail worth recognizing if it comes up in a paper**: lick
spout positioning is deliberately calibrated (not just close enough to reach,
but far enough that mouth-opening isn't mistaken for a lick) — papers on
licking-microstructure measurement or reward-delivery kinematics in rodent
behavior rigs are a low-priority but genuine methods-adjacent interest.

### Human work
Chronic **Utah arrays (Blackrock, Kilosort single units)** in **AG (angular
gyrus), SMG (supramarginal gyrus), IFG, MFG** of a single participant
(initials **M.B.** in lab documentation) with **chronic aphasia from a large
left MCA stroke** (comprehension severely
impaired ~27% accuracy; repetition largely spared ~87%) — this profile shapes
task design, since auditory chunking demands sustained attention and
working memory closer to comprehension-like processing, a real behavioural
feasibility consideration. The lab has prior single-unit work in this same
participant (frontoparietal/basal-ganglia sequence encoding, language-task
single-unit clustering — see the lab preprint).

Task: **chunk-in-stream detection** — a fixed 3- or 4-element target sequence
that may or may not be embedded in a stream; **yes/no (single-interval)
detection, NOT 2AFC** (scored Hit/Miss/FA/CR with d′ and criterion c). Trial
types include **Start-Target / End-Target / Distractor**; distractors are
near-miss variants (temporal reversals, circular shifts, neighbour mutations)
plus unrelated background chunks, in a balanced factorial (element-position-
controlled, translation) design. Five staged difficulty levels: template
acquisition → initial embedding → statistical background variation
(random / random-limited / template-relevant / unrelated chunks) →
complexity scaling with a longer target → integrated multi-template scene
analysis. **7 recording sessions** as described in the poster.

**Three stimulus classes** (extending from chords toward speech): harmonic
chords (6-note whole-scale alphabet with harmonics); **synthetic German
vowels** (TTS via Synthesizer V, plus pitch-shifted human singing); and
**human open syllables**. Core scientific question: the interplay between
**bottom-up statistical learning** (unconscious pattern extraction) and
**top-down template matching** (conscious detection of a memorised target).
High-gamma LFP used as a cross-session traceable signal alongside single units.

### Behavioural / computational modelling
My actual current modelling toolchain (not generic — weight papers using or
advancing these specifically):
- **Custom leaky-accumulator drift-diffusion model**: evidence accumulates
  per chord with chord-specific drift rates, integration noise fixed
  (σ=1.0), silence contributes zero evidence. I test a **family of 24 nested
  models** built from 5 structural toggles: sequence-dependent drift (does a
  chord's evidence value depend on its position — 6 drift rates vs. 3),
  leaky integration, time-dependent urgency (collapsing bounds),
  non-decision sensorimotor delay, and delay jitter — ranging 4–11 free
  parameters. Fit per-session by Maximum Likelihood via
  **`scipy.optimize.differential_evolution`**, model selection via
  **AICc and Akaike weights**. (An earlier/parallel exploratory approach
  also fit by minimising **`wasserstein_distance`** between simulated and
  empirical RT distributions, numba-accelerated — both are "my toolchain.")
- **GLM strategy models**: lick/no-lick modelled as Bernoulli, conditioned on
  a strategy-specific feature map. My actual model structure is tiered across
  three independent factors, all combinations (7×4×4) fit and 5-fold
  cross-validated: **Module A** (cognitive/stimulus strategy — bias, primacy,
  recency, spectral envelope, summed chord identity, chord identity by rank,
  or full-sequence/"chunk" identity — this is the module that directly tests
  whether a mouse is using a shortcut vs. genuine sequence memory), **Module
  B** (trial history — win-stay/lose-shift dynamics), **Module C** (global
  state — slow drifts from satiety/cumulative reward or time-on-task — this
  is my own version of the "continuous/non-stationary behavior" interest
  below). Model selection uses a **parsimony rule**: the simplest model
  within 1 SE of the best cross-validated performance wins, evaluated via
  information gain (bits/trial) and AIC/Akaike weights.
- **Template-matching / ideal-observer** models (pitch uncertainty +
  primacy/recency bias) reproducing behaviour.
- Framing I think in: **statistical learning vs. top-down template matching**,
  **sign-tracking vs. goal-tracking**, **primacy/recency bias**, **first-tone
  heuristics vs. true sequence representation**.
Papers advancing evidence-accumulation fitting methods (distribution-matching
/ simulation-based inference for DDMs, likelihood-free fitting, urgency/
collapsing-bound models) are high-relevance methods hits.

---

## How to judge relevance (instructions to the selector)

- Prefer genuinely NEW findings over reviews, unless a review is unusually
  foundational or directly methodological for my toolkit.
- Relevance notes must be CONCRETE: name the specific finding, method, region,
  circuit, or figure that connects to my mouse BC/CB go/no-go work or my human
  AG/SMG/IFG/MFG chunk-in-stream work. Never write "this is relevant to your
  field" generically.
- A methods paper that develops or cleanly applies a technique I use (below)
  ranks HIGH even if its topic is only adjacent — it builds analysis skill.
- Honesty over volume: if a day's batch is weak, say so; do not inflate
  relevance or pad sections.
- It is fine for a day to have zero papers in some categories.

---

## TIER 1 — core (should drive most of the daily volume)

**Chunking & sequence processing.** chunking, sequence segmentation, auditory
streaming, auditory scene analysis, transitional probabilities, predictive
coding, prediction error, deviance detection, temporal binding, order
perception, tone/chord sequence learning, working memory for sequences,
non-adjacent dependencies, artificial grammar.

**Auditory & prefrontal electrophysiology.** single-unit and LFP recordings in
auditory cortex, prelimbic/medial PFC, IFG/MFG; go/no-go or sequence-learning
paradigms; Neuropixels; intracranial/ECoG/Utah-array human auditory or language
recordings; high-gamma; chronic stability.

**Behavioural & computational modelling of decisions/sequences.** drift-diffusion
/ GDDM, GLM strategy models, template-matching / ideal-observer models, signal
detection theory, evidence accumulation, reinforcement-learning accounts of
sequence/auditory behaviour.

**Statistical learning & oddball.** statistical/implicit learning of sound
sequences, transitional-probability learning, mismatch negativity, oddball,
novelty/deviance detection, regularity extraction.

**Language processing (comprehension-weighted) & the language network.** speech
perception, phonological/semantic processing, word/sentence segmentation,
cortical tracking of linguistic structure, IFG/STG/SMG/AG/perisylvian network.
(De-emphasize speech PRODUCTION-focused work.)

**Clinical/translational: stroke, aphasia, BCI-for-language.** ischaemic stroke,
aphasia (recovery, reorganization), intracortical/communication BCI, speech
decoding, neuroprosthetics for language/locked-in/ALS, translational
animal-to-human bridges.

## TIER 2 — genuinely relevant, needn't dominate

**Broader systems & circuits.** auditory pathway (cochlea → inferior colliculus
→ A1), thalamus, basal ganglia, **dopamine / reward prediction error**,
corticostriatal loops, sign-tracking vs goal-tracking.

**Wider recording & perturbation methods.** optogenetics, fiber photometry,
calcium imaging (2-photon, miniscope), causal circuit manipulation.

**Population & network analysis methods.** dPCA, RSA, mixed selectivity,
population geometry / state-space / neural manifolds, cross-temporal and
cross-task decoding, **Markov / hidden Markov models, graph-theoretic and
network analysis, functional and effective connectivity**.

**Animal models of cognition generally**, comparative auditory cognition,
primate sequence learning.

**Broader cognition** — attention, working memory, cognitive control,
decision-making — with a lean toward order/sequence-related work.

## Lower priority (surface only if exceptional)
Pure human fMRI/EEG with no intracranial or single-unit component; non-auditory
sensory systems unless the method clearly transfers; purely clinical papers with
no mechanistic angle; generic ML/AI with no neuroscience link; computational
phonology / bilingual psycholinguistics (a means to an end for my stimuli, not
my research question).

## Watch authors (their new work jumps up)
See `search_config.py` for the full working list (kept there so the fetcher
uses it directly). It spans the reader's Google Scholar follow-list across
auditory predictive processing / MMN, auditory-cortex plasticity, statistical
and sequence learning, rodent decision-making, human intracranial / language
network, and modelling. None are current collaborators — they're the field
the reader wants to track.

## Continuous / non-stationary behavioral dynamics — a distinct standing interest
I'm specifically interested in modelling and neural studies where behaviour is
treated as an evolving, **non-stationary** process rather than reduced to
independent per-trial outcomes. Concretely, this means: hidden Markov /
state-space models of behavioural strategy or engagement (e.g. GLM-HMM-style
approaches), models of slow drift in strategy or motivation across a session
(this is exactly what my own GLM's Module C — satiety/time-on-task — is
trying to capture), continuous tracking / pose-estimation-based behavioural
quantification, spontaneous/unprompted movement analysis, and any framing
where "trial structure" is treated as an analysis convenience rather than a
ground truth of how the animal is actually behaving. This is a genuinely
elevated priority, not a minor add-on — treat it as comparable in importance
to the Tier 1 categories above, even though it cuts across species and
paradigms rather than being auditory-specific.

## Munich labs — always worth surfacing
The lab collaborates locally, so **computational / cognitive / systems
neuroscience groups in Munich** deserve elevated attention when their new
work is auditory, sequence-, decision-, or systems/computational-
neuroscience-related. The explicit BCCN Munich faculty list is
`MUNICH_LABS` in `search_config.py` (also checked in the bioRxiv author-match
scan). If a candidate's affiliation/country fields indicate a Munich
institution and the topic is even loosely relevant, lean toward including it
and note the local connection.

## My own output — never recommend my own work back to me as "new"
My most recent output is my **MSc thesis (last summer)** on this project, plus
the **MBCN 2026 conference poster** ("Auditory chunking: neuronal mechanisms
in human frontoparietal cortex and mouse models") and the **lab preprint**
in the same human participant: Schiffl, Held et al., "A right-hemispheric
language network at single-neuron resolution" (bioRxiv, March 2026;
Jacob lab, ERC grants Memcircuit/Rhetorical). If a candidate paper is clearly
my own or the lab's already-known work, don't surface it as new — at most
note it as context.

**What that preprint already established (treat as MY prior result, not
background)** — a new paper directly extending any of this should be flagged
as unusually high-value, not just topically related: 10,144 units across
right-hemisphere MFG/IFG/SMG/ANG in the same M.B. participant during
naming/repetition/comprehension; **semantic (fastText) features dominate
prefrontal (MFG/IFG) coding while phonological (Whisper-embedding) features
dominate parietal (SMG) coding**; item selectivity is highly task-specific
(mixed selectivity) despite correlated overall activity across tasks;
dPCA showed time-dominated variance in MFG/IFG vs. stimulus-time interaction
dominated variance in SMG; cross-task/cross-temporal SVM decoding showed
prefrontal generalization across modalities but SMG modality-specificity.
Any new paper on semantic-vs-phonological dissociation, right-hemisphere/
non-dominant language processing, or single-neuron language coding should be
read against this specific prior result.
Close external collaborator on this preprint (not Munich, but worth watching
directly): **Moritz Grosse-Wentrup** (University of Vienna).

## Language & naming conventions (read this before writing anything)

Define each paradigm ONCE in plain language, then refer to it in plain
language afterward. Do not chain letter/region codes as recurring shorthand —
readers should not need to hold a legend in their head to follow a sentence.

**Concrete example of what to avoid and what to write instead:**
- BAD: "a direct precedent for how your BB/CC/CB distractor structure could
  reshape target coding before it ever reaches PL or AC in the BC/CB task."
- GOOD: "a direct precedent for how repeating or reordering the distractor
  chords in your mouse sequence-discrimination task could reshape target
  coding before the signal ever reaches prefrontal or auditory cortex."
- BAD: "relevance to your human AG/SMG/IFG/MFG work"
- GOOD: "relevance to your human chunk-in-stream work, which records from
  angular gyrus, supramarginal gyrus, and inferior/middle frontal gyrus"
  (spell out region names in prose at least once per document; abbreviations
  are fine only in the per-paper meta line, not inside sentences)

Concretely:
- **The mouse work**: call it "the mouse sequence-discrimination task" or "my
  mouse go/no-go sequence task." The target sequence is BC; distractors
  include BB, CC, CB, BA, AC, BD, DB — but describe distractor TYPES in words
  ("a repeated-chord distractor," "a reordered distractor") rather than citing
  the letter codes. Only cite a specific letter code when a finding hinges on
  that exact contrast, and even then spell out what it means in the same
  sentence.
- **The human work**: call it "the human chunk-in-stream task." Spell out
  region names in prose (angular gyrus, supramarginal gyrus, inferior/middle
  frontal gyrus) at least once; abbreviations are fine afterward or in meta
  lines, not chained together as a single jargon block.
- Prefer describing WHAT the task tests over reciting its internal condition
  labels.

## Depth expected in relevance notes and Paper-of-the-Day bullets

Write with real depth, not single terse sentences:
- Each `relevance_note` should be 2-4 sentences: name the specific finding,
  then explain concretely HOW it connects to my mouse or human paradigm (which
  part of my task, which analysis, which open question it bears on) — not just
  that it does.
- Paper-of-the-Day `why_it_matters` bullets should each be a full thought (1-2
  sentences), not a fragment — enough that reading just the bullets gives a
  genuine sense of the paper's contribution, not just a topic tag.
- This is not padding: honesty about a thin day still applies — a thin day
  should have FEWER papers written about thoroughly, not many papers written
  about thinly.

## World knowledge: welcome for context, never for claims about a specific paper
Use your own trained knowledge freely for background, definitions, and
framing — that's what makes writing feel expert rather than mechanical.
But any claim about what a SPECIFIC paper found or argued must trace to its
actual fetched abstract/full text, never to a general impression of what a
paper like that "probably" says. If you're not sure you're describing the
actual paper in front of you, say so or leave the claim out.

## Notes for the Paper-of-the-Day read plan and reflection question
Give a concrete ~20-minute read plan: which sections to read in full, which
to skim, and what to focus on in each — the kind of advice a mentor would
give about spending limited reading time well, not just "read this paper."

End the Paper of the Day with a reflection question that is ideally
**two linked parts**, building toward an actual experimental-design decision
— not a single-clause comprehension check. It must require engaging with the
paper's method or finding and, ideally, connect to my own mouse or human
paradigm. Example shape: "Would you predict X reflects mechanism A or
mechanism B in your own data — and which of your existing conditions could
already distinguish between them, versus needing a new one?"
