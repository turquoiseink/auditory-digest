"""
search_config.py — structured search terms, watch-authors, and journal list.

Why this exists separately from profile.md: profile.md is prose meant for the
model's own judgment (nuance, priorities, tone). This file is the deterministic
fetchers' single source of truth — plain Python data, easy to edit, nothing to
parse out of natural language. When you update your interests, update BOTH:
profile.md for how the model should reason about relevance, and the relevant
list here for what the fetchers actually go looking for.
"""

# --- Tier 3: general keyword-clustered search (OpenAlex/PubMed/arXiv) -------
QUERY_CLUSTERS = [
    "auditory chunking sequence segmentation",
    "auditory streaming scene analysis",
    "statistical learning transitional probability sound",
    "sequence working memory prefrontal",
    "order perception temporal sequence cortex",
    "auditory cortex single unit sequence",
    "prelimbic prefrontal auditory prediction",
    "Neuropixels auditory cortex mouse",
    "mismatch negativity deviance detection auditory",
    "intracranial ECoG speech language cortex",
    "Utah array human single neuron language",
    "drift diffusion model decision auditory",
    "behavioral GLM strategy model mouse",
    "template matching ideal observer perception",
    "population geometry state space neural sequence",
    "cross-temporal decoding neural",
    "mixed selectivity prefrontal population",
    "hidden Markov model neural states",
    "functional connectivity auditory cortex",
    "optogenetics auditory cortex behavior",
    "fiber photometry dopamine learning",
    "two-photon calcium imaging auditory cortex",
    "basal ganglia thalamus sequence learning",
    "reward prediction error dopamine",
    "speech brain computer interface decoding",
    "aphasia stroke language recovery cortex",
    "go/no-go auditory discrimination rodent",
    # two new active task variants (July 2026): pure-tone + spatial-location
    "pure tone sequence learning cortex",
    "auditory spatial location sequence encoding",
    "sound localization cortex neurons",
    "interaural spatial cue auditory cortex",
    "spatial sequence working memory",
    # continuous / non-stationary behavioral dynamics (standing interest,
    # not auditory-specific)
    "hidden Markov model behavioral strategy",
    "GLM-HMM decision-making",
    "non-stationary behavior model",
    "behavioral state switching dynamics",
    "internal states decision-making mice",
    "continuous behavior tracking pose estimation",
    "spontaneous movement neural correlate",
]

# --- Watch authors: their new work matters regardless of keyword match -----
# Used to pull matches by author name alone, e.g. in the bioRxiv deep scan.
WATCH_AUTHORS = [
    # Own lab / close collaborators
    "Simon Jacob", "Xuanyu Wang",
    # Auditory predictive processing / MMN / mPFC-AC circuit
    "Manuel Malmierca", "Lorena Casado-Román", "Adam Hockley",
    "Ryszard Auksztulewicz", "David Pérez-González", "Jean-Marc Edeline",
    "Michael Brosch",
    # Auditory cortex plasticity / comparative auditory cognition
    "Michael Merzenich", "Daniel Polley", "Étienne de Villers-Sidani",
    "Jan Schnupp", "Jonathan Fritz", "Maria Neimark Geffen",
    "Andrea Hasenstaub", "Brice Bathellier", "Christopher Petkov",
    "Masumi Wakita", "Marc Hauser", "Hirokazu Takahashi", "Takahiro Noda",
    "Jianfeng Zhang", "Liping Wang", "Dan Luo", "Xing Tian", "Yu Xiongjie",
    "Kongyan Li", "Li Xinjian",
    # Statistical learning / sequence learning
    "Jenny Saffran", "Richard Aslin", "Elissa Newport", "Pierre Perruchet",
    "Dezső Németh", "Laura Batterink", "Stefan Köhler", "Ana Fló",
    "Lucas Benjamin", "Florent Meyniel", "Ghislaine Dehaene-Lambertz",
    "Catherine Wacongne", "Morten Christiansen", "Annie Vinter",
    "Juan M. Toro", "Delphine Dahan",
    # Rodent decision-making / systems neuroscience
    "Christine Constantinople", "Anne Churchland", "Athena Akrami",
    "Kishore Kuchibhotla", "Santiago Jaramillo", "Anthony Zador",
    "Hang Zhang",
    # Human intracranial / language network
    "Edward Chang", "Johannes Sarnthein", "Alejandro Blenkmann",
    "Anne-Kristin Solbakk", "Christophe Pallier", "Lars Meyer",
    "David Poeppel", "Nai Ding", "Lucia Melloni",
    # Modelling / decision-making / prefrontal cortex
    "Stanislas Dehaene", "Timothy Buschman", "Carlos Brody",
    "Michael Shadlen", "Doris Tsao", "Robert Zatorre", "Esther Mondragón",
    # Methods
    "Nicholas Steinmetz", "Marius Pachitariu", "Shelly Flagel",
    "Shihab Shamma", "Nima Mesgarani",
    # Other (labmates / less-placed but on the reader's own watch list)
    "Alice Milne", "Guillermo Varela Carbajal", "HiJee Kang",
    "Laura Bohórquez", "Hyunjung An",
    # Sourced directly from the mouse task documentation's own citations
    "Livia de Hoz", "Ivan Nelken", "Miguel Maravall", "Tania Barkat",
    "Robert Froemke",
    # Continuous / non-stationary behavioral dynamics (standing interest)
    "Zoe Ashwood", "Anne Urai", "Ilana Witten", "Sebastian Musall",
    "Carsen Stringer", "Kenneth Harris", "Matteo Carandini", "Ann Kennedy",
    # Human single-neuron language (directly cited in the lab's own preprint
    # on the same participant — treat as close prior-work context)
    "Ziv Williams", "Richard Andersen", "Sydney Cash", "Frank Willett",
    # Close external collaborator (not Munich) on the lab preprint
    "Moritz Grosse-Wentrup",
]

