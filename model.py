import json,sys,datetime,os
import numpy as np
from scipy.stats import norm
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
BASE=dict((a.split(':')[0],float(a.split(':')[1])) for a in open('base.txt').read().strip().split(','))
inp=json.load(open(sys.argv[1]));N=inp.get('N',7.8);SH=N+1.5
CK={'Toss Up':.5,'Lean D':.7,'Lean R':.3,'Likely D':.88,'Likely R':.12}
SEN_TR={'TX':13.6,'AK':13.1,'OH':11.2,'ME':-6.5,'KS':15.9,'IA':13.2,'MI':1.4,'NE':20.5,'SC':17.8}
GOV_TR={'OH':11.2,'IA':13.2,'TX':13.6,'NV':3.1,'GA':2.2,'FL':13.1,'AK':13.1,'WI':.9}
NM={'AK':'Alaska','OH':'Ohio','TX':'Texas','IA':'Iowa','KS':'Kansas','ME':'Maine','MI':'Michigan','GA':'Georgia','NC':'N. Carolina','NH':'N. Hampshire','MN':'Minnesota','NE':'Nebraska','SC':'S. Carolina','FL':'Florida','LA':'Louisiana','NV':'Nevada','WI':'Wisconsin'}
def wavg(parts):
    a=b=0
    for v,w in parts:
        if v is not None: a+=v*w;b+=w
    return a/b
fund_w=.25;k=(1-fund_w)/.75
cookh={}
for cat,keys in inp['cookh'].items():
    for key in keys: cookh[key]=CK[cat]
# House
H=[]
fpo=inp['fpo'];pmh=inp['pmh']
for key,b in BASE.items():
    f=fpo.get(key)
    if f is None: f=.999 if b>0 else .001
    pm=pmh.get(key)
    c=cookh.get(key,.97 if f>.5 else .03)
    fu=float(norm.cdf((b+SH)/5.5))
    comp=wavg([(f,.35*k),(pm,.25*k),(c,.15*k),(fu,fund_w)])
    H.append(dict(id=key,f=f,pm=pm,ck=c,fund=fu,comp=comp))
S=[]
for st,tr in SEN_TR.items():
    f=inp['sen'][st];pm=inp['pms'].get(st);cat=inp['cooks'].get(st)
    c=CK[cat] if cat else (.97 if f>.5 else .03)
    fu=float(norm.cdf((-tr+SH)/6.5))
    S.append(dict(id=st,f=f,pm=pm,ck=c,fund=fu,comp=wavg([(f,.35*k),(pm,.25*k),(c,.15*k),(fu,fund_w)])))
G=[]
for st,tr in GOV_TR.items():
    pm=inp['pmg'].get(st);cat=inp['cookg'].get(st);c=CK[cat] if cat else None
    fu=float(norm.cdf((-tr+SH)/6.5))
    G.append(dict(id=st,pm=pm,ck=c,fund=fu,comp=wavg([(pm,.45*(1-fund_w)),(c,.30*(1-fund_w)),(fu,fund_w)])))
rng=np.random.default_rng(7)
def sim(ps,rho,add,thr,n=20000):
    z=norm.ppf(np.clip(ps,1e-6,1-1e-6));S_=rng.standard_normal((n,1));e=rng.standard_normal((n,len(ps)))
    w=((np.sqrt(rho)*S_+np.sqrt(1-rho)*e)<z).sum(1)+add
    return dict(mean=float(w.mean()),ctl=float((w>=thr).mean()),lo=int(np.percentile(w,10)),hi=int(np.percentile(w,90)),w=w,thr=thr)
h=sim(np.array([x['comp'] for x in H]),.309,0,218);s=sim(np.array([x['comp'] for x in S]),.376,47,51);g=sim(np.array([x['comp'] for x in G]),.3,0,5)
fo=sim(np.array([x['f'] for x in H]),.309,0,218,5000)
res=dict(date=str(datetime.date.today()),N=N,house=dict(mean=round(h['mean'],1),ctl=round(h['ctl'],3),lo=h['lo'],hi=h['hi'],fpo_only=round(fo['mean'],1)),
 senate=dict(mean=round(s['mean'],1),ctl=round(s['ctl'],3),lo=s['lo'],hi=s['hi']),gov=dict(mean=round(g['mean'],1),maj=round(g['ctl'],3)),
 sen={x['id']:round(x['comp'],3) for x in S},gov_p={x['id']:round(x['comp'],3) for x in G},
 close=[(x['id'],round(x['comp'],3)) for x in sorted(H,key=lambda x:abs(x['comp']-.5))[:12]])
