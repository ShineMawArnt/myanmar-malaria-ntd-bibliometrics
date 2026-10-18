"""
10_final_analysis.py  — single-source recomputation of every statistic reported in the
revised manuscript, starting from final_included_dataset_n1220_updated.csv.

Final-dataset definition (n = 1,215):
  1,220 records after discipline-scope verification
  - 2 non-research-article records (PLoS Med Perspective; GHSP Editorial)
  - 3 preprint-server records (Research Square x2, bioRxiv) that were not peer-reviewed
    and are inconsistent with the Scopus 'Article' document-type restriction; this also
    removes the suspected duplicate-study pair disclosed in the Limitations.
Citation analyses use Scopus-sourced records only (n = 1,191); PubMed-only records carry
no citation count in the export (they were stored as 0, which would bias means).
"""
import json, re, unicodedata, sys
from collections import Counter, defaultdict
import numpy as np
import pandas as pd

SRC = sys.argv[1] if len(sys.argv) > 1 else 'data/41256de0-final_included_dataset_n1220_updated.csv'
OUT = 'work/stats'
import os; os.makedirs(OUT, exist_ok=True)

df = pd.read_csv(SRC, low_memory=False)
df['year'] = pd.to_numeric(df['year'], errors='coerce').astype(int)
df['cited_by'] = pd.to_numeric(df['cited_by'], errors='coerce').fillna(0).astype(int)
for c in ['abstract', 'author_keywords', 'affiliations', 'funding_details', 'author_full_names', 'authors', 'index_keywords', 'journal']:
    df[c] = df[c].fillna('').astype(str)

R = {}  # results
R['n_after_scope_verification'] = len(df)

# ---------------------------------------------------------------- exclusions
NONRESEARCH = ['Responding to AIDS, tuberculosis, malaria, and emerging infectious diseases in Burma',
               'Long-Lasting Insecticidal Nets for Malaria Control in Myanmar and Nigeria']
PREPRINT_JOURNALS = {'Res Sq', 'bioRxiv', 'medRxiv', 'SSRN', 'Preprints'}
df['excl_nonresearch'] = df['title'].apply(lambda t: any(t.startswith(x) for x in NONRESEARCH))
df['excl_preprint'] = df['journal'].isin(PREPRINT_JOURNALS)
R['excluded_nonresearch'] = int(df['excl_nonresearch'].sum())
R['excluded_preprint'] = int(df['excl_preprint'].sum())
R['excluded_titles'] = df[df.excl_nonresearch | df.excl_preprint][['title', 'journal', 'year']].to_dict('records')
df = df[~(df.excl_nonresearch | df.excl_preprint)].reset_index(drop=True)
N = len(df); R['n_final'] = N
R['n_by_source'] = df['source'].value_counts().to_dict()
df.to_csv(f'{OUT}/final_dataset_n{N}.csv', index=False)

# language note: bilingual (CJK) titles
cjk = df['title'].apply(lambda t: any('一' <= ch <= '鿿' or '぀' <= ch <= 'ヿ' for ch in t) or t.startswith('['))
R['n_cjk_or_bracketed_titles'] = int(cjk.sum())

# ---------------------------------------------------------------- completeness
R['completeness'] = {k: int((df[k].str.len() > 0).sum()) for k in ['abstract', 'author_keywords', 'affiliations', 'funding_details']}
R['completeness_pct'] = {k: round(v / N * 100, 1) for k, v in R['completeness'].items()}

# ---------------------------------------------------------------- annual production
yearly = df.groupby('year').size().reindex(range(2000, 2027), fill_value=0)
yearly.to_csv(f'{OUT}/annual_production.csv', header=['n_publications'])
R['annual'] = {int(k): int(v) for k, v in yearly.items()}
R['peak_year'] = int(yearly.idxmax()); R['peak_n'] = int(yearly.max())
R['n_2000_2009'] = int(yearly.loc[2000:2009].sum()); R['n_2010_2014'] = int(yearly.loc[2010:2014].sum())
R['n_2015_2019'] = int(yearly.loc[2015:2019].sum()); R['n_2020_2026'] = int(yearly.loc[2020:2026].sum())
R['n_2015_2025'] = int(yearly.loc[2015:2025].sum())
# compound annual growth rate 2000-2025 (full years) using 3-yr means at each end to damp noise
start = yearly.loc[2000:2002].mean(); end = yearly.loc[2023:2025].mean()
R['cagr_2001_2024_3yr_means'] = round(((end / start) ** (1 / (2024 - 2001)) - 1) * 100, 1)
R['mean_per_year_2015_2025'] = round(yearly.loc[2015:2025].mean(), 1)
R['min_2015_2025'] = int(yearly.loc[2015:2025].min()); R['max_2015_2025'] = int(yearly.loc[2015:2025].max())

