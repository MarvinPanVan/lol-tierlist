import os; os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # run from anywhere; paths are relative to pipeline/
import pandas as pd, numpy as np, os, sys
BASE='./data'
roles=['top','jungle','mid','adc','support']
# estimated matches per patch-so-far per dataset (pick% sums to 200 per role, so champ games = pick/100*M)
M={'opgg_global_e':1.5e6,'opgg_euw_e':4.5e5,'opgg_kr_e':3.8e5,'opgg_na_e':2.0e5,'opgg_global_m':1.2e5}
W={'opgg_global_e':0.30,'opgg_euw_e':0.20,'opgg_kr_e':0.20,'opgg_na_e':0.10,'opgg_global_m':0.20}
TAU2=0.012**2              # prior SD of true champion WR deviation ~1.2pp
K=0.25/TAU2                # shrinkage constant in games (~1736)
SPEC=0.4                   # specialist (low pick rate) correction, pp per ln unit below 2% pick
def load(ds,role):
    f=f'{BASE}/{ds}_{role}.csv'
    return pd.read_csv(f).set_index('champion') if os.path.exists(f) else None
def role_table(role):
    frames={}
    for ds in M:
        d=load(ds,role)
        m=(d.win*d.pick).sum()/d.pick.sum()
        delta=d.win-m
        n=d.pick/100*M[ds]
        shr=delta*n/(n+K)
        spec=SPEC*np.log(np.maximum(1,2/d.pick))
        frames[ds]=pd.DataFrame({'d':delta,'adj':shr-spec,'pick':d.pick,'ban':d.ban,'n':n})
    champs=sorted(set().union(*[f.index for f in frames.values()]))
    out=[]
    for c in champs:
        num=den=0; row={'champion':c}
        for ds,f in frames.items():
            key=ds.replace('opgg_','').replace('_e','').replace('global_m','mplus')
            if c in f.index:
                num+=W[ds]*f.loc[c,'adj']; den+=W[ds]
                row[key]=round(f.loc[c,'d'],2)
            else: row[key]=np.nan
        row['score']=num/den
        row['coverage']=den
        g=frames['opgg_global_e']
        row['pick_g']=g.loc[c,'pick'] if c in g.index else 0.0
        row['ban_g']=g.loc[c,'ban'] if c in g.index else np.nan
        regs=[row[k] for k in ['global','euw','kr','na'] if not np.isnan(row[k])]
        row['reg_spread']=max(regs)-min(regs) if len(regs)>1 else np.nan
        out.append(row)
    t=pd.DataFrame(out).set_index('champion')
    ll=load('lolalytics_global_e',role)
    t['ll_tier']=ll['tier'].reindex(t.index).fillna('')
    return t.sort_values('score',ascending=False)
if __name__=='__main__':
    pd.set_option('display.width',200)
    for r in (sys.argv[1:] or roles):
        t=role_table(r)
        t.to_csv(f'./out_{r}.csv')
        print('=====',r)
        print(t.round(2).head(45).to_string())