# own rating (composite = Dem win prob): Solid >=95, Likely 80-95, Lean 65-80, Tilt 55-65, Toss-up 45-55 (mirrored for R)
def rating(p):
    q=max(p,1-p);side='D' if p>=.5 else 'R'
    if q>=.95: return 'Solid '+side,4 if side=='D' else -4
    if q>=.80: return 'Likely '+side,3 if side=='D' else -3
    if q>=.65: return 'Lean '+side,2 if side=='D' else -2
    if q>=.55: return 'Tilt '+side,1 if side=='D' else -1
    return 'Toss-up',0
CKO={'Toss Up':0,'Lean D':2,'Likely D':3,'Lean R':-2,'Likely R':-3}
res_extra=dict(sen_rating={x['id']:rating(x['comp'])[0] for x in S},gov_rating={x['id']:rating(x['comp'])[0] for x in G})
diffs=[]
for cat,keys in inp['cookh'].items():
    for key in keys:
        x=next((y for y in H if y['id']==key),None)
        if x: diffs.append((abs(rating(x['comp'])[1]-CKO[cat]),key,cat,rating(x['comp'])[0]))
diffs.sort(reverse=True)
res_extra['vs_cook']=[(k,c,r) for d,k,c,r in diffs if d>=2][:5]
res.update(res_extra)
json.dump(res,open('result.json','w'));print(json.dumps(res))
# site data + history, written into the repo checkout given as argv[2] (default ./site); history.json is the persistent store
RD=sys.argv[2] if len(sys.argv)>2 else 'site';os.makedirs(RD,exist_ok=True)
def ld(p,dflt):
    try: return json.load(open(os.path.join(RD,p)))
    except Exception: return dflt
oldd=ld('data.json',{});prev={}
for r in oldd.get('H','').split(';'):
    if r: a_=r.split(',');prev[a_[0]]=int(a_[5])
def terms(i):
    if i in prev: return prev[i]
    s_=i[:2]
    return 1 if s_ in('TX','FL','OH','NC','MO','CA','UT','LA','TN') else 2 if s_ in('AL','NY','GA') else 3
CODE={'Toss Up':'T','Lean D':'l','Lean R':'L','Likely D':'k','Likely R':'K'}
def ckcode(p):
    for n,v in CK.items():
        if abs(v-p)<1e-9: return CODE[n]
    return ''
hs=sorted(H,key=lambda x:abs(x['comp']-.5));top=hs[:66];rest=hs[66:]
fixed=sum(1 for x in rest if x['comp']>.5)
Hs=';'.join(','.join(str(v) for v in [x['id'],round(x['f'],3),-1 if x['pm'] is None else round(x['pm'],3),ckcode(x['ck']) if x['id'] in cookh else '',round(max(-30,min(30,BASE[x['id']])),1),terms(x['id'])]) for x in sorted(top,key=lambda x:x['id']))
Ss=[[x['id'],round(x['f'],3),None if x['pm'] is None else round(x['pm'],3),CODE.get(inp['cooks'].get(x['id']),''),SEN_TR[x['id']]] for x in S]
Gs=[[x['id'],None if x['pm'] is None else round(x['pm'],3),CODE.get(inp['cookg'].get(x['id']),''),GOV_TR[x['id']]] for x in G]
json.dump(dict(asof=res['date'],N0=N,fixed_dem=fixed,sen_add=47,n_listed=66,rho_h=.5,H=Hs,S=Ss,G=Gs),open(os.path.join(RD,'data.json'),'w'),separators=(',',':'))
hist=[r for r in ld('history.json',[]) if r.get('date')!=res['date']]
hist.append(dict(date=res['date'],N=N,house_mean=res['house']['mean'],house_ctl=res['house']['ctl'],house_lo=res['house']['lo'],house_hi=res['house']['hi'],fpo_only=res['house']['fpo_only'],senate_mean=res['senate']['mean'],senate_ctl=res['senate']['ctl'],senate_lo=res['senate']['lo'],senate_hi=res['senate']['hi'],gov_mean=res['gov']['mean'],gov_maj=res['gov']['maj']))
json.dump(hist,open(os.path.join(RD,'history.json'),'w'),separators=(',',':'))
# image
bg,panel,ink,mute='#0f1218','#171b24','#eceff5','#9aa3b2';D,R='#6aa3ff','#ff7a6e'
fig=plt.figure(figsize=(12,9),facecolor=bg)
fig.text(.04,.955,'2026 Midterm Seat Model',color=ink,fontsize=22,weight='bold')
fig.text(.04,.925,f"{res['date']} · composite of FPO, Polymarket, Cook, fundamentals · national environment D+{N:.1f}",color=mute,fontsize=10.5)
def stat(x,t,big,l1,l2):
    fig.text(x,.86,t,color=mute,fontsize=9.5);fig.text(x,.805,big,color=D,fontsize=30,weight='bold',family='monospace');fig.text(x,.775,l1,color=ink,fontsize=10);fig.text(x,.752,l2,color=mute,fontsize=9.5)
