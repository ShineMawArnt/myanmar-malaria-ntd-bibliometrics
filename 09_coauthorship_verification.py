"""
09_coauthorship_verification.py

Independently verifies the manuscript's Figure 12 (keyword co-occurrence) and Figure 13
(co-authorship network) claims against the raw VOSviewer map/network output files, and
checks whether the Section 7.7.1 author-name-disambiguation algorithm -- applied to
productivity counts (Table/Figure 6) -- was also applied to the co-authorship network
construction (it was not; see manuscript Section 11, Limitations).

Confirms:
  - 5 keyword clusters, exact term/occurrence counts (179/9901, 180/7793, 205/6145,
    138/5767, 97/3402) match the manuscript exactly.
  - 17 co-authorship clusters, 748 nodes, top-5 cluster sizes and leading authors
    (Liu Hui/Xu Jian-wei; Cui Liwang/Yang Zhaoqing; Nosten/McGready; White/Imwong/Ashley;
    Kyaw Myat Phone/Thi Aung) match the manuscript exactly.

Finds (new): applying the Section 7.7.1 merge algorithm to the 748 co-authorship network
nodes identifies 13 same-individual name-variant pairs never merged in the network
construction, reducing the true distinct-node count to 735. 2 of these 13 pairs split
across different VOSviewer clusters.
"""
import pandas as pd
import re, unicodedata
from collections import defaultdict

coauth = pd.read_csv('coauthorship_map_file.txt', sep='\t', encoding='utf-8-sig')
kw = pd.read_csv('keyword_cooccurrence_map_file.txt', sep='\t', encoding='utf-8-sig')

print("=== KEYWORD CO-OCCURRENCE (Figure 12) ===")
print("Total nodes:", len(kw), " | clusters:", kw['cluster'].nunique())
summary = kw.groupby('cluster').agg(n_terms=('label','count'), total_occ=('weight<Occurrences>','sum')).sort_values('total_occ', ascending=False)
print(summary)

print("\n=== CO-AUTHORSHIP NETWORK (Figure 13) ===")
print("Total nodes:", len(coauth), " | clusters:", coauth['cluster'].nunique())
print(coauth['cluster'].value_counts().sort_values(ascending=False).head(5))

print("\n=== NAME-VARIANT MERGE CHECK (using Section 7.7.1's exact algorithm) ===")
labels = coauth['label'].str.strip('"').tolist()
docs = dict(zip(coauth['label'].str.strip('"'), coauth['weight<Documents>']))
clusters = dict(zip(coauth['label'].str.strip('"'), coauth['cluster']))

def get_last_and_tokens(name):
    if ',' not in name: return None, None
    last, first = name.split(',', 1)
    last_n = unicodedata.normalize('NFKD', last).encode('ascii', 'ignore').decode().strip().lower()
    first_n = unicodedata.normalize('NFKD', first).encode('ascii', 'ignore').decode().strip()
    tokens = [t.strip('.').lower() for t in re.split(r'[\s\-]+', first_n) if t.strip('.')]
    return last_n, tokens

def compatible(a, b):
    if len(a) != len(b): return False
    for x, y in zip(a, b):
        if x == y: continue
        if len(x)==1 and y.startswith(x): continue
        if len(y)==1 and x.startswith(y): continue
        return False
    return True

parsed = {n: get_last_and_tokens(n) for n in labels}
by_last = defaultdict(list)
for name,(last,tok) in parsed.items():
    if last is not None: by_last[last].append(name)

merge_groups = []
for last, names in by_last.items():
    names_sorted = sorted(names, key=lambda x: -docs.get(x,0))
    used = set()
    for i,ni in enumerate(names_sorted):
        if ni in used: continue
        group=[ni]
        for nj in names_sorted[i+1:]:
            if nj in used: continue
            if compatible(parsed[ni][1], parsed[nj][1]):
                group.append(nj); used.add(nj)
        if len(group)>1:
            merge_groups.append(group); used.add(ni)

print(f"Merge groups found: {len(merge_groups)}  (nodes: {len(labels)} -> {len(labels)-sum(len(g)-1 for g in merge_groups)})")
cross = [g for g in merge_groups if len(set(clusters[n] for n in g)) > 1]
print(f"Cross-cluster splits: {len(cross)}")
for g in sorted(merge_groups, key=lambda g: -sum(docs[n] for n in g)):
    print(f"  total={sum(docs[n] for n in g):>3}  " + " | ".join(f"{n} (c{clusters[n]}, n={docs[n]})" for n in g))
