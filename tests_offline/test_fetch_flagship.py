import sys, datetime as dt
sys.path.insert(0, 'src')
import fetch_flagship as ff

# --- RSS 2.0 style feed (Nature-like) ---
RSS_SAMPLE = """<?xml version="1.0"?>
<rss version="2.0">
<channel>
<title>Nature</title>
<item>
  <title>Prefrontal cortex encodes abstract sequence structure</title>
  <link>https://www.nature.com/articles/s41586-026-01234-5</link>
  <description>We show that prefrontal neurons encode transition probabilities. doi:10.1038/s41586-026-01234-5</description>
  <pubDate>Sun, 05 Jul 2026 00:00:00 GMT</pubDate>
</item>
<item>
  <title>An unrelated paper about gut microbiota</title>
  <link>https://www.nature.com/articles/s41586-026-09999-9</link>
  <description>Microbiome composition affects metabolism.</description>
  <pubDate>Sat, 04 Jul 2026 00:00:00 GMT</pubDate>
</item>
</channel>
</rss>"""

since, until = dt.date(2026, 7, 3), dt.date(2026, 7, 6)
journal = {"name": "Nature", "issn": "1476-4687", "rss": "http://fake/nature.rss"}

import types
class FakeResp:
    def __init__(self, content):
        self.content = content.encode()
        self.text = content
    def raise_for_status(self):
        pass

orig_get = ff._get
ff._get = lambda url, params=None, headers=None: FakeResp(RSS_SAMPLE)
papers = ff.fetch_journal_feed(journal, since, until, "test@example.com")
ff._get = orig_get

assert len(papers) == 2, f"expected 2 items, got {len(papers)}"
assert papers[0]["title"] == "Prefrontal cortex encodes abstract sequence structure"
assert papers[0]["doi"] == "10.1038/s41586-026-01234-5"
assert papers[0]["date"] == "2026-07-05"
assert papers[0]["pool"] == "flagship"
print("PASS — RSS 2.0 feed parsing (title, doi extraction, date filter, pool tag)")

# --- date-window filtering: an item outside the window should be excluded ---
RSS_OLD = RSS_SAMPLE.replace("Sun, 05 Jul 2026", "Mon, 01 Jun 2026")
ff._get = lambda url, params=None, headers=None: FakeResp(RSS_OLD)
papers2 = ff.fetch_journal_feed(journal, since, until, "test@example.com")
ff._get = orig_get
assert len(papers2) == 1, f"expected 1 item after date filter, got {len(papers2)}"
print("PASS — date-window filtering excludes out-of-range items")

# --- Atom-style feed (eLife-like) ---
ATOM_SAMPLE = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
<entry>
  <title>Auditory streaming in the inferior colliculus</title>
  <id>https://elifesciences.org/articles/98765</id>
  <summary>Background noise statistics reshape midbrain coding.</summary>
  <updated>2026-07-04T00:00:00Z</updated>
</entry>
</feed>"""
ff._get = lambda url, params=None, headers=None: FakeResp(ATOM_SAMPLE)
papers3 = ff.fetch_journal_feed({"name": "eLife", "issn": None, "rss": "http://fake/elife.xml"},
                                 since, until, "test@example.com")
ff._get = orig_get
assert len(papers3) == 1, papers3
assert papers3[0]["title"] == "Auditory streaming in the inferior colliculus"
assert papers3[0]["date"] == "2026-07-04"
print("PASS — Atom feed parsing (eLife-style)")

# --- PubMed efetch XML parsing: abstract + affiliation + country extraction ---
EFETCH_SAMPLE = """<?xml version="1.0"?>
<PubmedArticleSet>
<PubmedArticle>
  <MedlineCitation>
    <PMID>40123456</PMID>
    <Article>
      <Journal>
        <JournalIssue>
          <PubDate><Year>2026</Year></PubDate>
        </JournalIssue>
      </Journal>
      <ArticleTitle>Prefrontal population coding of learned tone sequences</ArticleTitle>
      <Abstract>
        <AbstractText Label="BACKGROUND">Sequence learning depends on prefrontal cortex.</AbstractText>
        <AbstractText Label="RESULTS">We recorded single units during a go/no-go task.</AbstractText>
      </Abstract>
      <AuthorList>
        <Author><LastName>Smith</LastName><ForeName>Alice</ForeName></Author>
        <Author>
          <LastName>Wang</LastName><ForeName>Xuanyu</ForeName>
          <AffiliationInfo><Affiliation>Technical University of Munich, Munich, Germany</Affiliation></AffiliationInfo>
        </Author>
      </AuthorList>
      <ArticleIdList>
        <ArticleId IdType="doi">10.1016/j.neuron.2026.01.001</ArticleId>
      </ArticleIdList>
    </Article>
  </MedlineCitation>
</PubmedArticle>
</PubmedArticleSet>"""
records = ff._parse_pubmed_efetch_xml(EFETCH_SAMPLE, "Neuron")
assert len(records) == 1, records
rec = records[0]
assert rec["title"] == "Prefrontal population coding of learned tone sequences"
assert "Sequence learning depends" in rec["abstract"] and "single units" in rec["abstract"]
assert rec["authors"] == ["Alice Smith", "Xuanyu Wang"]
assert rec["affiliation"] == "Technical University of Munich, Munich, Germany"
assert rec["country"] == "Germany"
assert rec["doi"] == "10.1016/j.neuron.2026.01.001"
assert rec["is_preprint"] is False
print("PASS — PubMed efetch XML parsing (multi-part abstract, corresponding-author affiliation, country guess)")

# --- regression test: real bug found in production (2026-07-07 digest) ---
# A UK-based paper's affiliation string chained a co-author's German institute
# after a semicolon; the old substring-anywhere search wrongly returned
# "Germany" for an Oxford-based paper. Only the primary (first) affiliation's
# own trailing segment should be trusted.
bug_case = ("Oxford Centre for Integrative Neuroimaging, FMRIB, Nuffield "
            "Department of Clinical Neurosciences, University of Oxford, "
            "Oxford, United Kingdom; Max Planck Institute, Germany")
assert ff._guess_country(bug_case) == "United Kingdom", \
    f"country-guessing regression: got {ff._guess_country(bug_case)!r}"
print("PASS — country-guessing regression test (Oxford paper no longer mislabelled Germany)")

print("\nAll fetch_flagship tests passed.")
