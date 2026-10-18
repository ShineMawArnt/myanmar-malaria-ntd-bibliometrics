import pandas as pd
import re
import difflib
import json

UPLOAD_DIR = "/mnt/user-data/uploads"
OUT_DIR = "/home/claude/ntd_biblio"

pm = pd.read_csv(f"{UPLOAD_DIR}/csv-Myanmartia-set-3.csv", encoding="utf-8-sig", dtype=str)
sc = pd.read_csv(f"{UPLOAD_DIR}/export_4284dc95-557d-4a1a-9f98-fa2d1ad2d4a8_2026-07-15T045600_152412201.csv", encoding="utf-8-sig", dtype=str)

report = {}
report["raw_pubmed_n"] = len(pm)
report["raw_scopus_n"] = len(sc)

report["scopus_doctype_counts"] = sc["Document Type"].value_counts(dropna=False).to_dict()
sc_art = sc[sc["Document Type"].str.lower() == "article"].copy()
report["scopus_after_doctype_filter"] = len(sc_art)

def norm_title(t):
    if not isinstance(t, str):
        return ""
    t = t.lower()
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def norm_doi(d):
    if not isinstance(d, str) or d.strip() == "":
        return None
    d = d.strip().lower()
    d = re.sub(r"^https?://(dx\.)?doi\.org/", "", d)
    return d

pm_std = pd.DataFrame({
    "source": "PubMed",
    "title": pm["Title"],
    "title_norm": pm["Title"].apply(norm_title),
    "year": pd.to_numeric(pm["Publication Year"], errors="coerce"),
    "authors": pm["Authors"],
    "journal": pm["Journal/Book"],
    "doi": pm["DOI"].apply(norm_doi),
    "pmid": pm["PMID"],
    "abstract": "",
    "author_keywords": "",
})

sc_std = pd.DataFrame({
    "source": "Scopus",
    "title": sc_art["Title"],
    "title_norm": sc_art["Title"].apply(norm_title),
    "year": pd.to_numeric(sc_art["Year"], errors="coerce"),
    "authors": sc_art["Authors"],
    "journal": sc_art["Source title"],
    "doi": sc_art["DOI"].apply(norm_doi),
    "pmid": sc_art["PubMed ID"],
    "abstract": sc_art["Abstract"].fillna(""),
    "author_keywords": sc_art["Author Keywords"].fillna(""),
})

combined = pd.concat([pm_std, sc_std], ignore_index=True)
report["combined_before_dedup"] = len(combined)

combined["dup_group"] = None
doi_map = {}
for idx, row in combined.iterrows():
    if row["doi"]:
        doi_map.setdefault(row["doi"], []).append(idx)

to_drop = set()
for doi, idxs in doi_map.items():
    if len(idxs) > 1:
        srcs = combined.loc[idxs, "source"].tolist()
        if "Scopus" in srcs:
            survivor = [i for i in idxs if combined.loc[i, "source"] == "Scopus"][0]
        else:
            survivor = idxs[0]
        for i in idxs:
            if i != survivor:
                to_drop.add(i)

after_doi_dedup = combined.drop(index=to_drop).reset_index(drop=True)
report["removed_by_doi_dedup"] = len(to_drop)
report["after_doi_dedup_n"] = len(after_doi_dedup)

remaining = after_doi_dedup.copy()
pm_rows = remaining[remaining["source"] == "PubMed"]
sc_rows = remaining[remaining["source"] == "Scopus"]

fuzzy_drop = set()
fuzzy_pairs = []
for i, prow in pm_rows.iterrows():
    if not prow["title_norm"]:
        continue
    candidates = sc_rows
    if pd.notna(prow["year"]):
        candidates = sc_rows[(sc_rows["year"] >= prow["year"] - 1) & (sc_rows["year"] <= prow["year"] + 1)]
    best_ratio = 0
    best_j = None
    for j, srow in candidates.iterrows():
        if j in fuzzy_drop:
            continue
        if not srow["title_norm"]:
            continue
        ratio = difflib.SequenceMatcher(None, prow["title_norm"], srow["title_norm"]).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_j = j
    if best_ratio >= 0.90:
        fuzzy_drop.add(i)
        fuzzy_pairs.append((prow["title"], candidates.loc[best_j, "title"], round(best_ratio, 3)))

after_fuzzy_dedup = remaining.drop(index=fuzzy_drop).reset_index(drop=True)
report["removed_by_fuzzy_title_dedup"] = len(fuzzy_drop)
report["after_fuzzy_dedup_n"] = len(after_fuzzy_dedup)

after_fuzzy_dedup.to_csv(f"{OUT_DIR}/step1_deduplicated.csv", index=False)
with open(f"{OUT_DIR}/report_step1.json", "w") as f:
    json.dump(report, f, indent=2, default=str)
print(json.dumps(report, indent=2, default=str))
