import sys, datetime as dt
sys.path.insert(0, 'src')
import fetch_papers as fp

until = dt.date.today()
since = until - dt.timedelta(days=5)
email = "salemayas33@gmail.com"

print("Testing OpenAlex (Pool A, 2 clusters)...")
fp.QUERY_CLUSTERS = fp.QUERY_CLUSTERS[:2]  # trim for a fast smoke test
a = fp.fetch_openalex(since, until, email)
print(f"  OpenAlex A: {len(a)} papers; sample: {a[0]['title'][:70] if a else 'NONE'}")

print("Testing bioRxiv...")
b = fp.fetch_biorxiv(since, until, email)
print(f"  bioRxiv: {len(b)} neuro papers; sample: {b[0]['title'][:70] if b else 'NONE'}")

print("Testing arXiv q-bio.NC...")
x = fp.fetch_arxiv(since, until, email)
print(f"  arXiv: {len(x)} papers; sample: {x[0]['title'][:70] if x else 'NONE'}")

print("Testing field pulse (Pool B)...")
fp2 = fp
pulse = fp.fetch_field_pulse(since, until, email)
print(f"  Field pulse: {len(pulse)} flagship papers; venues: {sorted(set(p['venue'] for p in pulse))[:8]}")

all_papers = fp.dedupe(a + b + x + pulse)
print(f"\nTotal after dedupe: {len(all_papers)}")
print(f"  Pool A: {sum(1 for p in all_papers if p['pool']=='A')}")
print(f"  Pool B: {sum(1 for p in all_papers if p['pool']=='B')}")
