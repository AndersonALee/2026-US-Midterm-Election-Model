import json,sys,datetime,os
import numpy as np
from scipy.stats import norm
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
BASE=dict((a.split(':')[0],float(a.split(':')[1])) for a in open('base.txt').read().strip().split(','))
RD0=sys.argv[2] if len(sys.argv)>2 else 'site'
# House fundamentals: Cook 2026 PVI (relative to the nation) converted to the 2024-margin scale used with SH (nation was R+1.5)
PV=json.load(open(os.path.join(RD0,'pvi.json')))
BASE=dict((k,PV[k]-1.5) for k in BASE)
inp=json.load(open(sys.argv[1]));N=inp.get('N',7.8);DISC=.7;SH=DISC*N+1.5
CK={'Toss Up':.5,'Lean D':.7,'Lean R':.3,'Likely D':.88,'Likely R':.12,'Solid D':.97,'Solid R':.03}
# 2024 Trump margin (points, + = Trump) for every state with a 2026 race
TRM=dict(AL=30.5,AK=13.1,AZ=5.5,AR=30.6,CA=-20.2,CO=-11.0,CT=-14.5,DE=-14.6,FL=13.1,GA=2.2,HI=-25.2,ID=36.0,IL=-10.9,IA=13.2,KS=15.9,KY=25.5,LA=22.0,ME=-6.5,MD=-28.6,MA=-25.2,MI=1.4,MN=-4.2,MS=22.0,MT=19.9,NE=20.5,NV=3.1,NH=-2.8,NJ=-5.9,NM=-6.0,NY=-12.6,NC=3.2,OH=11.2,OK=34.3,OR=-14.3,PA=1.8,RI=-13.9,SC=17.8,SD=29.3,TN=29.8,TX=13.6,VT=-31.9,VA=-5.8,WV=42.0,WI=0.9,WY=46.1)
SEN_ST='AL AK AR CO DE FL GA ID IL IA KS KY LA ME MA MI MN MS MT NE NH NJ NM NC OH OK OR RI SC SD TN TX VA WV WY'.split()
GOV_ST='AL AK AZ AR CA CO CT FL GA HI ID IL IA KS ME MD MA MI MN NE NV NH NM NY OH OK OR PA RI SC SD TN TX VT WI WY'.split()
SEN_TR={k:TRM[k] for k in SEN_ST}
GOV_TR={k:TRM[k] for k in GOV_ST}
# Yankee-Republican incumbents (VT Scott, NH Ayotte): blend 20% 2024 presidential margin + 80% 2024 gubernatorial margin (Trump-side +; approximate: VT gov ~R+49, NH gov ~R+9)
GOV_TR['VT']=round(.2*TRM['VT']+.8*49,1);GOV_TR['NH']=round(.2*TRM['NH']+.8*9,1)
SEN_ADD,GOV_ADD,GOV_THR=34,6,26  # Dem seats not up in 2026 (Senate 34 of 47; governors 6 of 24); governors majority = 26 of 50
NM={'AK':'Alaska','OH':'Ohio','TX':'Texas','IA':'Iowa','KS':'Kansas','ME':'Maine','MI':'Michigan','GA':'Georgia','NC':'N. Carolina','NH':'N. Hampshire','MN':'Minnesota','NE':'Nebraska','SC':'S. Carolina','FL':'Florida','LA':'Louisiana','NV':'Nevada','WI':'Wisconsin'}
def wavg(parts):
    a=b=0
    for v,w in parts:
        if v is not None: a+=v*w;b+=w
    return a/b
