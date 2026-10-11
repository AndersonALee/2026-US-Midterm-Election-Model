# Institution inputs: how the seat-model task fetches them (all primary sources, run in the computer's built-in browser)

Result = /tmp/seatmodel/inst.json = {"ddhq":{"h":{},"s":{},"g":{},"asof":"YYYY-MM-DD"},"st":{"h":{},"s":{},"asof":"YYYY-MM-DD"},"vh":{"h":{},"s":{},"g":{},"asof":"YYYY-MM-DD"}}
Every value is the Democratic win probability (0-1). House dicts keep only races between 3% and 97% (a missing House race means "not competitive": that source is simply left out for it); Senate and governor dicts are complete. Paste the exact JSON strings the browser returns. If one source fails, leave it out and say so in the doc entry (the model drops it and renormalizes). FPO and Cook are fetched as before (STEP 1, STEP 3).

## DDHQ (https://votes.decisiondeskhq.com/forecast/2026/house, /senate, /governor)
Navigate to each page (a Vercel check passes by itself after a few seconds), wait ~4 s, then run (action javascript_exec); it returns the dict for that page. The page text shows only the favored party's chance, so the side comes from the rating text, and for "Toss Up" from the position of the dot (left < 50 = Democrat):
```
await new Promise(r=>setTimeout(r,4500));const o={};const HOUSE=/forecast\/2026\/house/.test(location.href);for(const tr of document.querySelectorAll('tr')){const nm=(tr.querySelector('td')||{}).innerText;if(!nm)continue;const m=nm.trim().match(/^([A-Z]{2})(?: (\d+|At-Large))?$/);if(!m)continue;const dot=tr.querySelector('div.rounded-full[style*="left"]'),lab=tr.querySelector('span[style*="left"]'),rt=tr.querySelector('span.font-bold');if(!dot||!lab||!rt)continue;const left=parseFloat(dot.style.left),p=parseFloat(lab.innerText.replace('>','').replace('<',''))+(/>/.test(lab.innerText)?0.5:0),r=rt.innerText.trim();let d;if(/ D$/.test(r))d=true;else if(/ R$/.test(r))d=false;else d=left<50;const pd=left===50&&/Toss/.test(r)?50:(d?p:100-p);const key=m[2]?m[1]+'-'+(m[2]==='At-Large'?'01':m[2].padStart(2,'0')):m[1];if(!HOUSE||(pd>=3&&pd<=97))o[key]=Math.round(pd*10)/1000}
const upd=(document.body.innerText.match(/Last updated ([A-Z][a-z]{2}) (\d{1,2})/)||[]);o._asof=upd[1]?'2026-'+String('JanFebMarAprMayJunJulAugSepOctNovDec'.indexOf(upd[1])/3+1).padStart(2,'0')+'-'+upd[2].padStart(2,'0'):null;JSON.stringify(o)
```
Checks: house 435 rows parsed before the filter (sum of D probabilities about equals the seat count on the page), senate 35 keys, governor 36 keys. Put `_asof` into "asof" and delete the `_asof` key.

