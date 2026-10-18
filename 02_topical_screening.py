import pandas as pd
import re
import json

OUT_DIR = "/home/claude/ntd_biblio"
df = pd.read_csv(f"{OUT_DIR}/step1_deduplicated.csv")

MYANMAR_RE = re.compile(r"\b(myanmar|burma|burmese)\b", re.IGNORECASE)

DISEASE_TERMS = [
    "dengue", "chikungunya", "japanese encephalitis", "malaria", "plasmodium",
    "leprosy", "hansen's disease", "cholera", "vibrio cholerae", "melioidosis",
    "burkholderia pseudomallei", "leptospirosis", "leptospira", "rickettsi",
    "salmonellosis", "salmonella", "shigellosis", "shigella", "amoebiasis",
    "amebiasis", "entamoeba", "giardiasis", "giardia", "leishmaniasis",
    "leishmania", "ascariasis", "ascaris", "trichuriasis", "trichuris",
    "hookworm", "ancylostoma", "necator", "filariasis", "filaria",
    "strongyloidiasis", "strongyloides", "soil-transmitted helminth",
    "neglected tropical disease"
]
DISEASE_RE = re.compile("|".join(re.escape(t) for t in DISEASE_TERMS), re.IGNORECASE)

def has_myanmar(row):
    text = f"{row['title']} {row['abstract']}"
    return bool(MYANMAR_RE.search(str(text)))

def has_disease(row):
    text = f"{row['title']} {row['abstract']} {row['author_keywords']}"
    return bool(DISEASE_RE.search(str(text)))

df["flag_myanmar"] = df.apply(has_myanmar, axis=1)
df["flag_disease"] = df.apply(has_disease, axis=1)
df["auto_eligible"] = df["flag_myanmar"] & df["flag_disease"]

report = {
    "total_after_dedup": len(df),
    "pass_myanmar_check": int(df["flag_myanmar"].sum()),
    "pass_disease_check": int(df["flag_disease"].sum()),
    "auto_eligible": int(df["auto_eligible"].sum()),
    "auto_excluded": int((~df["auto_eligible"]).sum()),
    "excluded_no_myanmar": int((~df["flag_myanmar"]).sum()),
    "excluded_myanmar_but_no_disease": int(((~df["flag_disease"]) & (df["flag_myanmar"])).sum()),
}

excluded = df[~df["auto_eligible"]][["source", "title", "year", "journal", "flag_myanmar", "flag_disease"]]
excluded.to_csv(f"{OUT_DIR}/excluded_for_manual_review.csv", index=False)

included = df[df["auto_eligible"]].copy()
included.to_csv(f"{OUT_DIR}/step2_included.csv", index=False)

with open(f"{OUT_DIR}/report_step2.json", "w") as f:
    json.dump(report, f, indent=2)

print(json.dumps(report, indent=2))

no_disease = df[(~df["flag_disease"]) & (df["flag_myanmar"])]
print("\nSample: Myanmar mentioned but no disease term matched (n=%d):" % len(no_disease))
for t in no_disease["title"].head(15):
    print(" -", t)