fund_w=.15;kh=(1-fund_w)/.75;k=(1-fund_w)/.85
RD=sys.argv[2] if len(sys.argv)>2 else 'site'
try: POLLS=json.load(open(os.path.join(RD,'polls.json')))
except Exception: POLLS={'S':{},'G':{}}
TODAY=datetime.date.today()
def poll_sig(r):
    # RealClearPolling average -> Dem win probability. Returns (prob, weight multiplier, [avgD,avgR,n,last]) or (None,0,None)
    if not r: return None,0,None
    if r.get('aD') is not None: dd,rr=r['aD'],r['aR']
    else:
        ps=[p for p in r.get('polls',[]) if p[1] and 0<=(TODAY-datetime.date.fromisoformat(p[1])).days<=60]
        if not ps: return None,0,None
        dd=sum(p[2] for p in ps)/len(ps);rr=sum(p[3] for p in ps)/len(ps)
    age=(TODAY-datetime.date.fromisoformat(r['last'])).days;n=r['n']
    mult=1.0 if age<=14 else max(.4,1-(age-14)*.6/46)
    if n<3: mult*=.75
    sg=6.0 if n>=3 else 7.5
    return float(norm.cdf((dd-rr)/sg)),round(mult,2),[round(dd,1),round(rr,1),n,r['last']]
# weights at the default 15% fundamentals weight (they scale with the slider): Senate Polls .30 FPO .25 PM .20 Cook .10; Governor Polls .43 PM .28 Cook .14 (no FPO); House FPO .40 PM .28 Cook .17
cookh={}
for cat,keys in inp['cookh'].items():
    for key in keys: cookh[key]=CK[cat]
# House
H=[]
fpo=inp['fpo'];pmh=inp['pmh']
for key,b in BASE.items():
    f=fpo.get(key)
    pm=pmh.get(key)
    if f is None:
        # FPO lists only races between 0.5% and 99.5%; a missing race is a near-certain one. Direction: Polymarket, else Cook, else district lean
        if pm is not None: d_=pm>.5
        elif key in cookh: d_=cookh[key]>.5
        else: d_=b>0
        f=.999 if d_ else .001
    fnone=False
    c=cookh.get(key,.97 if f>.5 else .03)
    fu=float(norm.cdf((b+SH)/5.5))
    comp=wavg([(None if fnone else f,.35*kh),(pm,.25*kh),(c,.15*kh),(fu,fund_w)])
    H.append(dict(id=key,f=f,fn=fnone,pm=pm,ck=c,fund=fu,comp=comp))
S=[]
for st,tr in SEN_TR.items():
    f=inp['sen'].get(st)
    if f is None: f=.999 if tr<0 else .001
    pm=inp['pms'].get(st);cat=inp['cooks'].get(st)
    c=CK[cat] if cat else (.97 if f>.5 else .03)
    fu=float(norm.cdf((-tr+SH)/6.5))
    pp,pw,pa=poll_sig(POLLS['S'].get(st))
    S.append(dict(id=st,f=f,pm=pm,ck=c,fund=fu,pp=pp,pw=pw,pa=pa,comp=wavg([(f,.25*k),(pm,.20*k),(c,.10*k),(pp,.30*k*pw),(fu,fund_w)])))
G=[]
for st,tr in GOV_TR.items():
    pm=inp['pmg'].get(st);cat=inp['cookg'].get(st);fu=float(norm.cdf((-tr+SH)/6.5))
    c=CK[cat] if cat else (.97 if (pm if pm is not None else fu)>.5 else .03)
    pp,pw,pa=poll_sig(POLLS['G'].get(st))
    G.append(dict(id=st,pm=pm,ck=c,fund=fu,pp=pp,pw=pw,pa=pa,comp=wavg([(pm,.28*k),(c,.14*k),(pp,.43*k*pw),(fu,fund_w)])))
rng=np.random.default_rng(7)
def sim(ps,rho,add,thr,n=20000):
    z=norm.ppf(np.clip(ps,1e-6,1-1e-6));S_=rng.standard_normal((n,1));e=rng.standard_normal((n,len(ps)))
    w=((np.sqrt(rho)*S_+np.sqrt(1-rho)*e)<z).sum(1)+add
    return dict(mean=float(w.mean()),ctl=float((w>=thr).mean()),lo=int(np.percentile(w,10)),hi=int(np.percentile(w,90)),w=w,thr=thr)
