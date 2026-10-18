"""
06_disease_stratification.py  (v2 -- corrected)

Post-hoc classification of included records as malaria-only, NTD-only, or both.
CHANGE FROM v1: "cryptosporidium" removed from NTD_TERMS. It does not appear in
Swe et al.'s (2023) named NTD list and matched zero records in the final dataset,
so this correction does not change the reported classification counts (still
884 / 304 / 30 / 2). "helminth" is retained as a generic catch-all: removing it
would misclassify one soil-transmitted-helminthiasis record as unclassified, and
it overlaps conceptually with the "soil-transmitted helminth" term already used
in topical-eligibility screening (see S3 in the manuscript Supplementary Material).
"""
import pandas as pd
import re

df = pd.read_csv('master_final.csv')

MALARIA_RE = re.compile(
    r'\bmalaria\b|\bplasmodium\b|\bartemisinin\b|\bartesunate\b|\bchloroquine\b|\bprimaquine\b',
    re.IGNORECASE
)
NTD_TERMS = [
    'dengue', 'chikungunya', 'japanese encephalitis', 'leprosy', 'cholera', 'melioidosis',
    'leptospir', 'rickettsi', 'salmonella', 'shigell', 'amoebiasis', 'amebiasis', 'entamoeba',
    'giardia', 'ascaris', 'trichuris', 'hookworm', 'ancylostoma', 'necator',
    'filaria', 'strongyloid', 'leishmania', 'helminth'
]
NTD_RE = re.compile('|'.join(re.escape(t) for t in NTD_TERMS), re.IGNORECASE)


def classify(row):
    text = str(f"{row['title']} {row['abstract']} {row['author_keywords']}")
    has_malaria = bool(MALARIA_RE.search(text))
    has_ntd = bool(NTD_RE.search(text))
    if has_malaria and has_ntd:
        return 'Both'
    elif has_malaria:
        return 'Malaria only'
    elif has_ntd:
        return 'NTD only'
    else:
        return 'Unclassified'


df['disease_category'] = df.apply(classify, axis=1)
print(df['disease_category'].value_counts())
print((df['disease_category'].value_counts(normalize=True) * 100).round(1))
