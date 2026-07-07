# Canon / Foundations Reading List

Odd calendar days serve the next unserved entry here (a foundational paper /
key review I should know cold); even days serve the best NEW paper. Progress
is tracked in `state/canon_progress.json`. The selector reads this file
verbatim — add entries freely with a one-line note on why they matter.
Roughly ordered as a learning path; the pipeline serves top-to-bottom and
does not reorder.

## Auditory streaming, chunking, statistical learning
- Bregman (1990), *Auditory Scene Analysis* — foundational framework (cite a
  review chapter if the book isn't fetchable).
- Saffran, Aslin & Newport (1996, Science) — statistical learning in infants.
- Saffran, Johnson, Aslin & Newport (1999, Cognition) — statistical learning
  of tone sequences (non-linguistic; direct to my chords).
- Dehaene, Meyniel, Wacongne, Wang & Pallier (2015, Neuron) — neural
  representation of sequences: transition probabilities → algebraic patterns.
- Ding, Melloni, Zhang, Tian & Poeppel (2016, Nat Neurosci) — cortical
  tracking of hierarchical linguistic structure.
- Winkler, Denham & Nelken (2009, TICS) — predictive modelling of the
  auditory scene / regularity representation.

## Prefrontal cortex, sequences, working memory
- Miller & Cohen (2001, Annu Rev Neurosci) — PFC and cognitive control.
- Fang, Jiang, Chen, Zhang & Wang (2025, Curr Biol) — theta control of
  sequence working-memory geometry in frontal cortex.
- Libby & Buschman (2021, Nat Neurosci) — rotational dynamics reduce
  interference between sensory and memory representations (my ICI rationale).

## Prediction error / oddball / mPFC–auditory
- Näätänen, Gaillard & Mäntysalo (1978) — the mismatch negativity.
- Casado-Román et al. (2020, PLoS Biol) — prediction-error signalling in mPFC.
- Hockley, Bohorquez & Malmierca (2025, Cell Rep) — top-down mPFC control of
  auditory-cortex prediction errors (optogenetic).

## Human intracranial language/parietal network
- Flinker et al. (2015, PNAS) — causal role of Broca's area in speech.
- Mesgarani et al. (2014, Science) — phonetic feature encoding in human STG.
- Ding et al. (2018, J Neurosci) — attention required for knowledge-based
  sequential grouping (syllables → words).
- Jamali et al. (2024, Nature) — semantic encoding during language
  comprehension at single-cell resolution — directly cited in the lab's own
  preprint on the same participant as the closest left-hemisphere analogue.
- Khanna et al. (2024, Nature) — single-neuronal elements of speech
  production in humans.
- Wandelt et al. (2024, Nat Hum Behav) — internal speech encoding by single
  neurons in human SMG.

## Continuous / non-stationary behavioral dynamics
- Ashwood et al. — GLM-HMM: hidden Markov models of discrete behavioral
  states/strategies (the methodological ancestor of my own GLM Module C
  slow-drift framing).
- Any International Brain Laboratory (IBL) work on state-dependent decision
  strategies — same standing interest.

## Decision-making & behavioural modelling
- Gold & Shadlen (2007, Annu Rev Neurosci) — neural basis of decision-making.
- Brunton, Botvinick & Brody (2013, Science) — evidence accumulation in rats
  and humans.
- Ratcliff & McKoon (2008, Neural Comput) — the drift-diffusion model (my DDM
  backbone).

## Reward / learning circuitry
- Schultz, Dayan & Montague (1997, Science) — reward prediction-error signal.
- Flagel et al. (2011, Nature) — sign-tracking vs goal-tracking and dopamine
  (my Protocol-1 failure explanation).

## Stimulus design & auditory cortex plasticity (from my own task documentation)
- Wang et al. (2020, Nat Commun) — single-neuron representation of learned
  complex sounds; "Holistic Bursting" cells respond to learned chords but not
  constituent tones — the direct rationale for using chords, not pure tones
  (until now, with the new pure-tone variant).
- De et al. (2024, J Neurosci) — differential encoding of two-tone harmonics
  by sex in mouse auditory cortex.
- Gosselin et al. (2025, PLoS Biol) — sound feature representations
  decorrelate across the mouse auditory pathway (Bathellier lab).
- De Hoz & Nelken (2014, PLoS ONE) — frequency tuning: different bandwidths
  for discrimination vs. generalization — the basis for my 0.75-octave chord
  spacing.
- Walton, Frisina & Meierhans (1995, Hear Res); Prosen, Dore & May (2003,
  Hear Res); Ison, Allen & O'Neill (2007, JARO); Carlson & Willott (1996,
  Hear Res) — the C57BL/6 progressive high-frequency hearing-loss literature
  that constrains my whole stimulus frequency range (3–19 kHz).
- Bhumika et al. (2020, Cereb Cortex); Kirchgessner, Vaze & Froemke (2025,
  bioRxiv); Zucca et al. (2024, Cereb Cortex); Bureš et al. (2024, Hear Res)
  — auditory cortex critical periods and why passive exposure doesn't help
  at the age I receive mice (~P56, past the critical period).
- Dayan et al. (2006) — Pavlovian-instrumental conflict, my framing for why
  pure operant conditioning without Pavlovian pretraining failed.
- Majumder et al. (2023); Yang et al. (2026) — temporal scaling of
  neocortical dynamics during motor learning, my framing for why punished
  operant conditioning after Pavlovian pretraining produces a gradual
  rightward shift in response timing rather than an abrupt one.

## Methods backbone
- Kobak et al. (2016, eLife) — demixed PCA.
- King & Dehaene (2014, TICS) — temporal generalization / cross-temporal
  decoding.
- Kriegeskorte, Mur & Bandettini (2008, Front Syst Neurosci) — RSA.
- Rigotti et al. (2013, Nature) — mixed selectivity.
- Jun et al. (2017, Nature) — Neuropixels.
- Steinmetz et al. (2021, Science) — Neuropixels 2.0 / chronic stability.
- Pachitariu et al. — Kilosort spike sorting (read the assumptions; I use it).

## Animal auditory sequence learning
- Zhou, de Villers-Sidani, Panizzutti & Merzenich (2010, PNAS) —
  successive-signal biasing for a learned sound sequence (closest rodent
  precedent to my task).
- Kudoh, Seki & Shibuki (2004) — cholinergic dependence of sound-sequence
  learning in rat AC.
- Bale et al. (2021, Curr Biol) — sequence learning induces multi-parameter
  selectivity in mouse somatosensory cortex (cross-modal analogue).

---
Add more entries any time — no code changes needed to grow this list.