## Split Ticket (hosted by The Argument; its own site no longer carries the forecast)
Navigate to https://www.theargumentmag.com/p/split-ticket-2026-midterms-model , wait ~3.5 s, run. The post embeds old Datawrapper versions of its charts, so the script resolves the LATEST version of each chart and reports its Last-Modified date:
```
await new Promise(r=>setTimeout(r,3500));const ST={Alabama:'AL',Alaska:'AK',Arkansas:'AR',Colorado:'CO',Delaware:'DE',Florida:'FL',Georgia:'GA',Idaho:'ID',Illinois:'IL',Iowa:'IA',Kansas:'KS',Kentucky:'KY',Louisiana:'LA',Maine:'ME',Massachusetts:'MA',Michigan:'MI',Minnesota:'MN',Mississippi:'MS',Montana:'MT',Nebraska:'NE','New Hampshire':'NH','New Jersey':'NJ','New Mexico':'NM','North Carolina':'NC',Ohio:'OH',Oklahoma:'OK',Oregon:'OR','Rhode Island':'RI','South Carolina':'SC','South Dakota':'SD',Tennessee:'TN',Texas:'TX',Virginia:'VA','West Virginia':'WV',Wyoming:'WY'};
const csv=t=>{const L=t.trim().split(/\r?\n/);const h=L[0].split(',');return L.slice(1).map(l=>{const c=[];let cur='',q=false;for(const ch of l){if(ch=='"')q=!q;else if(ch==','&&!q){c.push(cur);cur=''}else cur+=ch}c.push(cur);const o={};h.forEach((k,i)=>o[k]=c[i]);return o})};
const ids=[...new Set([...document.querySelectorAll('iframe')].map(f=>f.src).map(s=>(s.match(/dwcdn\.net\/([A-Za-z0-9]+)\//)||[])[1]).filter(Boolean))];let H=null,S=null,lm=[];
for(const id of ids){const base=await (await fetch('https://datawrapper.dwcdn.net/'+id+'/')).text();const vs=[...base.matchAll(new RegExp(id+'/(\\d+)/','g'))].map(m=>+m[1]);const v=vs.length?Math.max(...vs):null;if(!v)continue;const r=await fetch('https://datawrapper.dwcdn.net/'+id+'/'+v+'/dataset.csv');const t=await r.text();const hd=t.split(/\r?\n/)[0];if(/cd,/.test(hd)&&/win_prob_d/.test(hd)&&!H){H=csv(t);lm.push(r.headers.get('last-modified'))}else if(/State/.test(hd)&&/win_prob_d/.test(hd)&&!S){S=csv(t);lm.push(r.headers.get('last-modified'))}}
const h={},s={};for(const r of H){let k=r.cd.replace('-AL','-01');const m=k.match(/^([A-Z]{2})-(\d+)$/);if(m)k=m[1]+'-'+m[2].padStart(2,'0');const p=parseFloat(r.win_prob_d)/100;if(p>=.03&&p<=.97)h[k]=Math.round(p*1000)/1000}
for(const r of S){const k=ST[r.State];if(k)s[k]=Math.round(parseFloat(r.win_prob_d)/10)/1000*1}
JSON.stringify({h,s,asof:new Date(lm.map(x=>Date.parse(x)).sort()[0]).toISOString().slice(0,10),nH:H.length,nS:S.length})
```
Checks: nH 435, nS 35 (Split Ticket has no governor forecast). Drop nH and nS from the stored JSON. If the House chart cannot be found, leave Split Ticket out.

## VoteHub (https://votehub.com/2026-forecast/ , same-origin API)
Navigate to the page, wait ~1.5 s, run. The API's `summary.probability` is the REPUBLICAN win chance, so the script stores 1 minus it:
```
await new Promise(r=>setTimeout(r,1500));let items=[],cur=null;for(let i=0;i<5;i++){const j=await (await fetch('https://2026-forecast.votehub.com/v1/races?limit=1000'+(cur?'&cursor='+encodeURIComponent(cur):''))).json();items.push(...j.items);cur=j.next_cursor;if(!cur)break}
const lu=await (await fetch('https://2026-forecast.votehub.com/v1/sims/last-updated')).json();const h={},s={},g={};
for(const r of items){const m=r.race_id.match(/^([HSG])2026([A-Z]{2})(\d\d)$/);if(!m||!r.summary||r.summary.probability==null)continue;const p=Math.round((1-r.summary.probability)*1000)/1000;if(m[1]==='H'){const k=m[2]+'-'+(m[3]==='00'?'01':m[3]);if(p>=.03&&p<=.97)h[k]=p}else if(m[1]==='S')s[m[2]]=p;else g[m[2]]=p}
JSON.stringify({h,s,g,asof:lu.last_updated.slice(0,10),n:items.length})
```
Checks: n about 506 (435 + 35 + 36); the Democratic House probabilities summed over all races should be near the "Democrats win" seat count the page shows. Drop `n`.
