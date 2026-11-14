import os; os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # run from anywhere; paths are relative to pipeline/
import json, re, pandas as pd, numpy as np
D='./data2'
data=json.load(open('tiers.json'))
ROLE={'top':'top','jungle':'jungle','mid':'mid','middle':'mid','adc':'adc','bottom':'adc','support':'support','utility':'support'}
def slug(s): return re.sub(r'[^a-z0-9]','',s.lower())
SPECIAL={'monkeyking':'Wukong','nunu':'Nunu & Willump','renata':'Renata Glasc'}
names={}
for r in data:
    for e in data[r]: names[slug(e['c'])]=e['c']
# also names from raw csvs
import glob
for f in glob.glob('./data/*.csv'):
    for c in pd.read_csv(f).champion: names[slug(c)]=c
def nm(s):
    s2=slug(s); return SPECIAL.get(s2, names.get(s2, s))
rows=[]
for line in open(f'{D}/ugg_d.txt'):
    c,r,t,w,p,b,g=line.strip().split(';'); rows.append(('ugg_d',ROLE[r],nm(c),t,float(w),float(p),float(b),int(g)))
for line in open(f'{D}/ugg_m.txt'):
    c,r,t,w,p,b,g=line.strip().split(';'); rows.append(('ugg_m',ROLE[r],nm(c),t,float(w),float(p),float(b),int(g)))
for line in open(f'{D}/dpm_d.txt'):
    parts=line.strip().split(';'); c,r=parts[1].split('|'); t=parts[3]; w=float(parts[4].strip('%')); p=float(parts[6].strip('%')); g=int(parts[7].replace('.',''))
    rows.append(('dpm_d',ROLE[r],nm(c),t,w,p,np.nan,g))
for line in open(f'{D}/blitz_d.txt'):
    t,rest=line.strip().split('=',1)
    for item in rest.split():
        c,r,w=item.split('/'); rows.append(('blitz_d',ROLE[r],nm(c),t,float(w),np.nan,np.nan,np.nan))
df=pd.DataFrame(rows,columns=['src','role','c','tier','win','pick','ban','games'])
# role averages: for sources with pick use pick-weighted mean; blitz: use games-free mean of champions also in ugg_d weighting by ugg_d pick
out={}
for (src,role),g in df.groupby(['src','role']):
    if src=='blitz_d':
        ref=df[(df.src=='ugg_d')&(df.role==role)].set_index('c')['pick']
        w=g.c.map(ref).fillna(0.3)
    else: w=g.pick
    m=(g.win*w).sum()/w.sum()
    for _,x in g.iterrows(): out[(src,role,x.c)]=(x.win-m, x.tier, x.pick, x.games)
# compare to OP.GG D+ / M+ deltas stored in tiers.json (dia, m)
comp={}
for src,key in [('ugg_d','dia'),('dpm_d','dia'),('blitz_d','dia'),('ugg_m','m')]:
    a=[];b=[]
    for r in data:
        for e in data[r]:
            k=(src,r,e['c'])
            if k in out and e.get(key) is not None: a.append(out[k][0]); b.append(e[key])
    comp[src]=(len(a), round(float(np.corrcoef(a,b)[0,1]),3), round(float(np.mean(np.abs(np.array(a)-np.array(b)))),2))
print('agreement with OP.GG (n, corr of deltas, mean abs diff pp):',comp)
# tier formula check: how much does each site's tier follow win rate vs pick rate (D+), using ugg_d WR/pick as reference
ref=df[df.src=='ugg_d'].set_index(['role','c'])
TV={'S+':6,'S':5,'A':4,'B':3,'C':2,'D':1}
for src in ['ugg_d','dpm_d','blitz_d']:
    s=df[df.src==src].copy(); s['tv']=s.tier.map(TV)
    s=s.join(ref[['win','pick']],on=['role','c'],rsuffix='_ref').dropna(subset=['tv','win_ref'])
    s['wd']=[out[('ugg_d',r,c)][0] if ('ugg_d',r,c) in out else np.nan for r,c in zip(s.role,s.c)]
    s=s.dropna(subset=['wd'])
    from scipy.stats import spearmanr
    print(src,'tier~winrate rho=%.2f  tier~log(pick) rho=%.2f  n=%d'%(spearmanr(s.tv,s.wd).correlation, spearmanr(s.tv,np.log(s.pick_ref)).correlation,len(s)))
# Mobalytics curated
mob=json.load(open(f'{D}/moba_highelo.json'))
mt=[];mw=[];mp=[]
for r,tiers in mob.items():
    for t,cs in tiers.items():
        for c in cs:
            k=('ugg_d',r,c)
            if k in out: mt.append({'S':3,'A':2,'B':1}[t]); mw.append(out[k][0]); mp.append(np.log(out[k][2]))
from scipy.stats import spearmanr
print('mobalytics curated tier~winrate rho=%.2f tier~log(pick) rho=%.2f n=%d'%(spearmanr(mt,mw).correlation,spearmanr(mt,mp).correlation,len(mt)))
json.dump({f'{k[0]}|{k[1]}|{k[2]}':[round(v[0],2),v[1],v[2],v[3] if v[3]==v[3] else None] for k,v in out.items()},open('./site_deltas.json','w'))
