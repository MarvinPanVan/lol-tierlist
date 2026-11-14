import os; os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # run from anywhere; paths are relative to pipeline/
import pandas as pd, numpy as np, sys
sys.path.insert(0,'./scripts')
from model import role_table
def draft(role):
    t=role_table(role)
    t=t[(t.coverage>=0.5)&(t.pick_g>0)]          # must appear in global + most regions
    regs=t[['global','euw','kr','na']]
    t['min_reg']=regs.min(axis=1)
    t['elo']=t['mplus']-regs.mean(axis=1)
    def tier(r):
        if r.pick_g<1.5 and r.score>=0.6: return 'NICHE'
        s=r.score
        if s>=1.15 and r.min_reg>0: return 'S'
        if s>=0.6: return 'A'
        if s>=0.15: return 'B'
        if s>=-0.45: return 'C'
        return 'D'
    t['draft']=t.apply(tier,axis=1)
    return t
if __name__=='__main__':
    pd.set_option('display.width',220)
    for r in sys.argv[1:]:
        t=draft(r)
        t.to_csv(f'./draft_{r}.csv')
        print('=====',r)
        cols=['draft','score','pick_g','ban_g','min_reg','elo','reg_spread','global','euw','kr','na','mplus','ll_tier']
        print(t[cols].round(2).to_string())
