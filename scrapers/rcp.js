const CODE={'alabama':'AL','alaska':'AK','arizona':'AZ','arkansas':'AR','california':'CA','colorado':'CO','connecticut':'CT','delaware':'DE','florida':'FL','georgia':'GA','hawaii':'HI','idaho':'ID','illinois':'IL','indiana':'IN','iowa':'IA','kansas':'KS','kentucky':'KY','louisiana':'LA','maine':'ME','maryland':'MD','massachusetts':'MA','michigan':'MI','minnesota':'MN','mississippi':'MS','missouri':'MO','montana':'MT','nebraska':'NE','nevada':'NV','new-hampshire':'NH','new-jersey':'NJ','new-mexico':'NM','new-york':'NY','north-carolina':'NC','north-dakota':'ND','ohio':'OH','oklahoma':'OK','oregon':'OR','pennsylvania':'PA','rhode-island':'RI','south-carolina':'SC','south-dakota':'SD','tennessee':'TN','texas':'TX','utah':'UT','vermont':'VT','virginia':'VA','washington':'WA','west-virginia':'WV','wisconsin':'WI','wyoming':'WY'};
const today=new Date();const iso=(m,d)=>{const t=new Date(today.getFullYear(),m-1,d);return t>today?null:`${today.getFullYear()}-${String(m).padStart(2,'0')}-${String(d).padStart(2,'0')}`};
const ed=s=>{const m=(s||'').split('-').pop().trim().match(/(\d+)\/(\d+)/);return m?iso(+m[1],+m[2]):null};
const num=x=>{const v=parseFloat(x);return isNaN(v)?null:v};
const smp=s=>{const n=((s||'').match(/[\d,]+/)||[''])[0].replace(/,/g,'');const p=((s||'').match(/\b(LV|RV|A|V|Adults?)\b/)||[''])[0];return [n?+n:null,p==='V'?'LV':(/^Adult/.test(p)?'A':p)]};
const links=new Set();
for(const p of ['/maps/senate/2026/toss-up','/maps/governor/2026/toss-up','/maps/senate/2026/polymarket','/maps/governor/2026/polymarket','/latest-polls/senate','/latest-polls/governor','/latest-polls/2026']){try{const h=await (await fetch(p)).text();for(const m of h.matchAll(/\/polls\/(senate|governor)\/(?:general|special-election)\/2026\/[a-z0-9\-]+\/[a-z0-9\-]+/g))links.add(m[0])}catch(e){}}
const out={asof:today.toISOString().slice(0,10),src:'RealClearPolling race pages (individual polls with sample and population, plus the RCP Average when listed)',S:{},G:{}};const best={};
for(const u of links){try{
 const h=await (await fetch(u)).text();const d=new DOMParser().parseFromString(h,'text/html');
 const tb=[...d.querySelectorAll('table')].find(t=>/pollster/i.test(t.textContent.slice(0,300)));if(!tb)continue;
 const hd=[...tb.querySelectorAll('th')].map(x=>x.textContent.trim());const rows=[...tb.querySelectorAll('tr')].map(r=>[...r.querySelectorAll('td')].map(c=>c.textContent.trim())).filter(r=>r.length>3);if(!rows.length)continue;
 const sp=hd.indexOf('spread');const first=hd.findIndex((x,i)=>i>=3&&!/^moe$/i.test(x));const cs=hd.slice(first,sp);const off=rows[0].length-cs.length-2;
 const cand=cs.map(c=>({n:c.replace(/\s*\([A-Z]\)\s*\*?|\s*\*/g,'').trim(),p:(c.match(/\(([A-Z])\)/)||[])[1]||''}));
 let di=cand.findIndex(c=>c.p==='D');if(di<0)di=cand.findIndex(c=>c.p==='I');let ri=cand.findIndex(c=>c.p==='R');
 if(/special-election\/2026\/ohio/.test(u)){di=0;ri=1}
 if(/senate\/general\/2026\/montana\//.test(u)){const b=cand.findIndex(c=>/Bodnar/.test(c.n));if(b>=0)di=b} // Bodnar (I) is the real Democratic-backed nominee in Montana
 if(di<0||ri<0)continue;
 const P=u.split('/');const off_='senate'===P[2]?'S':'G';const st=CODE[P[5].replace('---3-electoral','')];if(!st)continue;
 const rr=rows.map(r=>({po:r[0],dt:r[1],sa:r[2],d:num(r[off+di]),r:num(r[off+ri])}));
 const avg=rr.find(r=>/RCP Average/i.test(r.po));const polls=rr.filter(r=>!/RCP Average/i.test(r.po)&&r.d!=null&&r.r!=null&&ed(r.dt));
 if(!polls.length)continue;
 const dts=polls.map(p=>ed(p.dt)).sort();
 const rec={D:cand[di].n,R:cand[ri].n,n:polls.length,last:dts[dts.length-1]};
 if(avg&&avg.d!=null&&avg.r!=null){rec.aD=avg.d;rec.aR=avg.r;rec.aDt=avg.dt}
 rec.polls=polls.map(p=>[p.po,ed(p.dt),p.d,p.r,...smp(p.sa)]); // [pollster, end date, D, R, sample size, population]
 const key=off_+st;if(!best[key]||cs.length<best[key].nc||(cs.length===best[key].nc&&rec.n>best[key].rec.n))best[key]={nc:cs.length,rec};
}catch(e){}}
for(const k in best)out[k[0]][k.slice(1)]=best[k].rec;
return JSON.stringify(out)