# ---------------------------------------------------------------- journals + Bradford
JN = {'malar j': 'Malaria Journal', 'malaria journal': 'Malaria Journal',
      'am j trop med hyg': 'American Journal of Tropical Medicine and Hygiene',
      'trop med health': 'Tropical Medicine and Health', 'emerg infect dis': 'Emerging Infectious Diseases',
      'wellcome open res': 'Wellcome Open Research', 'parasite': 'Parasite', 'cureus': 'Cureus',
      'trop med infect dis': 'Tropical Medicine and Infectious Disease', 'plos one': 'PLoS ONE',
      'confl health': 'Conflict and Health', 'biomed res int': 'BioMed Research International',
      'acta med okayama': 'Acta Medica Okayama', 'parasite epidemiol control': 'Parasite Epidemiology and Control',
      'emerg microbes infect': 'Emerging Microbes and Infections', 'vaccines (basel)': 'Vaccines',
      'who south east asia j public health': 'WHO South-East Asia Journal of Public Health',
      'malariaworld j': 'MalariaWorld Journal',
      'nihon hansenbyo gakkai zasshi': 'Japanese Journal of Leprosy',
      'nihon hansenbyō gakkai zasshi = japanese journal of leprosy : official organ of the japanese leprosy association': 'Japanese Journal of Leprosy',
      'plos neglected tropical diseases': 'PLoS Neglected Tropical Diseases'}
def nj(j):
    k = j.strip().lower()
    return JN.get(k, j.strip())
df['journal_n'] = df['journal'].apply(nj)
jc = df['journal_n'].value_counts()
R['n_journals'] = int(jc.size)
jc.head(15).to_csv(f'{OUT}/top_journals.csv', header=['n_publications'])
R['top_journals'] = [(k, int(v)) for k, v in jc.head(15).items()]
R['malaria_journal_pct'] = round(jc.iloc[0] / N * 100, 1)
# Bradford: three zones with ~equal document counts
cum = jc.cumsum(); third = N / 3
z1 = int((cum < third).sum()) + 1
z2 = int((cum < 2 * third).sum()) + 1 - z1
z3 = int(jc.size - z1 - z2)
R['bradford'] = {'zone1_journals': z1, 'zone1_docs': int(jc.iloc[:z1].sum()),
                 'zone2_journals': z2, 'zone2_docs': int(jc.iloc[z1:z1 + z2].sum()),
                 'zone3_journals': z3, 'zone3_docs': int(jc.iloc[z1 + z2:].sum()),
                 'zone1_pct_docs': round(jc.iloc[:z1].sum() / N * 100, 1),
                 'journals_with_1_doc': int((jc == 1).sum())}
pd.DataFrame({'rank': range(1, jc.size + 1), 'journal': jc.index, 'n': jc.values, 'cum': cum.values}).to_csv(f'{OUT}/bradford_rank.csv', index=False)

# ---------------------------------------------------------------- author disambiguation (Section 2.7.1 algorithm)
def tokens_of(name):
    if ',' not in name: return None, None
    last, first = name.split(',', 1)
    last_n = unicodedata.normalize('NFKD', last).encode('ascii', 'ignore').decode().strip().lower()
    first_n = unicodedata.normalize('NFKD', first).encode('ascii', 'ignore').decode().strip()
    toks = [t.strip('.').lower() for t in re.split(r'[\s\-]+', first_n) if t.strip('.')]
    return last_n, toks
def compatible(a, b):
    if len(a) != len(b): return False
    for x, y in zip(a, b):
        if x == y: continue
        if len(x) == 1 and y.startswith(x): continue
        if len(y) == 1 and x.startswith(y): continue
        return False
    return True
