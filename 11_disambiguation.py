"""
11_disambiguation.py — improved, documented author-name disambiguation (replaces the
original same-token-length rule + ad-hoc manual merge, whose top count was not
reproducible from the final dataset).

Rule: group name-strings by NFKD-ASCII-folded surname; within a surname, two strings
are the SAME person if their given-name token lists are initial-compatible —
walking the shorter list against the longer position by position, each pair must be
equal OR one a single-letter initial prefixing the other, and every extra trailing
token in the longer list must itself be a single-letter initial (a middle initial).
This folds 'Nosten, François' / 'Nosten, François H.' and 'Kyaw, Myat Phone' /
'Kyaw, Myat P.', while still never merging 'Chen, Xi' with 'Chen, Xinyue' or
'Chen, Xiaoguang' (a 2+-letter token is never treated as an initial). Components are
formed by union-find; each author's productivity is the number of DISTINCT documents
containing any of their variants (a paper listing two variants counts once).
Counts use Scopus 'Author full names' (PubMed-only records, n=24, lack this field).
"""
import re, unicodedata, json
from collections import defaultdict, Counter
import numpy as np, pandas as pd

df = pd.read_csv('work/stats/final_dataset_n1215.csv', low_memory=False)
df['author_full_names'] = df['author_full_names'].fillna('')
N = len(df)

def fold(s):
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()

def parse(name):
    if ',' not in name:
        return None, None
    last, first = name.split(',', 1)
    last_n = fold(last).strip().lower()
    toks = [t.strip('.').lower() for t in re.split(r'[\s\-]+', fold(first).strip()) if t.strip('.')]
    return last_n, toks

def compatible(a, b):
    """initial-compatible given-token lists (a,b order-independent)."""
    if not a or not b:
        return a == b
    short, long = (a, b) if len(a) <= len(b) else (b, a)
    for x, y in zip(short, long):
        if x == y:
            continue
        if len(x) == 1 and y.startswith(x):
            continue
        if len(y) == 1 and x.startswith(y):
            continue
        return False
    # extra trailing tokens in the longer list must be middle initials
    for extra in long[len(short):]:
        if len(extra) != 1:
            return False
    return True

# gather distinct name-strings and their document memberships
occ = Counter()
name_docs = defaultdict(set)
for di, names in enumerate(df['author_full_names']):
    for a in names.split(';'):
        a = re.sub(r'\s*\(\d+\)\s*', '', a.strip()).strip()
        if a:
            occ[a] += 1
            name_docs[a].add(di)

parsed = {n: parse(n) for n in occ}
by_last = defaultdict(list)
for n, (l, t) in parsed.items():
    if l is not None:
        by_last[l].append(n)

parent = {n: n for n in occ}
def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]; x = parent[x]
    return x
def union(x, y):
    rx, ry = find(x), find(y)
    if rx != ry: parent[rx] = ry

for last, names in by_last.items():
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            if compatible(parsed[names[i]][1], parsed[names[j]][1]):
                union(names[i], names[j])

comp_docs = defaultdict(set)   # canonical -> set of doc indices
comp_label = {}                # canonical -> display name (most frequent variant)
comp_members = defaultdict(list)
for n in occ:
    c = find(n)
    comp_docs[c] |= name_docs[n]
    comp_members[c].append(n)
for c, members in comp_members.items():
    comp_label[c] = max(members, key=lambda m: occ[m])

prod = {comp_label[c]: len(docs) for c, docs in comp_docs.items()}
prod_counter = Counter(prod)

n_pre = len(occ); n_post = len(comp_docs)
R = {'authors_pre': n_pre, 'authors_post': n_post,
     'merge_groups': sum(1 for c in comp_members if len(comp_members[c]) > 1)}
top = prod_counter.most_common(15)
R['top_authors'] = [(k, int(v)) for k, v in top]

# Lotka on distinct-document productivity
dist = Counter(prod.values())
xs = np.array(sorted(dist)); ys = np.array([dist[x] for x in xs])
b, a = np.polyfit(np.log10(xs), np.log10(ys), 1)
R['lotka'] = {'single_pub': int(dist[1]), 'single_pub_pct': round(dist[1] / n_post * 100, 1),
              'two_pub_pct': round(dist[2] / n_post * 100, 1),
              'ge10': int(sum(v for k, v in dist.items() if k >= 10)),
              'exponent_ols': round(-b, 2), 'r2': round(np.corrcoef(np.log10(xs), np.log10(ys))[0, 1] ** 2, 3),
              'pre_single_pub_pct': round(Counter(occ.values())[1] / n_pre * 100, 1)}

pd.DataFrame(top, columns=['author', 'n_publications']).to_csv('work/stats/top_authors.csv', index=False)
pd.DataFrame({'n_pubs': xs, 'n_authors': ys}).to_csv('work/stats/lotka_distribution.csv', index=False)
# show variant folding for the leaders
for c in sorted(comp_docs, key=lambda c: -len(comp_docs[c]))[:6]:
    print(f"{len(comp_docs[c]):>4}  {comp_label[c]:<22}  <= {comp_members[c]}")
print(json.dumps({k: R[k] for k in ['authors_pre', 'authors_post', 'merge_groups', 'lotka']}, indent=2, default=str))
json.dump(R, open('work/stats/disambiguation.json', 'w'), indent=2, default=str)
