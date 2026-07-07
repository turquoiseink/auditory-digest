import sys
sys.path.insert(0, 'src')
import fetch_papers as fp

# --- OpenAlex-shaped record with inverted-index abstract ---
oa = {
    "title": "Prefrontal encoding of learned tone sequences",
    "abstract_inverted_index": {"We": [0], "show": [1], "prefrontal": [2], "encoding": [3]},
    "publication_date": "2026-07-02",
    "doi": "https://doi.org/10.1/abc",
    "primary_location": {"source": {"display_name": "Nature Neuroscience"},
                         "landing_page_url": "https://x"},
    "authors": [], "authorships": [{"author": {"display_name": "A. Smith"}}],
    "type": "article",
}
p = fp._openalex_paper(oa, pool="A", tag="test")
assert p["title"].startswith("Prefrontal"), p
assert p["abstract"] == "We show prefrontal encoding", p["abstract"]
assert p["doi"] == "10.1/abc", p["doi"]
assert p["venue"] == "Nature Neuroscience"
assert p["authors"] == ["A. Smith"]
print("PASS — OpenAlex parsing + inverted-index abstract reconstruction")

# --- arXiv Atom parsing ---
atom = """<entry><title>A q-bio paper on
sequences</title><summary>Long   abstract   text</summary>
<published>2026-07-01T00:00:00Z</published><id>http://arxiv.org/abs/2607.001</id>
<author><name>B. Lee</name></author></entry>"""
assert fp._tag(atom, "title").replace("\n", " ").split()[0] == "A"
assert " ".join(fp._tag(atom, "summary").split()) == "Long abstract text"
print("PASS — arXiv Atom tag extraction")

# --- dedupe: same DOI across pools keeps pool A; same title dedupes ---
papers = [
    {"title": "Same Paper", "doi": "10.1/x", "pool": "B"},
    {"title": "Same Paper", "doi": "10.1/x", "pool": "A"},
    {"title": "Other", "doi": "", "pool": "A"},
    {"title": "other", "doi": "", "pool": "A"},  # title-dup of "Other"
]
dd = fp.dedupe(papers)
assert len(dd) == 2, [p["title"] for p in dd]
same = [p for p in dd if p["title"] == "Same Paper"][0]
assert same["pool"] == "A", "pool A should win the DOI tie"
print("PASS — dedupe (DOI tie -> pool A wins; title-normalized dedupe)")

# --- Tier 2: bioRxiv title/author match filter ---
assert fp._title_matches("Prefrontal cortex encodes tone sequences") is True
assert fp._title_matches("A new species of deep-sea anglerfish") is False
assert fp._author_matches(["Xuanyu Wang", "C. Someone"]) is True  # watch author
assert fp._author_matches(["Totally Unrelated Person"]) is False
print("PASS — Tier 2 title-stem and watch-author matching")

# --- dedupe priority: flagship > A > B on a DOI tie ---
papers2 = [
    {"title": "Same Paper", "doi": "10.1/y", "pool": "B"},
    {"title": "Same Paper", "doi": "10.1/y", "pool": "A"},
    {"title": "Same Paper", "doi": "10.1/y", "pool": "flagship"},
]
dd2 = fp.dedupe(papers2)
assert len(dd2) == 1 and dd2[0]["pool"] == "flagship", dd2
print("PASS — dedupe priority: flagship wins over A and B on a tie")

print("\nAll fetch-logic unit tests passed.")