author_counter = Counter(); paper_authors = []
for names in df['author_full_names']:
    lst = []
    for a in names.split(';'):
        a = re.sub(r'\s*\(\d+\)\s*', '', a.strip()).strip()
        if a: author_counter[a] += 1; lst.append(a)
    paper_authors.append(lst)
parsed = {n: tokens_of(n) for n in author_counter}
by_last = defaultdict(list)
for n, (l, t) in parsed.items():
    if l is not None: by_last[l].append(n)
merge_map = {}; groups = []
for l, names in by_last.items():
    ns = sorted(names, key=lambda x: -author_counter[x]); used = set()
    for i, ni in enumerate(ns):
        if ni in used: continue
        g = [ni]
        for nj_ in ns[i + 1:]:
            if nj_ in used: continue
            if compatible(parsed[ni][1], parsed[nj_][1]): g.append(nj_); used.add(nj_)
        if len(g) > 1:
            groups.append(g); used.add(ni)
            for x in g: merge_map[x] = g[0]
merge_map['Nosten, François H.'] = 'Nosten, François'  # manually verified same individual
def canon(a): return merge_map.get(a, a)
merged = Counter()
for a, c in author_counter.items(): merged[canon(a)] += c
R['authors_pre'] = len(author_counter); R['authors_post'] = len(merged); R['merge_groups'] = len(groups)
R['top_authors'] = [(k, int(v)) for k, v in merged.most_common(15)]
pd.DataFrame(R['top_authors'], columns=['author', 'n_publications']).to_csv(f'{OUT}/top_authors.csv', index=False)
# Lotka
prod = Counter(merged.values())
R['lotka'] = {'single_pub': int(prod[1]), 'single_pub_pct': round(prod[1] / len(merged) * 100, 1),
              'two_pub_pct': round(prod[2] / len(merged) * 100, 1),
              'ge10_pub': int(sum(v for k, v in prod.items() if k >= 10)),
              'pre_single_pub_pct': round(Counter(author_counter.values())[1] / len(author_counter) * 100, 1)}
# Lotka exponent by OLS on log-log (Pao's method approximation, x = 1..max with nonzero y)
xs = np.array(sorted(k for k in prod if prod[k] > 0)); ys = np.array([prod[k] for k in xs])
b, a = np.polyfit(np.log10(xs), np.log10(ys), 1)
R['lotka']['exponent_ols'] = round(-b, 2); R['lotka']['r2'] = round(np.corrcoef(np.log10(xs), np.log10(ys))[0, 1] ** 2, 3)
pd.DataFrame({'n_pubs': xs, 'n_authors': ys}).to_csv(f'{OUT}/lotka_distribution.csv', index=False)
# collaboration
n_auth = df['authors'].apply(lambda s: len([a for a in s.split(';') if a.strip()]))
multi = n_auth[n_auth > 1]
R['collab'] = {'single_authored': int((n_auth == 1).sum()), 'single_pct': round((n_auth == 1).mean() * 100, 1),
               'mean_authors': round(n_auth.mean(), 2), 'median_authors': float(n_auth.median()),
               'max_authors': int(n_auth.max()), 'collaboration_index': round(multi.sum() / len(multi), 2),
               'ge10_authors_pct': round((n_auth >= 10).mean() * 100, 1), 'gt25_authors': int((n_auth > 25).sum())}

# ---------------------------------------------------------------- countries (full counting, normalized)
CNORM = {'UK': 'United Kingdom', 'USA': 'United States', 'PR China': 'China',
         "People's Republic of China": 'China', 'Viet Nam': 'Vietnam',
         'Russian Federation': 'Russia', 'Hong Kong': 'China', 'Macao': 'China', 'Macau': 'China'}
def countries_of(aff):
    out = set()
    for p in aff.split(';'):
        toks = [t.strip() for t in p.strip().split(',')]
        if toks:
            c = re.sub(r'\.$', '', toks[-1]).strip()
            c = re.sub(r'\s*&\s*amp.*$', '', c).strip()
            c = CNORM.get(c, c)
            if c and len(c) < 30 and not any(ch.isdigit() for ch in c) and 'PMC' not in c and 'consultant' not in c.lower() and 'Department' not in c and 'Ministry' not in c and 'Macdonald' not in c and 'MOH' != c and '(' not in c:
                out.add(c)
    return out
