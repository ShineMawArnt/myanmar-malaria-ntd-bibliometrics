"""
05_author_name_disambiguation.py

Systematic author name-string disambiguation procedure described in manuscript
Section 7.7.1. Groups author name-strings by normalized surname, then merges
two name-strings only if every given-name token matches exactly, or one name's
token is a true single-letter initial consistent with the other's full token.

This conservative matching rule was adopted after an earlier, less conservative
prefix-matching version was found (via manual spot-checking) to incorrectly merge
distinct individuals sharing a surname and a short given-name prefix (e.g.,
"Chen, Xi", "Chen, Xinyue", and "Chen, Xiaoguang" were incorrectly merged by
that earlier version). See manuscript Limitations (Section 11) for a full
discussion of residual risk.
"""
import pandas as pd
import re
import unicodedata
from collections import Counter, defaultdict

df = pd.read_csv('master_final.csv')

author_counter = Counter()
for names in df['author_full_names'].dropna():
    for a in str(names).split(';'):
        a = a.strip()
        a_clean = re.sub(r'\s*\(\d+\)\s*', '', a).strip()
        if a_clean:
            author_counter[a_clean] += 1


def get_last_and_tokens(name):
    """Split 'Surname, Given Names' into (normalized_surname, [given_name_tokens])."""
    if ',' not in name:
        return None, None
    last, first = name.split(',', 1)
    last_n = unicodedata.normalize('NFKD', last).encode('ascii', 'ignore').decode().strip().lower()
    first_n = unicodedata.normalize('NFKD', first).encode('ascii', 'ignore').decode().strip()
    tokens = re.split(r'[\s\-]+', first_n)
    tokens = [t.strip('.').lower() for t in tokens if t.strip('.')]
    return last_n, tokens


def compatible(tokens_a, tokens_b):
    """Two token lists are compatible (same person) only if:
    - same number of given-name tokens, AND
    - every token pair matches exactly OR one is a true single-letter initial
      that is a prefix of the other (e.g. 'b' matches 'bin', but 'xi' does NOT
      match 'xinyue' since len('xi')==2, not a true initial).
    """
    if len(tokens_a) != len(tokens_b):
        return False
    for a, b in zip(tokens_a, tokens_b):
        if a == b:
            continue
        if len(a) == 1 and b.startswith(a):
            continue
        if len(b) == 1 and a.startswith(b):
            continue
        return False
    return True


parsed = {n: get_last_and_tokens(n) for n in author_counter}
by_last = defaultdict(list)
for name, (last, tok) in parsed.items():
    if last is not None:
        by_last[last].append(name)

merge_map = {}
groups_log = []
for last, names in by_last.items():
    names_sorted = sorted(names, key=lambda x: -author_counter[x])
    used = set()
    for i, ni in enumerate(names_sorted):
        if ni in used:
            continue
        group = [ni]
        for nj in names_sorted[i + 1:]:
            if nj in used:
                continue
            if compatible(parsed[ni][1], parsed[nj][1]):
                group.append(nj)
                used.add(nj)
        if len(group) > 1:
            groups_log.append(group)
            used.add(ni)
            for g in group:
                merge_map[g] = group[0]

merged = Counter()
for name, c in author_counter.items():
    merged[merge_map.get(name, name)] += c

# Manually verified correction: same individual, split only by middle-initial
# presence/absence, confirmed via independent knowledge of the field (SMRU PI).
if 'Nosten, François H.' in merged:
    merged['Nosten, François'] = merged.get('Nosten, François', 0) + merged.pop('Nosten, François H.')

print(f"Merge groups identified: {len(groups_log)}")
print(f"Distinct author name-strings before merge: {len(author_counter)}")
print(f"Distinct authors after algorithmic merge + 1 manual correction: {len(merged)}")

top15 = merged.most_common(15)
for name, count in top15:
    print(f"  {count:>4}  {name}")

pd.DataFrame(top15, columns=['author', 'n_publications']).to_csv('FINAL_top_authors.csv', index=False)
