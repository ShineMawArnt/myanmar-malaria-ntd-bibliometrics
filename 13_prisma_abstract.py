import json, numpy as np, matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib as mpl
mpl.rcParams.update({'font.family':'DejaVu Sans','figure.dpi':300,'savefig.dpi':300,'savefig.bbox':'tight'})
NAVY='#1b3a5b'; TEAL='#2a9d8f'; BLUE='#3d6fb4'; GREY='#eef2f5'
R=json.load(open('work/stats/ALL_STATS.json')); OUT='out'

# ---------------- PRISMA
steps=[
 ("Records identified","PubMed (n = 1,242) + Scopus, Document Type = Article (n = 1,448)\nTotal = 2,690"),
 ("After deduplication","1,288 duplicates removed (DOI + fuzzy title)\nn = 1,402"),
 ("After first-pass topical screen","176 excluded (145 no Myanmar term; 31 no disease term)\nn = 1,226"),
 ("After discipline-scope verification","6 confirmed off-topic excluded (incl. 'Burmese python' snake report)\nn = 1,220"),
 ("After eligibility correction","5 excluded: 2 non-research articles (Perspective, Editorial)\n+ 3 non-peer-reviewed preprints (resolving the duplicate-study pair)\nn = 1,215"),
 ("Final included records","n = 1,215  (1,191 Scopus; 24 PubMed-only)"),
]
fig,ax=plt.subplots(figsize=(7.2,10)); ax.set_xlim(0,10); ax.set_ylim(0,len(steps)*2+0.5); ax.axis('off')
y=len(steps)*2-0.6
for i,(title,body) in enumerate(steps):
    final=i==len(steps)-1
    box=FancyBboxPatch((1.1,y-1.1),7.8,1.5,boxstyle="round,pad=0.08,rounding_size=0.12",
                       fc=TEAL if final else GREY,ec=NAVY,lw=1.3)
    ax.add_patch(box)
    ax.text(5,y-0.18,title,ha='center',va='center',fontweight='bold',fontsize=10.5,color=NAVY if not final else 'white')
    ax.text(5,y-0.72,body,ha='center',va='center',fontsize=8.3,color='#1a1a1a' if not final else 'white')
    if i<len(steps)-1:
        ax.add_patch(FancyArrowPatch((5,y-1.15),(5,y-1.55),arrowstyle='-|>',mutation_scale=16,color=NAVY,lw=1.3))
    y-=2
plt.savefig(f'{OUT}/fig2_prisma.png'); plt.close()

# ---------------- Graphical abstract
fig=plt.figure(figsize=(12.5,7.4)); gs=fig.add_gridspec(3,3,height_ratios=[0.5,1.25,1.1],hspace=0.55,wspace=0.35)
fig.suptitle('Malaria and Neglected Tropical Disease Research in Myanmar, 2000–2026',fontsize=17,fontweight='bold',y=0.99)
# data sources (top-left)
axa=fig.add_subplot(gs[0:2,0]); axa.axis('off')
axa.text(0,1.0,'DATA SOURCES',fontsize=13,fontweight='bold',color=NAVY,transform=axa.transAxes)
axa.text(0,0.80,'PubMed (n = 1,242)\n       +\nScopus (n = 1,448)\n\n        ↓\n\n1,215 included\n(PRISMA-informed screening;\n2,690 identified)',fontsize=11,transform=axa.transAxes,va='top')
axa.text(0,0.18,'DOMINANT THEMES',fontsize=13,fontweight='bold',color=NAVY,transform=axa.transAxes)
axa.text(0,0.04,'1. Plasmodium molecular\n    genetics / drug resistance\n2. Clinical antimalarial trials\n3. Epidemiological &\n    phylogenetic surveillance',fontsize=10.5,transform=axa.transAxes,va='top')
# annual (top-mid/right)
axb=fig.add_subplot(gs[0:2,1:]); yr=R['annual']; years=list(range(2000,2027)); vals=[yr[str(y)] for y in years]
axb.bar(years,vals,color=[ '#9aa5b1' if y==2026 else BLUE for y in years])
axb.set_title(f'Publication growth: 4 (2000) → {R["peak_n"]} ({R["peak_year"]} peak)',fontsize=12)
axb.spines[['top','right']].set_visible(False); axb.set_ylabel('Publications')
# countries (bottom-mid)
axc=fig.add_subplot(gs[2,1]); tc=R['top_countries'][:5][::-1]
axc.barh([t[0] for t in tc],[t[1] for t in tc],color=BLUE); axc.set_title('Top 5 countries by affiliation',fontsize=11)
axc.spines[['top','right']].set_visible(False)
# metrics (bottom-right)
axd=fig.add_subplot(gs[2,2]); axd.axis('off')
axd.text(0,1.0,'KEY METRICS',fontsize=13,fontweight='bold',color=NAVY,transform=axd.transAxes)
m=f"• 1,215 included articles ({R['stratification_pct']['Malaria only']}% malaria-only)\n• {R['n_journals']} journals\n• {R['authors_post']:,} distinct authors\n• {R['citations']['total']:,} citations (Scopus)\n• h-index = {R['citations']['h_index']}\n• Collaboration Index = {R['collab']['collaboration_index']}"
axd.text(0,0.84,m,fontsize=10.5,transform=axd.transAxes,va='top')
# conclusion band (bottom-left under data sources handled; add full-width caption)
fig.text(0.5,0.015,"Myanmar's malaria/NTD research is a large, high-impact field tied to the Greater Mekong Subregion artemisinin-resistance effort "
         f"({R['stratification_pct']['Malaria only']}% malaria-only). Myanmar-based institutions (Department of Medical Research) and a genuine Myanmar "
         "co-authorship cluster form a substantial part of the field, though international consortia (MORU, SMRU) remain dominant.",
         ha='center',fontsize=9,style='italic',wrap=True,bbox=dict(boxstyle='round',fc='#eaf2fb',ec=BLUE,lw=0.8))
plt.savefig(f'{OUT}/fig1_graphical_abstract.png'); plt.close()
print('PRISMA + graphical abstract written')