cc = Counter()
for aff in df['affiliations']:
    if aff: cc.update(countries_of(aff))
R['n_countries'] = len(cc)
R['top_countries'] = [(k, int(v)) for k, v in cc.most_common(20)]
pd.DataFrame(R['top_countries'], columns=['country', 'n_publications']).to_csv(f'{OUT}/top_countries.csv', index=False)

# ---------------------------------------------------------------- institutions (approximate)
INST_PAT = [('Mahidol University', r'mahidol university'),
            ('Centre for Tropical Medicine and Global Health (Oxford)', r'centre for tropical medicine and global health'),
            ('Department of Medical Research (Myanmar)', r'department of medical research'),
            ('Shoklo Malaria Research Unit', r'shoklo malaria research unit|\bsmru\b'),
            ('Mahidol-Oxford Tropical Medicine Research Unit', r'mahidol-oxford|\bmoru\b'),
            ('Kunming Medical University', r'kunming medical university'),
            ('Yunnan Institute of Parasitic Diseases', r'yunnan institute of parasitic diseases'),
            ('National Institute of Parasitic Diseases (China CDC)', r'national institute of parasitic diseases'),
            ('University of Oxford', r'university of oxford'),
            ('University of California', r'university of california'),
            ('Pennsylvania State University', r'pennsylvania state university|penn state'),
            ('London School of Hygiene & Tropical Medicine', r'london school of hygiene'),
            ('University of Yangon / Univ. of Medicine (Myanmar)', r'university of medicine.{0,40}(yangon|mandalay|myanmar)|university of yangon'),
            ('Thammasat University', r'thammasat university'),
            ('Chinese Academy of ', r'chinese academy of')]
inst_counts = {}
low_aff = df['affiliations'].str.lower()
for name, pat in INST_PAT:
    inst_counts[name] = int(low_aff.str.contains(pat, regex=True, na=False).sum())
inst_sorted = sorted(inst_counts.items(), key=lambda x: -x[1])
R['top_institutions'] = inst_sorted
pd.DataFrame(inst_sorted, columns=['institution', 'n_publications']).to_csv(f'{OUT}/top_institutions.csv', index=False)

# ---------------------------------------------------------------- funders
FUND_PAT = [('National Institute of Allergy and Infectious Diseases', r'national institute of allergy|niaid'),
            ('Wellcome Trust', r'wellcome'),
            ('Bill & Melinda Gates Foundation', r'gates foundation|bill and melinda gates|bill & melinda gates'),
            ('National Institutes of Health (US)', r'national institutes of health|\bnih\b'),
            ('National Natural Science Foundation of China', r'national natural science foundation of china|nsfc'),
            ('National Health and Medical Research Council (Australia)', r'national health and medical research council|nhmrc'),
            ('Mahidol University', r'mahidol university'),
            ('Fogarty International Center', r'fogarty'),
            ('World Health Organization', r'world health organization|\bwho\b'),
            ('Global Fund', r'global fund'),
            ('Thailand Research Fund / NRCT', r'thailand research fund|national research council of thailand'),
            ('Japan Society for the Promotion of Science', r'japan society for the promotion of science|jsps'),
            ('Department for International Development (UK)', r'department for international development|dfid'),
            ('Japan Agency for Medical Research and Development', r'japan agency for medical research|amed'),
            ('National Research Foundation of Korea', r'national research foundation of korea')]
fund = df[df['funding_details'].str.len() > 0]
R['n_with_funding'] = len(fund); R['funding_pct'] = round(len(fund) / N * 100, 1)
low_f = fund['funding_details'].str.lower()
fc = {name: int(low_f.str.contains(pat, regex=True, na=False).sum()) for name, pat in FUND_PAT}
fc_sorted = sorted(fc.items(), key=lambda x: -x[1])
R['top_funders'] = fc_sorted
pd.DataFrame(fc_sorted, columns=['funder', 'n_records']).to_csv(f'{OUT}/top_funders.csv', index=False)