h=sim(np.array([x['comp'] for x in H]),.309,0,218);s=sim(np.array([x['comp'] for x in S]),.376,SEN_ADD,51);g=sim(np.array([x['comp'] for x in G]),.3,GOV_ADD,GOV_THR)
fo=sim(np.array([x['f'] for x in H]),.309,0,218,5000)
res=dict(date=str(datetime.date.today()),N=N,house=dict(mean=round(h['mean'],1),ctl=round(h['ctl'],3),lo=h['lo'],hi=h['hi'],fpo_only=round(fo['mean'],1)),
 senate=dict(mean=round(s['mean'],1),ctl=round(s['ctl'],3),lo=s['lo'],hi=s['hi']),gov=dict(mean=round(g['mean'],1),maj=round(g['ctl'],3)),
 sen={x['id']:round(x['comp'],3) for x in S},gov_p={x['id']:round(x['comp'],3) for x in G},
 close=[(x['id'],round(x['comp'],3)) for x in sorted(H,key=lambda x:abs(x['comp']-.5))[:12]])
# own rating (composite = Dem win prob): Solid >=90, Likely 80-90, Lean 70-80, Tilt 60-70, Toss-up 40-60 (mirrored for R)
def rating(p):
    q=max(p,1-p);side='D' if p>=.5 else 'R'
    if q>=.90: return 'Solid '+side,4 if side=='D' else -4
    if q>=.80: return 'Likely '+side,3 if side=='D' else -3
    if q>=.70: return 'Lean '+side,2 if side=='D' else -2
    if q>=.60: return 'Tilt '+side,1 if side=='D' else -1
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
# consistency check: seats where independent sources (FPO, Polymarket, RCP polls) disagree by 30+ points; top 8 by spread
fl=[]
def _chk(name,src,comp):
    v=[(k,x) for k,x in src if x is not None]
    if len(v)>=2:
        sp=max(x for k,x in v)-min(x for k,x in v)
        if sp>=.30: fl.append((sp,name+' '+' / '.join('%s %d'%(k,round(x*100)) for k,x in v)+' / model %d'%round(comp*100)))
for x in H: _chk(x['id'],[('FPO',inp['fpo'].get(x['id'])),('PM',x['pm'])],x['comp'])
for x in S: _chk('Senate '+x['id'],[('FPO',inp['sen'].get(x['id'])),('PM',x['pm']),('Polls',x['pp'])],x['comp'])
for x in G: _chk('Gov '+x['id'],[('PM',x['pm']),('Polls',x['pp'])],x['comp'])
res_extra['flags']=[t for sp,t in sorted(fl,reverse=True)[:8]]
res_extra['n_flags']=len(fl)
res.update(res_extra)
json.dump(res,open('result.json','w'));print(json.dumps(res))
# site data + history, written into the repo checkout given as argv[2] (default ./site); history.json is the persistent store
os.makedirs(RD,exist_ok=True)
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
CODE={'Toss Up':'T','Lean D':'l','Lean R':'L','Likely D':'k','Likely R':'K','Solid D':'S','Solid R':'s'}
def ckcode(p):
    for n,v in CK.items():
        if abs(v-p)<1e-9: return CODE[n]
    return ''
