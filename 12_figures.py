"""12_figures.py — regenerate all manuscript figures on the final n=1,215 dataset."""
import json, numpy as np, pandas as pd
import matplotlib as mpl, matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

mpl.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11, 'axes.spines.top': False,
                     'axes.spines.right': False, 'axes.titlesize': 13, 'axes.titleweight': 'bold',
                     'figure.dpi': 300, 'savefig.dpi': 300, 'savefig.bbox': 'tight'})
NAVY='#1b3a5b'; TEAL='#2a9d8f'; AMBER='#e9a23b'; RED='#c1403d'; GREY='#9aa5b1'; BLUE='#3d6fb4'
R=json.load(open('work/stats/ALL_STATS.json')); OUT='out'
import os; os.makedirs(OUT,exist_ok=True)

# Fig: annual production
yr=R['annual']; years=list(range(2000,2027)); vals=[yr[str(y)] for y in years]
fig,ax=plt.subplots(figsize=(9,4.2))
bars=ax.bar(years,vals,color=[GREY if y==2026 else NAVY for y in years],width=0.74)
ax.set_xlabel('Year'); ax.set_ylabel('Publications'); ax.set_title('Annual scientific production, 2000–2026')
ax.annotate('2026 partial\n(to 15 Jul)',xy=(2026,38),xytext=(2023.2,74),fontsize=8.5,color='#555',
            arrowprops=dict(arrowstyle='->',color='#999',lw=0.8))
ax.margins(x=0.01); plt.savefig(f'{OUT}/fig3_annual_production.png'); plt.close()

# Fig: top journals
tj=R['top_journals'][:10][::-1]
fig,ax=plt.subplots(figsize=(8.2,4.4))
ax.barh([t[0] for t in tj],[t[1] for t in tj],color=NAVY)
for i,(n,v) in enumerate(tj): ax.text(v+2,i,str(v),va='center',fontsize=9)
ax.set_xlabel('Publications'); ax.set_title('Top 10 journals'); ax.margins(x=0.08)
plt.savefig(f'{OUT}/fig4_top_journals.png'); plt.close()

# Fig: Bradford
br=pd.read_csv('work/stats/bradford_rank.csv')
fig,ax=plt.subplots(figsize=(7.6,4.2))
ax.plot(np.log10(br['rank']),br['cum'],color=NAVY,lw=1.8)
z1=R['bradford']['zone1_journals']; z2=z1+R['bradford']['zone2_journals']
ax.axvline(np.log10(z1),ls='--',color=AMBER,lw=1); ax.axvline(np.log10(z2),ls='--',color=TEAL,lw=1)
ax.text(np.log10(z1)-0.05,R['n_final']*0.9,f'Zone 1\n{z1} journals\n{R["bradford"]["zone1_pct_docs"]}% of output',ha='right',fontsize=8.5,color=AMBER)
ax.set_xlabel('log10(journal rank)'); ax.set_ylabel('Cumulative documents'); ax.set_title('Journal concentration (Bradford-type)')
plt.savefig(f'{OUT}/fig5_bradford.png'); plt.close()

# Fig: top authors
ta=R['top_authors'][:10][::-1]
fig,ax=plt.subplots(figsize=(8,4.4))
ax.barh([t[0] for t in ta],[t[1] for t in ta],color=NAVY)
for i,(n,v) in enumerate(ta): ax.text(v+2,i,str(v),va='center',fontsize=9)
ax.set_xlabel('Publications'); ax.set_title('Top 10 authors (after name disambiguation)'); ax.margins(x=0.08)
plt.savefig(f'{OUT}/fig6_top_authors.png'); plt.close()

# Fig: Lotka
lk=pd.read_csv('work/stats/lotka_distribution.csv')
fig,ax=plt.subplots(figsize=(7,4.2))
ax.scatter(lk['n_pubs'],lk['n_authors'],color=NAVY,s=22,zorder=3)
x=np.logspace(0,np.log10(lk['n_pubs'].max()),50)
C=R['lotka']['single_pub']; a=R['lotka']['exponent_ols']
ax.plot(x,C*x**(-a),color=RED,lw=1.4,label=f"Lotka fit: n∝1/pubs^{a:.2f} (R²={R['lotka']['r2']})")
ax.set_xscale('log'); ax.set_yscale('log'); ax.set_xlabel('Publications per author'); ax.set_ylabel('Number of authors')
ax.set_title('Author productivity vs Lotka\'s Law'); ax.legend(fontsize=8.5,frameon=False)
plt.savefig(f'{OUT}/fig7_lotka.png'); plt.close()