# ---------------------------------------------------------------- citation impact (Scopus-only)
sc = df[df['source'] == 'Scopus'].copy()
R['n_scopus_for_citations'] = len(sc)
cites = sc['cited_by']
R['citations'] = {'total': int(cites.sum()), 'mean': round(cites.mean(), 1), 'median': float(cites.median()),
                  'zero_cited': int((cites == 0).sum()), 'zero_pct': round((cites == 0).mean() * 100, 1)}
cs = sorted(cites.tolist(), reverse=True); h = 0
for i, c in enumerate(cs, 1):
    if c >= i: h = i
R['citations']['h_index'] = h
# age-normalized
sc = sc.assign(age=2026.54 - sc['year'])
sc = sc.assign(cpy=sc['cited_by'] / sc['age'].clip(lower=0.5))
R['citations']['mean_cpy'] = round(sc['cpy'].mean(), 2); R['citations']['median_cpy'] = round(sc['cpy'].median(), 2)
R['citations']['pre2015_cpy'] = round(sc[sc.year < 2015]['cpy'].mean(), 2)
R['citations']['post2020_cpy'] = round(sc[sc.year >= 2020]['cpy'].mean(), 2)
top_cited = sc.sort_values('cited_by', ascending=False)[['title', 'year', 'journal_n', 'cited_by']].head(15)
top_cited.to_csv(f'{OUT}/top_cited.csv', index=False)
R['top_cited'] = top_cited.to_dict('records')
# histogram bins
bins = [0, 1, 5, 10, 20, 50, 100, 250, 500, 1000, 1e9]; labels = ['0', '1-4', '5-9', '10-19', '20-49', '50-99', '100-249', '250-499', '500-999', '1000+']
hist = pd.cut(cites, bins=bins, right=False, labels=labels).value_counts().reindex(labels)
hist.to_csv(f'{OUT}/citation_histogram.csv', header=['n_documents'])
R['citation_histogram'] = {k: int(v) for k, v in hist.items()}

# ---------------------------------------------------------------- disease stratification
MAL = re.compile(r'\bmalaria\b|\bplasmodium\b|\bartemisinin\b|\bartesunate\b|\bchloroquine\b|\bprimaquine\b', re.I)
NTD_TERMS = ['dengue', 'chikungunya', 'japanese encephalitis', 'leprosy', 'cholera', 'melioidosis', 'leptospir',
             'rickettsi', 'salmonell', 'shigell', 'amoebiasis', 'amebiasis', 'entamoeba', 'giardia', 'ascaris',
             'trichuris', 'hookworm', 'ancylostoma', 'necator', 'filaria', 'strongyloid', 'leishmania', 'helminth']
NTD = re.compile('|'.join(re.escape(t) for t in NTD_TERMS), re.I)
df['txt'] = (df['title'] + ' ' + df['abstract'] + ' ' + df['author_keywords'])
def classify(t):
    m, n = bool(MAL.search(t)), bool(NTD.search(t))
    return 'Both' if (m and n) else 'Malaria only' if m else 'NTD only' if n else 'Unclassified'
df['cat'] = df['txt'].apply(classify)
vc = df['cat'].value_counts()
R['stratification'] = {k: int(vc.get(k, 0)) for k in ['Malaria only', 'NTD only', 'Both', 'Unclassified']}
R['stratification_pct'] = {k: round(vc.get(k, 0) / N * 100, 1) for k in ['Malaria only', 'NTD only', 'Both', 'Unclassified']}
# two-way comparison table
def grp_stats(sub):
    scs = sub[sub.source == 'Scopus']
    return {'n': len(sub), 'pct': round(len(sub) / N * 100, 1), 'total_cites': int(scs['cited_by'].sum()),
            'mean_cites': round(scs['cited_by'].mean(), 1) if len(scs) else 0, 'median_cites': float(scs['cited_by'].median()) if len(scs) else 0,
            'journals': int(sub['journal_n'].nunique()), 'countries': len(set().union(*[countries_of(a) for a in sub['affiliations'] if a]) if any(sub['affiliations']) else set())}
R['tab2'] = {'Malaria only': grp_stats(df[df.cat == 'Malaria only']), 'NTD only': grp_stats(df[df.cat == 'NTD only'])}

