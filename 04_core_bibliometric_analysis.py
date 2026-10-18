import pandas as pd
import re
from collections import Counter

OUT_DIR = "/home/claude/ntd_biblio"
df = pd.read_csv(f"{OUT_DIR}/master_final.csv")
df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
df["cited_by"] = pd.to_numeric(df["cited_by"], errors="coerce").fillna(0).astype(int)

print("="*60, "\n1. ANNUAL SCIENTIFIC PRODUCTION\n", "="*60)
yearly = df.groupby("year").size().sort_index()
print(yearly.to_string())
print("\nTotal:", yearly.sum())

print("\n", "="*60, "\n2. TOP JOURNALS\n", "="*60)
top_journals = df["journal"].value_counts().head(15)
print(top_journals.to_string())
print(f"\nDistinct journals: {df['journal'].nunique()}")

print("\n", "="*60, "\n3. MOST CITED PAPERS\n", "="*60)
top_cited = df.sort_values("cited_by", ascending=False)[["title", "year", "journal", "cited_by", "source"]].head(15)
for _, r in top_cited.iterrows():
    print(f"  [{r['cited_by']:>4}] {r['year']} - {r['title'][:85]} ({r['journal']})")

print("\n", "="*60, "\n4. AUTHOR PRODUCTIVITY\n", "="*60)
author_counter = Counter()
for names in df["author_full_names"].dropna():
    for a in str(names).split(";"):
        a = a.strip()
        a_clean = re.sub(r"\s*\(\d+\)\s*$", "", a).strip()
        if a_clean:
            author_counter[a_clean] += 1
top_authors = author_counter.most_common(15)
for a, c in top_authors:
    print(f"  {c:>3}  {a}")
print(f"\nTotal distinct authors: {len(author_counter)}")

print("\n", "="*60, "\n5. COUNTRY OF AFFILIATION\n", "="*60)
country_counter = Counter()
for aff in df["affiliations"].dropna():
    seen = set()
    for p in str(aff).split(";"):
        p = p.strip()
        if not p: continue
        tokens = [t.strip() for t in p.split(",")]
        if tokens:
            country = re.sub(r"\.$", "", tokens[-1]).strip()
            if country and len(country) < 40:
                seen.add(country)
    for c in seen:
        country_counter[c] += 1
top_countries = country_counter.most_common(20)
for c, n in top_countries:
    print(f"  {n:>3}  {c}")

print("\n", "="*60, "\n6. KEYWORD FREQUENCY\n", "="*60)
kw_counter = Counter()
for kws in df["author_keywords"].dropna():
    for k in str(kws).split(";"):
        k = k.strip().lower()
        if k:
            kw_counter[k] += 1
top_kw = kw_counter.most_common(30)
for k, c in top_kw:
    print(f"  {c:>3}  {k}")

# Save outputs
yearly.to_csv(f"{OUT_DIR}/FINAL_annual_production.csv", header=["n_publications"])
top_journals.to_csv(f"{OUT_DIR}/FINAL_top_journals.csv", header=["n_publications"])
pd.DataFrame(top_authors, columns=["author", "n_publications"]).to_csv(f"{OUT_DIR}/FINAL_top_authors.csv", index=False)
pd.DataFrame(top_countries, columns=["country", "n_publications"]).to_csv(f"{OUT_DIR}/FINAL_top_countries.csv", index=False)
pd.DataFrame(top_kw, columns=["keyword", "frequency"]).to_csv(f"{OUT_DIR}/FINAL_top_keywords.csv", index=False)
top_cited.to_csv(f"{OUT_DIR}/FINAL_top_cited.csv", index=False)

n_journals = df['journal'].nunique()
n_authors = len(author_counter)
n_countries = len(country_counter)
print(f"\nSUMMARY: {len(df)} records, {n_journals} journals, {n_authors} authors, {n_countries} countries")
print(f"Total citations: {df['cited_by'].sum()}, mean: {df['cited_by'].mean():.2f}, median: {df['cited_by'].median()}")
cites_sorted = sorted(df['cited_by'].tolist(), reverse=True)
h = 0
for i,c in enumerate(cites_sorted, start=1):
    if c >= i: h = i
print(f"Approx h-index: {h}")
