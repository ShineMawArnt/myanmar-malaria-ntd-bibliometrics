import pandas as pd
import re
from collections import Counter

df = pd.read_csv('master_final.csv')
df['year'] = pd.to_numeric(df['year'], errors='coerce').astype('Int64')
df['cited_by'] = pd.to_numeric(df['cited_by'], errors='coerce').fillna(0).astype(int)

DISEASES = {
    "Dengue": r"\bdengue\b",
    "Chikungunya": r"\bchikungunya\b",
    "Japanese encephalitis": r"\bjapanese encephalitis\b",
    "Leprosy": r"\bleprosy\b",
    "Cholera": r"\bcholera\b|\bvibrio cholerae\b",
    "Melioidosis": r"\bmelioidosis\b|\bburkholderia pseudomallei\b",
    "Leptospirosis": r"\bleptospir",
    "Rickettsioses": r"\brickettsi",
    "Salmonellosis": r"\bsalmonell",
    "Shigellosis": r"\bshigell",
    "Amoebiasis": r"\bamoebiasis\b|\bamebiasis\b|\bentamoeba\b",
    "Giardiasis": r"\bgiardia",
    "Leishmaniasis": r"\bleishmania",
    "Ascariasis": r"\bascaris|\bascariasis\b",
    "Trichuriasis": r"\btrichuris|\btrichuriasis\b",
    "Hookworm": r"\bhookworm\b|\bancylostoma\b|\bnecator\b",
    "Filariasis": r"\bfilaria",
    "Strongyloidiasis": r"\bstrongyloid",
}

def get_countries(sub):
    countries = set()
    for aff in sub['affiliations'].dropna():
        for p in str(aff).split(';'):
            tokens = [t.strip() for t in p.strip().split(',')]
            if tokens:
                c = re.sub(r'\.$', '', tokens[-1]).strip()
                if c and len(c) < 40:
                    countries.add(c)
    return countries

PERIODS = [(2000,2009,"2000-2009"), (2010,2014,"2010-2014"), (2015,2019,"2015-2019"), (2020,2026,"2020-2026")]

rows = []
period_matrix = {}
for name, pattern in DISEASES.items():
    rx = re.compile(pattern, re.IGNORECASE)
    mask = df.apply(lambda r: bool(rx.search(f"{r['title']} {r['abstract']} {r['author_keywords']}")), axis=1)
    sub = df[mask]
    n = len(sub)
    pct = n / len(df) * 100
    cites = sub['cited_by'].sum()
    mean_cite = sub['cited_by'].mean() if n else 0
    countries = len(get_countries(sub))
    early = sub[sub['year'] <= 2012]['year'].count()
    late = sub[sub['year'] >= 2013]['year'].count()
    early_years, late_years = 13, 14
    early_rate, late_rate = early/early_years, late/late_years
    if n < 5:
        trend = "n/a"
    elif late_rate > early_rate * 1.3:
        trend = "Increasing"
    elif late_rate < early_rate * 0.7:
        trend = "Decreasing"
    else:
        trend = "Stable"
    rows.append([name, n, round(pct,1), int(cites), round(mean_cite,1), countries, early, late, trend])

    pcounts = []
    for (s,e,label) in PERIODS:
        pcounts.append(int(sub[(sub['year']>=s)&(sub['year']<=e)]['year'].count()))
    period_matrix[name] = pcounts

result = pd.DataFrame(rows, columns=["Disease","N","Pct","TotalCites","MeanCites","Countries","N_2000_2012","N_2013_2026","Trend"])
result = result.sort_values("N", ascending=False).reset_index(drop=True)
result.to_csv('per_disease_breakdown.csv', index=False)
print("=== PER-DISEASE BREAKDOWN ===")
print(result.to_string(index=False))

# Period matrix table (diseases x periods)
period_df = pd.DataFrame(period_matrix, index=[p[2] for p in PERIODS]).T
period_df = period_df.loc[result['Disease']]
period_df.to_csv('per_disease_by_period.csv')
print("\n=== PER-DISEASE BY PERIOD ===")
print(period_df.to_string())

# Malaria vs NTD overall by period (temporal evolution of the field's composition)
MALARIA_RE = re.compile(r'\bmalaria\b|\bplasmodium\b|\bartemisinin\b|\bartesunate\b|\bchloroquine\b|\bprimaquine\b', re.IGNORECASE)
NTD_TERMS_FIXED = ['dengue','chikungunya','japanese encephalitis','leprosy','cholera','melioidosis',
    'leptospir','rickettsi','salmonell','shigell','amoebiasis','amebiasis','entamoeba',
    'giardia','ascaris','trichuris','hookworm','ancylostoma','necator','filaria','strongyloid',
    'leishmania','helminth']
NTD_RE_FIXED = re.compile('|'.join(re.escape(t) for t in NTD_TERMS_FIXED), re.IGNORECASE)

def classify_fixed(row):
    text = f"{row['title']} {row['abstract']} {row['author_keywords']}"
    m = bool(MALARIA_RE.search(text))
    n = bool(NTD_RE_FIXED.search(text))
    if m and n: return 'Both'
    if m: return 'Malaria only'
    if n: return 'NTD only'
    return 'Unclassified'

df['disease_category_fixed'] = df.apply(classify_fixed, axis=1)
print("\n=== DISEASE STRATIFICATION AFTER REMOVING CRYPTOSPORIDIUM (helminth retained) ===")
print(df['disease_category_fixed'].value_counts())

period_composition = []
for (s,e,label) in PERIODS:
    sub = df[(df['year']>=s)&(df['year']<=e)]
    counts = sub['disease_category_fixed'].value_counts()
    period_composition.append({
        'Period': label,
        'Total': len(sub),
        'Malaria_only': int(counts.get('Malaria only',0)),
        'NTD_only': int(counts.get('NTD only',0)),
        'Both': int(counts.get('Both',0)),
        'Unclassified': int(counts.get('Unclassified',0)),
    })
comp_df = pd.DataFrame(period_composition)
comp_df['Pct_NTD_only'] = (comp_df['NTD_only']/comp_df['Total']*100).round(1)
comp_df.to_csv('temporal_composition_by_period.csv', index=False)
print("\n=== TEMPORAL COMPOSITION (malaria vs NTD share by period) ===")
print(comp_df.to_string(index=False))