# per-disease
PERIODS = [(2000, 2009, '2000-2009'), (2010, 2014, '2010-2014'), (2015, 2019, '2015-2019'), (2020, 2026, '2020-2026')]
DIS = {'Dengue': r'\bdengue\b', 'Chikungunya': r'\bchikungunya\b', 'Japanese encephalitis': r'\bjapanese encephalitis\b',
       'Leprosy': r'\bleprosy\b|\bhansen', 'Cholera': r'\bcholera\b|\bvibrio cholerae\b',
       'Melioidosis': r'\bmelioidosis\b|burkholderia pseudomallei', 'Leptospirosis': r'\bleptospir', 'Rickettsioses': r'\brickettsi',
       'Salmonellosis': r'\bsalmonell', 'Shigellosis': r'\bshigell', 'Amoebiasis': r'\bamoebiasis\b|\bamebiasis\b|\bentamoeba\b',
       'Giardiasis': r'\bgiardia', 'Leishmaniasis': r'\bleishmania', 'Ascariasis': r'\bascaris|\bascariasis\b',
       'Trichuriasis': r'\btrichuris|\btrichuriasis\b', 'Hookworm': r'\bhookworm\b|\bancylostoma\b|\bnecator\b',
       'Filariasis': r'\bfilaria', 'Strongyloidiasis': r'\bstrongyloid'}
rows = []; permat = {}
for name, pat in DIS.items():
    rx = re.compile(pat, re.I); mask = df['txt'].apply(lambda t: bool(rx.search(t)))
    sub = df[mask]; scs = sub[sub.source == 'Scopus']; n = len(sub)
    early = int((sub['year'] <= 2012).sum()); late = int((sub['year'] >= 2013).sum())
    er, lr = early / 13, late / 14
    trend = 'n/a (n<5)' if n < 5 else 'Increasing' if lr > er * 1.3 else 'Decreasing' if lr < er * 0.7 else 'Stable'
    rows.append([name, n, round(n / N * 100, 1), int(scs['cited_by'].sum()), round(scs['cited_by'].mean(), 1) if len(scs) else 0,
                 len(set().union(*[countries_of(a) for a in sub['affiliations'] if a]) if any(sub['affiliations']) else set()), early, late, trend])
    permat[name] = [int(((sub.year >= s) & (sub.year <= e)).sum()) for s, e, _ in PERIODS]
pd_df = pd.DataFrame(rows, columns=['Disease', 'N', 'Pct', 'TotalCites', 'MeanCites', 'Countries', 'N_2000_2012', 'N_2013_2026', 'Trend']).sort_values('N', ascending=False)
pd_df.to_csv(f'{OUT}/per_disease.csv', index=False)
R['per_disease'] = pd_df.to_dict('records')
pm_df = pd.DataFrame(permat, index=[p[2] for p in PERIODS]).T.loc[pd_df['Disease']]
pm_df.to_csv(f'{OUT}/per_disease_by_period.csv')

# temporal composition
comp = []
for s, e, lab in PERIODS:
    sub = df[(df.year >= s) & (df.year <= e)]; v = sub['cat'].value_counts()
    comp.append({'Period': lab, 'Total': len(sub), 'Malaria_only': int(v.get('Malaria only', 0)), 'NTD_only': int(v.get('NTD only', 0)),
                 'Both': int(v.get('Both', 0)), 'Unclassified': int(v.get('Unclassified', 0)), 'Pct_NTD_only': round(v.get('NTD only', 0) / len(sub) * 100, 1)})
comp_df = pd.DataFrame(comp); comp_df.to_csv(f'{OUT}/temporal_composition.csv', index=False)
R['temporal'] = comp_df.to_dict('records')

json.dump(R, open(f'{OUT}/ALL_STATS.json', 'w'), indent=2, default=str)
print('N final =', N, '| Scopus', R['n_by_source'].get('Scopus'), '| PubMed', R['n_by_source'].get('PubMed'))
print('journals', R['n_journals'], '| authors', R['authors_post'], '| countries', R['n_countries'])
print('citations', R['citations']['total'], 'h', R['citations']['h_index'])
print('strat', R['stratification'])
print('bradford z1', R['bradford']['zone1_journals'], R['bradford']['zone1_pct_docs'], '%')
print('lotka single%', R['lotka']['single_pub_pct'], 'exp', R['lotka']['exponent_ols'])
print('peak', R['peak_year'], R['peak_n'])