hs=sorted(H,key=lambda x:abs(x['comp']-.5));top=hs[:66];rest=hs[66:]
fixed=sum(1 for x in rest if x['comp']>.5)
As=';'.join('%s,%s,%s'%(x['id'],round(x['comp'],3),round(max(-30,min(30,PV[x['id']])),1)) for x in sorted(rest,key=lambda x:x['id']))
Hs=';'.join(','.join(str(v) for v in [x['id'],-1 if x['fn'] else round(x['f'],3),-1 if x['pm'] is None else round(x['pm'],3),ckcode(x['ck']) if x['id'] in cookh else '',round(max(-30,min(30,PV[x['id']])),1),terms(x['id'])]) for x in sorted(top,key=lambda x:x['id']))
Ss=[[x['id'],round(x['f'],3),None if x['pm'] is None else round(x['pm'],3),CODE.get(inp['cooks'].get(x['id']),''),SEN_TR[x['id']],None if x['pp'] is None else round(x['pp'],3),x['pw'],x['pa']] for x in S]
Gs=[[x['id'],None if x['pm'] is None else round(x['pm'],3),CODE.get(inp['cookg'].get(x['id']),''),GOV_TR[x['id']],None if x['pp'] is None else round(x['pp'],3),x['pw'],x['pa']] for x in G]
json.dump(dict(asof=res['date'],disc=DISC,ts=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).strftime('%Y-%m-%dT%H:%MZ'),N0=N,fixed_dem=fixed,sen_add=SEN_ADD,gov_add=GOV_ADD,gov_thr=GOV_THR,n_listed=66,rho_h=.5,H=Hs,A=As,S=Ss,G=Gs,C={x['id']:round(x['comp'],3) for x in H},SC={x['id']:round(x['comp'],3) for x in S},GC={x['id']:round(x['comp'],3) for x in G}),open(os.path.join(RD,'data.json'),'w'),separators=(',',':'))
hist=[r for r in ld('history.json',[]) if r.get('date')!=res['date']]
hist.append(dict(date=res['date'],N=N,house_mean=res['house']['mean'],house_ctl=res['house']['ctl'],house_lo=res['house']['lo'],house_hi=res['house']['hi'],fpo_only=res['house']['fpo_only'],senate_mean=res['senate']['mean'],senate_ctl=res['senate']['ctl'],senate_lo=res['senate']['lo'],senate_hi=res['senate']['hi'],gov_mean=res['gov']['mean'],gov_maj=res['gov']['maj']))
json.dump(hist,open(os.path.join(RD,'history.json'),'w'),separators=(',',':'))
# image
bg,panel,ink,mute='#0f1218','#171b24','#eceff5','#9aa3b2';D,R='#6aa3ff','#ff7a6e'
fig=plt.figure(figsize=(12,9),facecolor=bg)
fig.text(.04,.955,'2026 Midterm Seat Model',color=ink,fontsize=22,weight='bold')
fig.text(.04,.925,f"{res['date']} · composite of FPO, Polymarket, Cook, RCP polls, fundamentals · national environment D+{N:.1f}",color=mute,fontsize=10.5)
def stat(x,t,big,l1,l2):
    fig.text(x,.86,t,color=mute,fontsize=9.5);fig.text(x,.805,big,color=D,fontsize=30,weight='bold',family='monospace');fig.text(x,.775,l1,color=ink,fontsize=10);fig.text(x,.752,l2,color=mute,fontsize=9.5)
stat(.04,'HOUSE · 218 NEEDED',f"{h['mean']:.0f}",f"Dem control {h['ctl']*100:.0f}%",f"80% range {h['lo']}–{h['hi']} seats (FPO alone {fo['mean']:.0f})")
stat(.37,'SENATE · 51 NEEDED',f"{s['mean']:.1f}",f"Dem control {s['ctl']*100:.0f}%",f"80% range {s['lo']}–{s['hi']} seats")
stat(.70,'GOVERNORS · 36 RACES',f"{g['mean']:.1f}",f"Majority (≥26 of 50) {g['ctl']*100:.0f}%",'expected Dem governors (of 50)')
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
bars(fig.add_axes([.10,.06,.24,.34]),[(x['id'],x['comp']) for x in S if .1<x['comp']<.9],'Senate: Dem win % (10-90%)')
bars(fig.add_axes([.46,.06,.18,.34]),[(x['id'],x['comp']) for x in G if .1<x['comp']<.9],'Governor: Dem win % (10-90%)')
bars(fig.add_axes([.78,.06,.18,.34]),[(a,b) for a,b in res['close']],'House: 12 closest seats')
fig.text(.04,.02,'Fundamentals = 2024 presidential + 2024/2022 House results (where lines unchanged) + generic ballot. Does not capture candidate quality.',color=mute,fontsize=8)
fig.savefig('summary.png',dpi=110,facecolor=bg)
