# Malaria and NTD research in Myanmar (2000–2026): bibliometric analysis — replication package

Code and data to reproduce every value, table, and figure in the manuscript
**"Malaria and neglected tropical disease research in Myanmar (2000–2026): a bibliometric
analysis of research trends, collaboration, and gaps"** (S. M. Arnt).

## Contents
- `data/final_included_dataset_n1215.csv` — the 1,215 screened, included records (the analysis dataset).
- `data/scopus_vosviewer_export.csv` — Scopus-format export (1,191 records) used as VOSviewer input.
- `scripts/01–09_*.py` — the original pipeline: deduplication, topical screening, master-dataset
  build, core bibliometric analysis, author disambiguation, disease stratification, per-disease/
  temporal analysis, and co-authorship verification.
- `scripts/10_final_analysis.py` — authoritative single-source recomputation (n = 1,215): annual
  production, journals/Bradford, countries, institutions, funders, citations, disease stratification,
  per-disease and temporal tables.
- `scripts/11_disambiguation.py` — author name disambiguation (union-find, distinct-document counts).
- `scripts/12_figures.py`, `scripts/13_prisma_abstract.py` — figure generation.
- `results/` — computed outputs: `ALL_STATS.json` and the per-table CSVs.
- `vosviewer/` — raw VOSviewer map and network files for the keyword co-occurrence and
  co-authorship analyses.

## Final dataset definition (n = 1,215)
2,690 identified (PubMed 1,242 + Scopus 1,448) → 1,402 after deduplication → 1,226 after topical
screen → 1,220 after discipline-scope verification → **1,215** after removing 2 non-research
articles and 3 non-peer-reviewed preprints (which also resolved a suspected duplicate-study pair).
Citation analyses use the 1,191 Scopus-indexed records only.

## Reproduce
```bash
pip install pandas numpy matplotlib
cd scripts
python 10_final_analysis.py ../data/final_included_dataset_n1215.csv   # writes results/
python 11_disambiguation.py                                            # author counts + Lotka
python 12_figures.py                                                   # data figures
python 13_prisma_abstract.py                                           # PRISMA + graphical abstract
```
Network maps (keyword co-occurrence, co-authorship) were generated in VOSviewer 1.6.21 from
`data/scopus_vosviewer_export.csv`; the resulting map/network files are in `vosviewer/`.

## License
Released for scientific reproducibility. Source bibliographic records are from PubMed/MEDLINE
(open) and Scopus (subscription); please observe those providers' terms.