# Fig: institutions
ti=R['top_institutions'][:10][::-1]
fig,ax=plt.subplots(figsize=(8.6,4.6))
ax.barh([t[0] for t in ti],[t[1] for t in ti],color=NAVY)
for i,(n,v) in enumerate(ti): ax.text(v+3,i,str(v),va='center',fontsize=9)
ax.set_xlabel('Records (approximate, pattern-matched)'); ax.set_title('Top institutions'); ax.margins(x=0.10)
plt.savefig(f'{OUT}/fig8_institutions.png'); plt.close()

# Fig: funders
tf=R['top_funders'][:10][::-1]
fig,ax=plt.subplots(figsize=(8.8,4.6))
ax.barh([t[0] for t in tf],[t[1] for t in tf],color=NAVY)
for i,(n,v) in enumerate(tf): ax.text(v+2,i,str(v),va='center',fontsize=9)
ax.set_xlabel('Records acknowledging funder'); ax.set_title('Top funding bodies'); ax.margins(x=0.12)
plt.savefig(f'{OUT}/fig9_funders.png'); plt.close()

# Fig: countries
tc=R['top_countries'][:10][::-1]
fig,ax=plt.subplots(figsize=(8,4.4))
ax.barh([t[0] for t in tc],[t[1] for t in tc],color=NAVY)
for i,(n,v) in enumerate(tc): ax.text(v+4,i,str(v),va='center',fontsize=9)
ax.set_xlabel('Records with ≥1 author affiliation (full counting)'); ax.set_title('Top 10 contributing countries'); ax.margins(x=0.08)
plt.savefig(f'{OUT}/fig10_countries.png'); plt.close()

# Fig: citation distribution
ch=R['citation_histogram']; labels=list(ch.keys()); cv=list(ch.values())
fig,ax=plt.subplots(figsize=(8.4,4.2))
ax.bar(labels,cv,color=BLUE)
for i,v in enumerate(cv): ax.text(i,v+3,str(v),ha='center',fontsize=8)
ax.set_xlabel('Citations'); ax.set_ylabel('Documents'); ax.set_title(f'Citation distribution (Scopus-indexed records, n={R["n_scopus_for_citations"]:,})')
plt.savefig(f'{OUT}/fig11_citation_dist.png'); plt.close()

# Fig: per-disease
pdd=pd.read_csv('work/stats/per_disease.csv').sort_values('N')
cmap={'Increasing':BLUE,'Decreasing':RED,'Stable':GREY,'n/a (n<5)':GREY}
fig,ax=plt.subplots(figsize=(8.6,6))
ax.barh(pdd['Disease'],pdd['N'],color=[cmap[t] for t in pdd['Trend']])
for i,(n,v) in enumerate(zip(pdd['Disease'],pdd['N'])): ax.text(v+1.5,i,str(v),va='center',fontsize=8.5)
import matplotlib.patches as mp
ax.legend(handles=[mp.Patch(color=BLUE,label='Increasing (2013–26 vs 2000–12)'),mp.Patch(color=GREY,label='Stable / n<5'),mp.Patch(color=RED,label='Decreasing')],fontsize=8.5,loc='lower right',frameon=True)
ax.set_xlabel(f'Records (n={R["n_final"]:,} total; rows not mutually exclusive)'); ax.set_title('NTD records by disease, 2000–2026')
plt.savefig(f'{OUT}/fig12_per_disease.png'); plt.close()

# Fig: temporal composition stacked
tp=pd.read_csv('work/stats/temporal_composition.csv')
fig,ax=plt.subplots(figsize=(8.2,4.8))
periods=tp['Period']; bottom=np.zeros(len(tp))
for col,color,lab in [('Malaria_only',NAVY,'Malaria-only'),('NTD_only',TEAL,'NTD-only'),('Both',AMBER,'Both'),('Unclassified',GREY,'Unclassified')]:
    ax.bar(periods,tp[col],bottom=bottom,color=color,label=lab); bottom+=tp[col]
for i,row in tp.iterrows():
    ax.text(i,row['Total']+6,f"{row['Pct_NTD_only']}%\nNTD-only",ha='center',fontsize=8.5,color='#333')
ax.set_ylabel('Records'); ax.set_title('Composition of Myanmar malaria/NTD research by period'); ax.legend(fontsize=8.5,frameon=False,loc='upper left')
ax.margins(y=0.12)
plt.savefig(f'{OUT}/fig13_temporal_composition.png'); plt.close()
print('figures written:', sorted(os.listdir(OUT)))
