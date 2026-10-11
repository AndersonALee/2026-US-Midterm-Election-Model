await new Promise(r=>setTimeout(r,1500));let items=[],cur=null;for(let i=0;i<5;i++){const j=await (await fetch('https://2026-forecast.votehub.com/v1/races?limit=1000'+(cur?'&cursor='+encodeURIComponent(cur):''))).json();items.push(...j.items);cur=j.next_cursor;if(!cur)break}
const lu=await (await fetch('https://2026-forecast.votehub.com/v1/sims/last-updated')).json();const h={},s={},g={};
for(const r of items){const m=r.race_id.match(/^([HSG])2026([A-Z]{2})(\d\d)$/);if(!m||!r.summary||r.summary.probability==null)continue;const p=Math.round((1-r.summary.probability)*1000)/1000;if(m[1]==='H'){const k=m[2]+'-'+(m[3]==='00'?'01':m[3]);if(p>=.03&&p<=.97)h[k]=p}else if(m[1]==='S')s[m[2]]=p;else g[m[2]]=p}
return JSON.stringify({h,s,g,asof:lu.last_updated.slice(0,10),n:items.length})
