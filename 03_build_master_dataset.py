import pandas as pd
import re

UPLOAD_DIR = "/mnt/user-data/uploads"
OUT_DIR = "/home/claude/ntd_biblio"

pm = pd.read_csv(f"{UPLOAD_DIR}/csv-Myanmartia-set-3.csv", encoding="utf-8-sig", dtype=str)
sc = pd.read_csv(f"{UPLOAD_DIR}/export_4284dc95-557d-4a1a-9f98-fa2d1ad2d4a8_2026-07-15T045600_152412201.csv", encoding="utf-8-sig", dtype=str)

final = pd.read_csv(f"{OUT_DIR}/final_dataset_FINAL.csv")

def norm_doi(d):
    if not isinstance(d, str) or d.strip() == "":
        return None
    d = d.strip().lower()
    d = re.sub(r"^https?://(dx\.)?doi\.org/", "", d)
    return d

sc["doi_norm"] = sc["DOI"].apply(norm_doi)
sc_idx = sc.set_index("doi_norm")

JOURNAL_NORMALIZE = {
    "malaria journal ": "Malaria Journal",
    "malaria journal": "Malaria Journal",
    "malar j": "Malaria Journal",
    "parasites and vectors ": "Parasites and Vectors",
    "parasites and vectors": "Parasites and Vectors",
    "nature communications ": "Nature Communications",
    "nature communications": "Nature Communications",
    "the korean journal of parasitology": "Korean Journal of Parasitology",
    "korean journal of parasitology": "Korean Journal of Parasitology",
    "public health nursing (boston, mass.)": "Public Health Nursing",
    "japanese journal of infectious diseases": "Japanese Journal of Infectious Diseases",
}

def norm_journal(j):
    if not isinstance(j, str):
        return j
    key = j.strip().lower()
    return JOURNAL_NORMALIZE.get(key, j.strip())

rows = []
for _, r in final.iterrows():
    rec = {
        "source": r["source"], "title": r["title"], "year": r["year"],
        "authors": r["authors"], "journal": norm_journal(r["journal"]), "doi": r["doi"],
        "abstract": r["abstract"], "author_keywords": r["author_keywords"],
    }
    if r["source"] == "Scopus" and r["doi"] in sc_idx.index:
        row = sc_idx.loc[r["doi"]]
        if isinstance(row, pd.DataFrame):
            row = row.iloc[0]
        rec["cited_by"] = row.get("Cited by")
        rec["affiliations"] = row.get("Affiliations")
        rec["index_keywords"] = row.get("Index Keywords")
        rec["author_full_names"] = row.get("Author full names")
        rec["author_ids"] = row.get("Author(s) ID")
        rec["funding_details"] = row.get("Funding Details")
        rec["references"] = row.get("References")
    else:
        rec["cited_by"] = None
        rec["affiliations"] = None
        rec["index_keywords"] = None
        rec["author_full_names"] = None
        rec["author_ids"] = None
        rec["funding_details"] = None
        rec["references"] = None
    rows.append(rec)

master = pd.DataFrame(rows)
master["cited_by"] = pd.to_numeric(master["cited_by"], errors="coerce").fillna(0).astype(int)
master["year"] = pd.to_numeric(master["year"], errors="coerce").astype("Int64")
master.to_csv(f"{OUT_DIR}/master_final.csv", index=False)
print("Master dataset:", len(master))
print(master["source"].value_counts())
print("Records with abstract:", (master["abstract"].fillna("").str.len() > 0).sum())
print("Records with author_keywords:", (master["author_keywords"].fillna("").str.len() > 0).sum())
print("Records with affiliations:", (master["affiliations"].fillna("").str.len() > 0).sum())
print("Records with funding_details:", (master["funding_details"].fillna("").str.len() > 0).sum())
print("Year range:", master["year"].min(), "-", master["year"].max())
print("\nTop 10 journals after normalization:")
print(master["journal"].value_counts().head(10))
