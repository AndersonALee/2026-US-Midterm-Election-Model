#!/usr/bin/env python3
"""Refresh data.json from one seat-model run.
usage: python3 update_site.py /tmp/seatmodel   (dir holding in.json and result.json)
data.json keeps the static parts (district list, fundamentals, state traits) and the run history.
"""
import json,sys,os
wd=sys.argv[1] if len(sys.argv)>1 else '/tmp/seatmodel'
here=os.path.dirname(os.path.abspath(__file__))
inp=json.load(open(os.path.join(wd,'in.json')));res=json.load(open(os.path.join(wd,'result.json')))
dp=os.path.join(here,'data.json');d=json.load(open(dp))
LET={'Toss Up':'T','Lean D':'l','Lean R':'L','Likely D':'k','Likely R':'K'}
hc={}
for cat,keys in inp['cookh'].items():
    for k in keys: hc[k]=LET[cat]
for h in d['house']:
    f=inp['fpo'].get(h['id'])
    h['f']=f if f is not None else (.999 if h['base']>0 else .001)
    h['pm']=inp['pmh'].get(h['id']);h['ck']=hc.get(h['id'])
for s in d['senate']:
    s['f']=inp['sen'][s['id']];s['pm']=inp['pms'].get(s['id']);c=inp['cooks'].get(s['id']);s['ck']=LET.get(c)
for g in d['gov']:
    g['pm']=inp['pmg'].get(g['id']);c=inp['cookg'].get(g['id']);g['ck']=LET.get(c,g.get('ck'))
r=res
row=dict(date=r['date'],N=r['N'],house_mean=r['house']['mean'],house_ctl=r['house']['ctl'],house_lo=r['house']['lo'],house_hi=r['house']['hi'],fpo_only=r['house']['fpo_only'],senate_mean=r['senate']['mean'],senate_ctl=r['senate']['ctl'],senate_lo=r['senate']['lo'],senate_hi=r['senate']['hi'],gov_mean=r['gov']['mean'],gov_maj=r['gov']['maj'])
d['history']=[x for x in d.get('history',[]) if x['date']!=row['date']]+[row]
d['history'].sort(key=lambda x:x['date'])
d['asof']=r['date'];d['N']=r['N']
json.dump(d,open(dp,'w'),separators=(',',':'))
print('data.json updated',d['asof'],len(d['history']),'history rows')