# --- Munich comp/cognitive/systems neuroscience faculty (BCCN Munich) ------
# The lab collaborates only with Munich groups; these deserve elevated
# attention whenever their new work is even loosely relevant (matched via
# TITLE_MATCH_STEMS and the candidate's affiliation/country fields).
MUNICH_LABS = [
    "Alexander Borst", "Laura Busse", "Lisa Fenk", "Uwe Firzlaff",
    "Virginia Flanagin", "David Franklin", "Julijana Gjorgjieva",
    "Benedikt Grothe", "Werner Hemmert", "Andreas Herz", "Simon Jacob",
    "Harald Luksch", "Wiktor Młynarski", "Dennis Nestvogel",
    "Steffen Schneider", "Anna Schroeder", "Bernhard Seeber", "Anton Sirota",
    "Kay Thurley", "Daniela Vallentin", "Leo van Hemmen", "Thomas Wachtler",
    "Bernhard Wolfrum",
]

# --- Keyword stems for title-matching the bioRxiv deep scan -----------------
# Looser than QUERY_CLUSTERS (single stems, not phrases) since this is checked
# against titles alone, which are short.
TITLE_MATCH_STEMS = [
    "auditory", "chunk", "sequence", "prefrontal", "prelimbic", "chord",
    "tone sequence", "streaming", "statistical learning", "oddball",
    "mismatch negativity", "neuropixels", "utah array", "ecog",
    "intracranial", "population geometry", "cross-temporal", "drift diffusion",
    "aphasia", "stroke", "dopamine", "basal ganglia", "sign-tracking",
    "goal-tracking", "speech decoding", "language network",
    "pure tone", "sound localization", "spatial hearing", "interaural",
    "drift-diffusion", "evidence accumulation", "leaky integrator",
    "vowel", "syllable", "harmonic complex",
    "holistic bursting", "critical period auditory", "hearing loss cortex",
    "presbycusis", "cortical map plasticity", "auditory decorrelation",
    "hidden markov", "non-stationary behavior", "behavioral state",
    "glm-hmm", "internal state", "continuous behavior", "pose estimation",
]

# --- Tier 1: flagship journals, scanned via two independent sources each ----
# (RSS/Atom feed + PubMed ISSN-scoped query, unioned, so neither source alone
# is a single point of failure.) is_open_access is informational only — even
# closed-access journals are covered for title+abstract via PubMed regardless.
FLAGSHIP_JOURNALS = [
    {"name": "Nature", "issn": "1476-4687",
     "rss": "https://www.nature.com/nature.rss", "is_open_access": False},
    {"name": "Nature Neuroscience", "issn": "1546-1726",
     "rss": "https://www.nature.com/neuro.rss", "is_open_access": False},
    {"name": "Nature Communications", "issn": "2041-1723",
     "rss": "https://www.nature.com/ncomms.rss", "is_open_access": True},
    {"name": "Nature Human Behaviour", "issn": "2397-3374",
     "rss": "https://www.nature.com/nathumbehav.rss", "is_open_access": False},
    {"name": "Nature Reviews Neuroscience", "issn": "1471-0048",
     "rss": "https://www.nature.com/nrn.rss", "is_open_access": False},
    {"name": "Science", "issn": "1095-9203",
     "rss": "https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=science",
     "is_open_access": False},
    {"name": "Science Advances", "issn": "2375-2548",
     "rss": "https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=sciadv",
     "is_open_access": True},
    {"name": "Cell", "issn": "1097-4172",
     "rss": "https://www.cell.com/cell/current.rss", "is_open_access": False},
    {"name": "Neuron", "issn": "1097-4199",
     "rss": "https://www.cell.com/neuron/current.rss", "is_open_access": False},
    {"name": "Current Biology", "issn": "1879-0445",
     "rss": "https://www.cell.com/current-biology/current.rss", "is_open_access": False},
    {"name": "iScience", "issn": "2589-0042",
     "rss": "https://www.cell.com/iscience/current.rss", "is_open_access": True},
    {"name": "Cell Reports", "issn": "2211-1247",
     "rss": "https://www.cell.com/cell-reports/current.rss", "is_open_access": True},
    {"name": "Scientific Reports", "issn": "2045-2322",
     "rss": "https://www.nature.com/srep.rss", "is_open_access": True},
    {"name": "PNAS", "issn": "1091-6490",
     "rss": "https://www.pnas.org/action/showFeed?type=etoc&feed=rss&jc=pnas",
     "is_open_access": False},
    {"name": "eLife", "issn": "2050-084X",
     "rss": "https://elifesciences.org/rss/recent.xml", "is_open_access": True},
    {"name": "Trends in Cognitive Sciences", "issn": "1879-307X",
     "rss": "https://www.cell.com/trends/cognitive-sciences/current.rss", "is_open_access": False},
    {"name": "Trends in Neurosciences", "issn": "1878-108X",
     "rss": "https://www.cell.com/trends/neurosciences/current.rss", "is_open_access": False},
    {"name": "Annual Review of Neuroscience", "issn": "1545-4126",
     "rss": None, "is_open_access": False},  # no public RSS; PubMed-only coverage
    {"name": "Journal of Neuroscience", "issn": "1529-2401",
     "rss": "https://www.jneurosci.org/rss/current.xml", "is_open_access": False},
]