stat(.04,'HOUSE · 218 NEEDED',f"{h['mean']:.0f}",f"Dem control {h['ctl']*100:.0f}%",f"80% range {h['lo']}–{h['hi']} seats (FPO alone {fo['mean']:.0f})")
stat(.37,'SENATE · 51 NEEDED',f"{s['mean']:.1f}",f"Dem control {s['ctl']*100:.0f}%",f"80% range {s['lo']}–{s['hi']} seats")
stat(.70,'GOVERNORS · 8 TRACKED',f"{g['mean']:.1f}",f"Majority (≥5) {g['ctl']*100:.0f}%",'expected Dem wins')
def hist(ax,r,lo,hi,t):
    ax.set_facecolor(panel);xs=np.arange(lo,hi+1);ys=[(r['w']==v).mean()*100 for v in xs]
    ax.bar(xs,ys,color=[D if v>=r['thr'] else R for v in xs],width=.9);ax.axvline(r['thr']-.5,color=ink,ls='--',lw=1)
    ax.set_title(t,color=ink,fontsize=11,loc='left');ax.tick_params(colors=mute,labelsize=8);[sp.set_visible(False) for sp in ax.spines.values()];ax.set_yticks([])
hist(fig.add_axes([.04,.50,.43,.20]),h,int(h['lo'])-25,int(h['hi'])+25,'House: Democratic seats (dashed = majority)')
hist(fig.add_axes([.55,.50,.41,.20]),s,41,62,'Senate: Democratic seats (dashed = majority)')
def bars(ax,items,t,fs=8):
    items=sorted(items,key=lambda x:x[1]);ax.set_facecolor(panel)
    ax.barh([a for a,_ in items],[b*100 for _,b in items],color=[D if b>=.5 else R for _,b in items],height=.62);ax.axvline(50,color=ink,lw=.8,ls='--');ax.set_xlim(0,100);ax.set_xticks([])
    for i,(a,b) in enumerate(items): ax.text(min(b*100+1.5,93),i,f"{b*100:.0f}",va='center',color=ink,fontsize=8,family='monospace')
    ax.set_title(t,color=ink,fontsize=11,loc='left');ax.tick_params(colors=mute,labelsize=fs);[sp.set_visible(False) for sp in ax.spines.values()]
bars(fig.add_axes([.10,.06,.24,.34]),[(NM[x['id']],x['comp']) for x in S],'Senate: Dem win %')
bars(fig.add_axes([.46,.06,.18,.34]),[(NM[x['id']],x['comp']) for x in G],'Governor: Dem win %')
bars(fig.add_axes([.78,.06,.18,.34]),[(a,b) for a,b in res['close']],'House: 12 closest seats')
fig.text(.04,.02,'Fundamentals = 2024 presidential + 2024/2022 House results (where lines unchanged) + generic ballot. Does not capture candidate quality.',color=mute,fontsize=8)
fig.savefig('summary.png',dpi=110,facecolor=bg)
