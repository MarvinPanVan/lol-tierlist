import os; os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # run from anywhere; paths are relative to pipeline/
import json, numpy as np, pandas as pd
data=json.load(open('tiers.json'))
sd=json.load(open('site_deltas.json'))
mob=json.load(open('data2/moba_highelo.json'))
K=0.25/0.012**2
def shrink(d,n): return d*n/(n+K)
def spec(p): return 0.4*np.log(max(1,2/p)) if p else 0
def opgg(ds,role):
    o=pd.read_csv(f'data/{ds}_{role}.csv').set_index('champion'); m=(o.win*o.pick).sum()/o.pick.sum(); return (o.win-m)
for r,L in data.items():
    od=opgg('opgg_global_d',r); om=opgg('opgg_global_m',r)
    mobt={c:t for t,cs in mob[r].items() for c in cs}
    for e in L:
        c=e['c']; g=lambda s: sd.get(f'{s}|{r}|{c}')
        dv=[]; 
        if c in od.index: dv.append((1,od[c]))
        for s,w in [('ugg_d',1),('dpm_d',1),('blitz_d',1),('log_d',0.5)]:
            if g(s): dv.append((w,g(s)[0]))
        mv=[]
        if c in om.index: mv.append(om[c])
        if g('ugg_m'): mv.append(g('ugg_m')[0])
        nd=(g('ugg_d') or [0,0,0,None])[3] or e['pick']/100*6e5
        nm=(g('ugg_m') or [0,0,0,None])[3] or e['pick']/100*1.2e5
        p=(g('ugg_d') or [0,0,None])[2] or e['pick']
        dmean=sum(w*v for w,v in dv)/sum(w for w,_ in dv) if dv else None
        parts=[]
        if dmean is not None: parts.append((0.5, shrink(dmean,nd)-spec(p)))
        if mv: parts.append((0.35, shrink(np.mean(mv),nm)-spec(p)))
        if e.get('euw') is not None: parts.append((0.15, shrink(e['euw'],e['pick']/100*4.5e5)-spec(e['pick'])))
        ws=sum(w for w,_ in parts)
        e['hi']=round(float(sum(w*v for w,v in parts)/ws),2) if ws>=0.5 else None
        e['dia']=round(float(dmean),2) if dmean is not None else None
        e['m']=round(float(np.mean(mv)),2) if mv else None
        e['pick_d']=p
        e['sites']={'U.GG':(g('ugg_d') or [None,None])[1],'Blitz':(g('blitz_d') or [None,None])[1],'dpm.lol':(g('dpm_d') or [None,None])[1],'League of Graphs':(g('log_d') or [None,None])[1],'METAsrc':(g('ms_d') or [None,None])[1],'Mobalytics experts':mobt.get(c)}
json.dump(data,open('tiers.json','w'),ensure_ascii=False)
for r,L in data.items():
    t=sorted([e for e in L if e['hi'] is not None],key=lambda e:-e['hi'])
    z=[e['c'] for e in t if e['hi']>=1.8 and e['pick_d']>=2 and (e['dia'] or -9)>=1.5 and (e['m'] or -9)>=1.5]
    print(r,'Z:',z,'| top6:',[(e['c'],e['hi']) for e in t[:6]])
