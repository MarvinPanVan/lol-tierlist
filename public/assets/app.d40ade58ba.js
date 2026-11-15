{
let DATA=TL.DATA;const CUR=DATA;
const ROOT=TL.ROOT,PAGE=TL.PAGE,INIT_ROLE=TL.ROLE,INIT_CHAMP=TL.CHAMP||'';
const SITE=new URL(ROOT||'./',location.href).href,IMGBASE=SITE+'img/champ/';
const RICON={top:'<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M3 3h11l-3.5 3.5H6.5v4L3 14z" fill="currentColor"/><path d="M7.5 17h9.5V7.5" fill="none" stroke="currentColor" stroke-width="1.6" opacity=".45"/></svg>',
jungle:'<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M6 2.5c2.6 3.2 3.4 7.6 2.4 13.5M10.2 2.5c1.6 3 2 7 1.2 11.5M14.2 3c1 2.4 1.3 5.4.6 8.8" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
mid:'<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M4 16 16 4" stroke="currentColor" stroke-width="3" stroke-linecap="round"/><path d="M3 9.5V3h6.5M17 10.5V17h-6.5" fill="none" stroke="currentColor" stroke-width="1.6" opacity=".45"/></svg>',
adc:'<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M17 17H6l3.5-3.5h4v-4L17 6z" fill="currentColor"/><path d="M12.5 3H3v9.5" fill="none" stroke="currentColor" stroke-width="1.6" opacity=".45"/></svg>',
support:'<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 2.2 16.5 5v4.6c0 4-2.7 6.9-6.5 8.2-3.8-1.3-6.5-4.2-6.5-8.2V5z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M10 6.2v7.6M6.4 9.6h7.2" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>'};
const ROLES=[['top','Top'],['jungle','Jungle'],['mid','Mid'],['adc','ADC'],['support','Support']];
const TIERS=[['Z','Outlier'],['S',''],['A',''],['B',''],['C',''],['D',''],['P','Mains only']];
const RKS=[['e','Emerald+'],['d','Diamond+'],['m','Master+']],RGS=[['all','All'],['euw','EUW'],['kr','KR'],['na','NA']];
const RN=Object.fromEntries(RKS),GN={all:'All regions',euw:'EUW',kr:'KR',na:'NA'};
const META=CUR._meta;let ARCH=null;const DOC=PAGE==="method"||PAGE==="patch";
// pages carry one role; the rest of the patch loads on demand (and quietly after the first render)
let FULLP=null;
function ensureFull(){if(!CUR._meta.part)return Promise.resolve();return FULLP||(FULLP=fetch(SITE+'data/'+META.patch+'.json').then(r=>{if(!r.ok)throw 0;return r.json();}).then(j=>{for(const [r] of ROLES)if(!CUR[r])CUR[r]=j[r];CUR._meta.part=false;}).catch(()=>{FULLP=null;}));}
const NEXT=META.next.roles;
const GRADE=META.grade;
const SITES=[
["OP.GG","https://op.gg/lol/champions","Korea","Global, EUW, KR and NA at Emerald+, Diamond+ and Master+, plus last patch","Clean numbers and sample totals, the base of every list"],
["U.GG","https://u.gg/lol/tier-list","NA","Diamond+ and Master+, all roles","Matches OP.GG; letters follow win rate"],
["Blitz","https://blitz.gg/lol/tierlist","NA","Diamond+, all roles","Matches OP.GG; letters follow win rate"],
["dpm.lol","https://dpm.lol/tierlist","EU","Diamond+, all roles","Numbers match; letters lean on popularity"],
["League of Graphs","https://www.leagueofgraphs.com/champions/tier-list/diamond","EU (France)","Diamond+, all roles","Numbers drift; odd letters; half weight"],
["METAsrc","https://www.metasrc.com/lol/tier-list","Global","Diamond+, all roles","Letters are a popularity ranking; not scored"],
["Mobalytics","https://mobalytics.gg/lol/tier-list/high-elo","NA/EU","Expert high-elo list; stats only for all ranks","Expert list follows popularity"],
["lol.ps","https://lol.ps/statistics","Korea","KR Emerald+ top lane","Matched OP.GG KR within 0.13 points"],
["Lolalytics","https://lolalytics.com/lol/tierlist/","NA/EU","Top 20 per role, Emerald+","About 1.6 points high; tiers reward popularity"],
["Deeplol","https://www.deeplol.gg/","Korea","KR Emerald+ top lane","Matched OP.GG KR; not added"],
["WeGame, 101.qq.com",null,"China","Not public","No Chinese data"]];
const $=id=>document.getElementById(id);
const fmt=v=>{if(v==null)return 'n/a';const r=Math.round(v*10)/10;return (r>0?'+':r<0?'−':'')+Math.abs(r).toFixed(1);};
const colT=t=>{t=(t||'').replace('+','');return {Z:'--Z',S:'--S',A:'--A',B:'--B',C:'--C',D:'--D',P:'--P'}[t]||'--E';};
const narrow=()=>matchMedia('(max-width:980px)').matches;
let role='top',rank='e',reg='all',pick=null,q='',mode='tiers',sortK='cur',sortD=-1;
try{const s=localStorage.getItem('tl-mode');if(s==='tiers'||s==='table')mode=s;}catch(e){}
{const sh=new URLSearchParams(location.search).get('show');if(sh==='chart'||sh==='counter')mode=sh;}   // links from other pages: /?show=chart   // the chart is never remembered: the list is the page
try{const s=localStorage.getItem('tl-view');if(s){const [a,b]=s.split('|');if(RN[a])rank=a;if(GN[b])reg=b;}else if(localStorage.getItem('tl-lens')==='hi')rank='d';}catch(e){}
// every view (rank x region) is scored the same way; older limited archives only have Emerald+, all regions
const R=()=>LIM()?'e':rank,G=()=>LIM()?'all':reg;
const VK=(r=R(),g=G())=>g==='all'?r.toUpperCase():g+(r==='e'?'':r);          // key in d.v
const STK=(r=R(),g=G())=>g==='all'?{e:'g',d:'dia',m:'m'}[r]:VK(r,g);          // dataset behind the games, pick and ban numbers
const VNM=(r=R(),g=G())=>LIM()?'Global Emerald+':g==='all'?RN[r]:GN[g]+' '+RN[r];
const DSRC=(r=R(),g=G())=>(g==='all'?'Global ':GN[g]+' ')+RN[r];   // the OP.GG dataset behind games, pick and ban
const stat=(d,k=STK())=>{const x=d.st&&d.st[k];return x?{n:x[0],pick:x[1],ban:x[2],wr:x[3]}:k==='g'?{n:d.games,pick:d.pick,ban:d.ban,wr:d.wr}:null;};
const vw=(d,k=VK())=>{const x=d.v&&d.v[k];return x?{s:x[0],se:x[1],t:x[2]}:k==='E'?{s:d.score,se:d.se,t:d.t}:null;};
const SV=(d,k)=>{const x=vw(d,k);return x?x.s:null;};
const tierOf=(d,k)=>{const x=vw(d,k);return x?x.t:null;};
const isLow=d=>{const x=vw(d);return !!x&&x.se>=.8;};
const LOWN=1500;
const slug=c=>c.toLowerCase().replace(/[^a-z0-9]/g,'');
const ALIAS={mf:'Miss Fortune',tf:'Twisted Fate',j4:'Jarvan IV',asol:'Aurelion Sol',ww:'Warwick',gp:'Gangplank',tk:'Tahm Kench',lb:'LeBlanc',ks:"K'Sante",xz:'Xin Zhao',yi:'Master Yi',mundo:'Dr. Mundo',morde:'Mordekaiser',nunu:'Nunu & Willump',renata:'Renata Glasc',kog:"Kog'Maw",kha:"Kha'Zix",cho:"Cho'Gath",vel:"Vel'Koz",bel:"Bel'Veth",rek:"Rek'Sai"};
const hit=c=>{if(!q)return true;const k=slug(q);return !k||slug(c).includes(k)||ALIAS[k]===c||c.toLowerCase().includes(q);};
const starts=c=>{const k=slug(q);return slug(c).startsWith(k)||ALIAS[k]===c;};
const pic=(c,cl='pic')=>`<img class="${cl}" src="${IMGBASE}${slug(c)}.webp" alt="" width="64" height="64" loading="lazy" decoding="async" onerror="this.remove()">`;
const LIM=()=>!!(ARCH&&ARCH.kind==='limited');
function tri(d){if(d.tr==null||Math.abs(d.tr)<.6||chance(d)||VK()!=='E')return '';const up=d.tr>0;return `<span class="tri ${up?'up':'dn'}" title="${up?'Up':'Down'} ${Math.abs(d.tr).toFixed(1)} since ${META.prev_patch}">${up?'↑':'↓'}</span>`;}
function renderControls(){if(!DATA[role])return;
  $('roles').innerHTML=ROLES.map(([k,n])=>`<button type="button" data-r="${k}" aria-pressed="${k===role}" aria-label="${n}">${RICON[k]}<span class="rl">${n}</span></button>`).join('');
  $('modes').innerHTML=[['tiers','Tiers'],['table','Table'],['chart','Chart'],...(META.cpf&&!ARCH?[['counter','Counter']]:[])].map(([k,n])=>`<button type="button" data-mode="${k}" aria-pressed="${k===mode}">${n}</button>`).join('');
  const lim=LIM(),dv=R()!=='e'||G()!=='all',nf=(mode!=='tiers')+(!!ARCH)+(!!q);
  if($('filt'))$('filt').innerHTML=dv?`${G()==='all'?'':GN[G()]+' '}${{e:'E+',d:'D+',m:'M+'}[R()]}${nf?` <small>+${nf}</small>`:''}`:nf?`Filters (${nf})`:'Filters';
  if($('filt'))$('filt').title=dv?'Showing '+VNM()+'. Tap to change.':'';
  const dis=lim?' disabled title="Only Emerald+, all regions is kept for this patch"':'';
  $('ranks').innerHTML=RKS.map(([k,n])=>`<button type="button" data-rk="${k}" aria-pressed="${k===R()}"${k!=='e'?dis:''}>${n}</button>`).join('');
  $('regs').innerHTML=RGS.map(([k,n])=>`<button type="button" data-rg="${k}" aria-pressed="${k===G()}"${k!=='all'?dis:''}${k==='all'?' title="All regions"':''}>${n}</button>`).join('');
  document.querySelectorAll('.guide [data-rk]').forEach(b=>{b.setAttribute('aria-pressed',b.dataset.rk===R());b.disabled=lim&&b.dataset.rk!=='e';});
  document.querySelectorAll('.guide [data-rg]').forEach(b=>{b.setAttribute('aria-pressed',b.dataset.rg===G());b.disabled=lim&&b.dataset.rg!=='all';});
  const list=DATA[role],miss=list.filter(d=>tierOf(d)==null).length;
  const BLK={e:'OP.GG Global, EUW, KR and NA.',d:'Global from OP.GG, U.GG, Blitz, dpm.lol and League of Graphs, plus EUW, KR and NA.',m:'Global from OP.GG and U.GG, plus EUW, KR and NA.'};
  const BLS={e:'OP.GG',d:'OP.GG + 4 more sites',m:'OP.GG + U.GG'};
  $('vwn').textContent=lim?`Patch ${ARCH.patch}`:G()==='all'?`${RN[R()]}, all regions`:VNM();
  $('hint').textContent=(lim?'Global Emerald+ only':G()==='all'?BLS[R()]:'OP.GG only, fewer games')+(miss?`, ${miss} with no games`:'');
  $('gbtn').title=(lim?`Patch ${ARCH.patch}: Global Emerald+ only, same scoring and cutoffs.`:G()==='all'?`${RN[R()]}, all regions: ${BLK[R()]}`:`${VNM()} only, from OP.GG. Fewer games, so scores sit closer to zero.`)+(miss?` ${miss} champions have no games here.`:'')+' Tap to see which rank and region to pick.';
  $('legend').hidden=lim||mode==='chart';
}
function renderTable(){if(!DATA[role])return;
  const list=DATA[role],lim=LIM();
  // the three ranks of the current region side by side; the active one carries the ± range
  const rcols=lim?[['r_e','Score']]:RKS.map(([r,n])=>['r_'+r,n]);
  const cols=[['c','Champion'],['t','Tier'],...rcols,...(lim||VK()!=='E'?[]:[['tr','Since '+META.prev_patch]]),['wr','Win %'],['pick','Pick %'],['ban','Ban %'],['games','Games'],...(lim?[]:[['ctr','Counters']])];
  const NA='<span class="mu">–</span>';
  const SC={wr:'wr',pick:'pick',ban:'ban',games:'n'};
  const sk=sortK==='cur'?'r_'+R():sortK;
  const val=(d,c)=>c==='t'?({Z:7,S:6,A:5,B:4,C:3,D:2,P:1}[tierOf(d)]||0):c==='c'?d.c:SC[c]?(stat(d)||{})[SC[c]]:c.startsWith('r_')?SV(d,VK(c[2])):d[c];
  const rows=list.filter(d=>tierOf(d)).slice().sort((a,b)=>{const x=val(a,sk),y=val(b,sk);if(typeof x==='string')return sortD*(x<y?-1:x>y?1:0);return sortD*((x??-999)-(y??-999));});
  const cell=(d,c)=>{const v=d[c];if(c.startsWith('r_')){const r=c[2],x=vw(d,VK(r)),on=r===R();if(!x)return `<td class="n">${NA}</td>`;return `<td class="n${on?' cur':''}">${on?`<b>${fmt(x.s)}</b> <span class="mu se">±${x.se.toFixed(1)}</span>`:`${fmt(x.s)} <span class="tg sm" style="--T:var(${colT(x.t)})">${x.t}</span>`}</td>`;}
    switch(c){case 'c':return `<td class="tc">${pic(d.c)}<b>${isMine(d.c)?'<span class="mst">★</span>':''}${d.c}</b>${d.nx?nxTag(d,' tbl'):''}${d.mx!=null&&d.mx>=6?'<span class="flag mx" title="Its best players win far more than average">mastery</span>':''}</td>`;
    case 't':{const t=tierOf(d);return `<td><span class="tg" style="--T:var(${colT(t)})">${t}</span></td>`;}
    case 'tr':return `<td class="n">${v==null?NA:Math.abs(v)<.05?'<span class="mu">0.0</span>':`<span style="color:var(${v>=0?'--pos':'--neg'})">${v>=0?'↑':'↓'} ${fmt(v)}</span>`}</td>`;
    case 'wr':case 'pick':case 'ban':{const w=val(d,c);return `<td class="n">${w==null?NA:w.toFixed(c==='ban'?0:1)}</td>`;}
    case 'ctr':{const {cs}=ctrs(d);return `<td><span class="ctrs">${cs.length?cs.map(([x,wr,n])=>`<img src="${IMGBASE}${slug(x)}.webp" alt="${x}" title="${x}: ${wr.toFixed(0)}% in ${n.toLocaleString('en-US')} games" width="22" height="22" loading="lazy">`).join(''):'<span class="mu">–</span>'}</span></td>`;}
    case 'games':{const w=val(d,c);return `<td class="n${w!=null&&w<LOWN?' mu':''}">${w==null?NA:Math.round(w).toLocaleString('en-US')}</td>`;}}};
  $('board').innerHTML=`<div class="scroll tbl"><table class="tv"><thead><tr><th>#</th>${cols.map(([c,n])=>c==='ctr'?`<th data-k="${c}"><span class="thn">${n}</span></th>`:`<th data-k="${c}"${c==='r_'+R()&&!lim?' class="cur"':''}><button type="button" data-sort="${c}" aria-sort="${sk===c?(sortD<0?'descending':'ascending'):'none'}">${n}${sk===c?(sortD<0?' ↓':' ↑'):''}</button></th>`).join('')}</tr></thead><tbody>${rows.map((d,i)=>`<tr data-c="${d.c}" class="${pick===d.c?'on':''}${hit(d.c)?'':' dim'}"><td class="n mu">${i+1}</td>${cols.map(([c])=>cell(d,c)).join('')}</tr>`).join('')}</tbody></table></div>`;
  fitTable();
}
// the table never hides columns behind a sideways scroll on wide screens: next to the panel it drops, in this order,
// Counters (the panel shows matchups), Games and Ban % (the panel shows both) until it fits. Phones scroll instead.
function fitTable(){const t=document.querySelector('.tbl');if(!t)return;t.classList.remove('fit');const tb=t.querySelector('table');if(!tb)return;
  tb.querySelectorAll('[data-drop]').forEach(c=>{c.hidden=false;c.removeAttribute('data-drop');});
  if(narrow())return;
  const hs=[...tb.querySelectorAll('thead th')];
  for(const k of ['ctr','games','ban']){if(t.scrollWidth<=t.clientWidth+1)break;const i=hs.findIndex(h=>h.dataset.k===k);if(i<0)continue;
    tb.querySelectorAll(`tr>:nth-child(${i+1})`).forEach(c=>{c.hidden=true;c.dataset.drop='1';});}
  if(t.scrollWidth<=t.clientWidth+1)t.classList.add('fit');}
const LABT={Z:'Outlier: clearly ahead in every dataset with a real pick rate.',P:'Strong but rarely picked (under 1.5%). Mostly played by mains, so expect less if you are new to it.'};
let MINE=[];try{MINE=JSON.parse(localStorage.getItem('tl-mine')||'[]');}catch(e){}
const isMine=c=>MINE.includes(role+'|'+c)||MINE.includes(c);
function toggleMine(c){MINE=isMine(c)?MINE.filter(x=>x!==c&&x!==role+'|'+c):[...MINE,role+'|'+c];try{localStorage.setItem('tl-mine',JSON.stringify(MINE));}catch(e){}renderBoard();renderPanel();}
const isTrap=d=>{const x=stat(d),v=SV(d);return !!x&&v!=null&&x.pick>=5&&v<=-.3;};
const kfmt=n=>n>=1e6?(n/1e6).toFixed(1)+'M':n>=1e4?Math.round(n/1e3)+'k':n>=1e3?(n/1e3).toFixed(1)+'k':String(Math.round(n));
const chipHTML=(d,tag,size='')=>{const low=isLow(d),x=stat(d),big=size==='big',vx=vw(d);return `<button type="button" class="chip${size?' '+size:''}${hit(d.c)?'':' dim'}${low?' low':''}" data-c="${d.c}" aria-pressed="${pick===d.c}"${big?` style="--art:url(${SITE}img/splash/${slug(d.c)}.webp)"`:''}${low?` title="Few games${x?` (${x.n.toLocaleString('en-US')} in ${VNM()})`:''}, could be off by ±${vx.se.toFixed(1)}"`:''}><span class="chpf">${pic(d.c)}${badges(d)}</span><span class="nm">${!tag&&isMine(d.c)?'<span class="mst">★</span>':''}<span class="nmt${d.c.length>=12?' l2':d.c.length>=10?' l1':''}">${d.c}</span>${tag?`<span class="tg sm" style="--T:var(${colT(tierOf(d))})">${tierOf(d)}</span>`:''}</span><span class="sc">${tri(d)}<b>${fmt(vx&&vx.s)}</b></span>${big&&x?`<span class="cm">${x.pick.toFixed(1)}% pick · ${kfmt(x.n)} games</span>`:''}</button>`;};
function poolHTML(mine){
  const best=mine[0],cnt={};
  for(const d of mine)for(const [c] of ctrs(d).cs)if(!mine.some(m=>m.c===c))cnt[c]=(cnt[c]||0)+1;
  const bans=Object.entries(cnt).filter(([,n])=>n>=2).sort((a,b)=>b[1]-a[1]).slice(0,2);
  let t=mine.length>1?`Best of yours this patch: <b>${best.c}</b> (${tierOf(best)}, ${fmt(SV(best))}).`:'';
  if(bans.length)t+=` Ban ${bans.map(([c,n])=>`<b>${c}</b>`).join(' or ')}: hard matchup for ${bans[0][1]} of your ${mine.length}.`;
  else if(mine.length===1){const {cs}=ctrs(best);if(cs.length)t=`Hardest matchups for ${best.c}: ${cs.map(([c,wr])=>`<b>${c}</b> (${wr.toFixed(0)}%)`).join(', ')}.`;}
  return t?`<p class="mi">${t}</p>`:'';
}
function sinceVisit(){
  if(ARCH)return;if(!DATA[role]){ensureFull().then(()=>{if(DATA[role])sinceVisit();});return;}let seen=null;try{seen=JSON.parse(localStorage.getItem('tl-seen')||'null');}catch(e){}
  const list=DATA[role],rn=ROLES.find(r=>r[0]===role)[1],t=Object.assign({},seen&&seen.t||{});
  let html='';
  if(seen&&seen.p&&seen.p!==META.patch){
    const mv=list.filter(d=>d.tr!=null&&d.pick>=1&&Math.abs(d.tr)>=.4&&!chance(d)).sort((a,b)=>b.tr-a.tr);
    const up=mv.filter(d=>d.tr>0).slice(0,2),dn=mv.filter(d=>d.tr<0).slice(-2).reverse();
    const tk=d=>VK()+'|'+role+'|'+d.c,ch=list.filter(d=>isMine(d.c)&&tierOf(d)&&t[tk(d)]&&t[tk(d)]!==tierOf(d)).map(d=>`<b>${d.c}</b> ${t[tk(d)]} → ${tierOf(d)}`);
    html=`<div class="since"><span><b>Patch ${META.patch} is in since your last visit.</b> ${rn}: ${[...up.map(d=>`<b>${d.c}</b> up ${fmt(d.tr)}`),...dn.map(d=>`<b>${d.c}</b> down ${fmt(d.tr)}`)].join(', ')||'no clear moves'}.${ch.length?` Your champs in ${VNM()}: ${ch.join(', ')}.`:''}</span><button type="button" class="x2" id="sincex" aria-label="Close">×</button></div>`;
  }
  for(const d of list)if(isMine(d.c)&&tierOf(d))t[VK()+'|'+role+'|'+d.c]=tierOf(d);
  try{localStorage.setItem('tl-seen',JSON.stringify({p:META.patch,t}));}catch(e){}
  if(html){$('since').innerHTML=html;$('since').hidden=false;}
}
function flipRender(fn){
  if(mode!=='tiers'||matchMedia('(prefers-reduced-motion: reduce)').matches){fn();return;}
  const pos={};document.querySelectorAll('#board .row:not(.mine-row) .chip').forEach(el=>{pos[el.dataset.c]=el.getBoundingClientRect();});
  fn();
  document.querySelectorAll('#board .row:not(.mine-row) .chip').forEach(el=>{const a=pos[el.dataset.c];if(!a)return;const b=el.getBoundingClientRect(),dx=a.left-b.left,dy=a.top-b.top;
    if(Math.abs(dx)<1&&Math.abs(dy)<1)return;el.animate([{transform:`translate(${dx}px,${dy}px)`,zIndex:5},{transform:'none',zIndex:5}],{duration:460,easing:'cubic-bezier(.2,.7,.2,1)'});});
}
function renderBoard(){if(!DATA[role])return;
  if(mode==='table'){renderTable();return;}
  if(mode==='chart'){renderChart();return;}
  if(mode==='counter'){renderCounter();return;}
  const list=DATA[role];
  $('board').innerHTML=TIERS.map(([t,cap],ti)=>{
    const cs=list.filter(d=>tierOf(d)===t).sort((a,b)=>(SV(b)??-99)-(SV(a)??-99));
    if(!cs.length&&(t==='Z'||t==='P'))return '';
    const size=t==='Z'||t==='S'?'big':t==='C'||t==='D'?'sm':'';
    const body=cs.length?cs.map(d=>chipHTML(d,false,size)).join(''):'<span class="empty">None</span>';
    return `<div class="row t-${t}" style="--T:var(${colT(t)})"><div class="lab"${LABT[t]?` title="${LABT[t]}"`:''}><span class="lt">${t}</span>${cap?`<small>${cap}</small>`:''}</div><div class="chips${size==='big'?' bigs':size==='sm'?' smalls':''}">${body}</div></div>`;
  }).join('');
  const mine=list.filter(d=>isMine(d.c)&&tierOf(d)).sort((a,b)=>(SV(b)??-99)-(SV(a)??-99));
  if(mine.length)$('board').insertAdjacentHTML('afterbegin',`<div class="row mine-row" style="--T:var(--acc)"><div class="lab" title="Your champions, saved in this browser only"><span class="lt">★</span><small>Yours</small></div><div class="chips">${mine.map(d=>chipHTML(d,true)).join('')}${poolHTML(mine)}</div></div>`);
}
const OPGG={wukong:'monkeyking',nunuwillump:'nunu',renataglasc:'renata'};
const opgg=(c,pg='build')=>`https://op.gg/lol/champions/${OPGG[slug(c)]||slug(c)}/${pg}/${role}`;
const HIGHV=()=>R()!=='e';
function renderPanel(){if(!DATA[role])return;
  const d=DATA[role].find(x=>x.c===pick);if(!d){$('panel').innerHTML='';$('panel').dataset.key='';return;}
  const rn=ROLES.find(r=>r[0]===role)[1],sx=stat(d)||{},vx=vw(d)||{},lim=LIM();
  // every rank x region view: score and tier; tapping one switches the whole list to it
  const gcell=(r,g)=>{const x=vw(d,VK(r,g)),on=r===R()&&g===G();if(!x)return `<td class="na">–</td>`;const n=d.st&&d.st[STK(r,g)];
    return `<td class="${on?'on':''}" style="--T:var(${colT(x.t)})"><button type="button" data-rk="${r}" data-rg="${g}" title="${VNM(r,g)}: ${x.t} tier, ${fmt(x.s)} ±${x.se.toFixed(1)}${n?`, ${n[0].toLocaleString('en-US')} games`:''}. Tap to show this list." aria-label="${VNM(r,g)}: ${x.t} tier, ${fmt(x.s)}. Show this list"><b>${fmt(x.s)}</b><i>${x.t}</i></button></td>`;};
  const grid=`<table class="hm"><thead><tr><th></th>${RKS.map(([,n])=>`<th>${n}</th>`).join('')}</tr></thead><tbody>${RGS.map(([g,n])=>`<tr><th>${n}</th>${RKS.map(([r])=>gcell(r,g)).join('')}</tr>`).join('')}</tbody></table>`;
  const SNM={'Mobalytics experts':'Mobalytics'};
  const sites=Object.entries(d.sites||{}).filter(([k,v])=>v).map(([k,v])=>`<span class="site"${SNM[k]?` title="${k}"`:''}>${SNM[k]||k}<b style="--T:var(${colT(v)})">${v}</b></span>`).join('')+(d.ll?`<span class="site" title="Lolalytics, Emerald+">Lolalytics E+<b style="--T:var(${colT(d.ll)})">${d.ll}</b></span>`:'');
  const tex=[pkShift(d),chance(d)&&Math.abs(d.tr)>=.05?'too small to be sure':''].filter(Boolean).join(', ');
  const tr=d.tr==null||ARCH?'':`<p class="trend">Since ${META.prev_patch} (Global Emerald+): ${Math.abs(d.tr)<.05?'<b>no change</b>':`<b style="color:var(${d.tr>0?'--pos':'--neg'})">${d.tr>0?'↑':'↓'} ${fmt(d.tr)}</b>`}${tex?`, ${tex}`:''}</p>`;
  const tt=t=>t?`<span class="tg sm" style="--T:var(${colT(t)})">${t}</span>`:'';
  const PH=`<div class="pin"><div class="pban" style="--art:url(${SITE}img/splash/${slug(d.c)}.webp)"></div><div class="ph">${pic(d.c,'pic big')}<div class="pht"><h3>${!ARCH&&PAGE!=='champ'?`<a href="${champURL(d.c)}" title="Open the full page for ${d.c}">${d.c}<svg class="go" viewBox="0 0 16 16" aria-hidden="true"><path d="M5 11 11 5M6 5h5v5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></a>`:d.c}</h3><p class="rolesub">${rn} · ${sx.n!=null?sx.n.toLocaleString('en-US'):'No'} games in ${DSRC()}${d.mx!=null&&d.mx>=6?' · <b class="mxb">Rewards mastery</b>':''}</p></div><button type="button" class="x" id="x" aria-label="Close">×</button></div>
  <div class="acts"><button type="button" class="star" data-star="${d.c}" aria-pressed="${isMine(d.c)}" title="${isMine(d.c)?'Remove from your champions':'Save to your champions (this browser only)'}">${isMine(d.c)?'★ My champ':'☆ My champs'}</button><a class="ext" href="${opgg(d.c)}" target="_blank" rel="noopener" title="Builds and runes on OP.GG">OP.GG build ↗</a><button type="button" class="ext ico" data-share="${d.c}" aria-label="Share ${d.c}" title="Share"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 3v10M6 7l4-4 4 4M4 12v4h12v-4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></button></div>
  <div class="kv"><div class="km" data-tip="Win rate points above the role average in ${VNM()}, corrected for sample size and one-tricks. ± is a rough 90% range."><span><u>${VNM()}</u></span><strong>${tt(vx.t)}${fmt(vx.s)}<small> ±${vx.se==null?'?':vx.se.toFixed(1)}</small></strong>${rngHTML(d)}</div><div><span>Win</span><strong>${sx.wr==null?'–':sx.wr.toFixed(1)+'%'}</strong></div><div><span>Pick</span><strong>${sx.pick==null?'–':sx.pick.toFixed(1)+'%'}</strong></div><div><span>Ban</span><strong>${sx.ban==null?'–':sx.ban.toFixed(0)+'%'}</strong></div></div>
  ${lim?`<p class="cap">Older patches keep Global Emerald+ only.</p>`:`<p class="cap">Every rank and region. Tap one to show that list.</p>${grid}`}
  ${d.note?`<p class="note">${d.note}</p>`:''}
  ${histHTML(d,tr)||tr}${d.ch&&!ARCH?`<p class="nx ${d.ch[0]}">${CHW[d.ch[0]]||'Changed'} in ${META.patch}: ${d.ch[1]}.${nlink(META.patch,d.c)}</p>`:''}${d.it&&!ARCH?d.it.map(([n,k,t])=>`<p class="nx ${k}">${n}, one of its core items, ${ITW[k]||'changed'} in ${META.patch}: ${t}.${nlink(META.patch,n,1)}</p>`).join(''):''}${d.nx?`<p class="nx ${d.nx}">${d.nx==='buff'?'Buff':'Nerf'} coming in ${META.next.patch}: ${d.nxt}.${nlink(META.next.patch,d.c)}</p>`:''}
  ${glHTML(d)}${buildHTML(d)}${ctrHTML(d)}${duoHTML(d)}
  ${sites?`<div class="sites"><span class="sl">Other sites, Diamond+:</span>${sites}</div>`:''}</div>`;
  const key=role+'|'+d.c+'|'+(ARCH?ARCH.patch:''),P0=$('panel');
  if(P0.dataset.key===key&&P0.firstElementChild){const t=document.createElement('template');t.innerHTML=PH;morph(P0.firstElementChild,t.content.firstElementChild);}
  else{P0.innerHTML=PH;P0.dataset.key=key;}
}
// update the panel in place: keep every element, only change what differs, fade just the changed numbers
function morph(a,b){
  if(a.nodeType!==b.nodeType||a.nodeName!==b.nodeName){a.replaceWith(b);return;}
  if(a.nodeType===3){if(a.data!==b.data){a.data=b.data;const el=a.parentElement;if(el&&el.animate&&!matchMedia('(prefers-reduced-motion: reduce)').matches)el.animate([{opacity:.25},{opacity:1}],{duration:260,easing:'ease-out'});}return;}
  if(a.nodeType!==1)return;
  for(const at of [...a.attributes])if(!b.hasAttribute(at.name))a.removeAttribute(at.name);
  for(const at of [...b.attributes])if(a.getAttribute(at.name)!==at.value)a.setAttribute(at.name,at.value);
  const ac=[...a.childNodes],bc=[...b.childNodes];
  for(let i=0;i<Math.max(ac.length,bc.length);i++){if(i>=ac.length)a.appendChild(bc[i]);else if(i>=bc.length)ac[i].remove();else morph(ac[i],bc[i]);}
}
let HIST=null,HISTP=null;
function histHTML(d,tr=''){
  if((META.hist||0)<3||ARCH)return '';
  if(!HIST){if(!HISTP)HISTP=fetch(SITE+'data/history.json').then(r=>r.json()).then(j=>{HIST=j;renderPanel();}).catch(()=>{});return '';}
  const v=(HIST.roles[role]||{})[d.c],P=HIST.patches;if(!v||v.filter(x=>x!=null).length<3)return '';
  const W=320,H=78,L=8,R=40,T=8,B=20,nn=v.filter(x=>x!=null),lo=Math.min(-1,...nn),hi=Math.max(1,...nn);
  const X=i=>L+i/(P.length-1)*(W-L-R),Y=x=>T+(hi-x)/(hi-lo)*(H-T-B);
  let path='';v.forEach((x,i)=>{if(x==null)return;path+=(path&&v[i-1]!=null?'L':'M')+X(i).toFixed(1)+' '+Y(x).toFixed(1);});
  const li=v.length-1-[...v].reverse().findIndex(x=>x!=null),fi=v.findIndex(x=>x!=null);
  return `<p class="cap">Global Emerald+ by patch${tr?' · '+tr.replace(/<\/?p[^>]*>/g,'').replace(/^Since [^:]*: /,'since '+META.prev_patch+' '):''}</p><svg class="hist" viewBox="0 0 ${W} ${H}" role="img" aria-label="${d.c} by patch: ${v.map((x,i)=>P[i]+' '+(x==null?'no data':fmt(x))).join(', ')}">
  <line x1="${L}" x2="${W-R}" y1="${Y(0)}" y2="${Y(0)}" class="z"/>
  <path d="${path}" class="ln"/>${v.map((x,i)=>x==null?'':`<circle cx="${X(i)}" cy="${Y(x)}" r="${i===li?4:2.6}" class="${x>=0?'p':'n'}"><title>${P[i]}: ${fmt(x)}</title></circle>`).join('')}
  <text x="${X(li)+8}" y="${Y(v[li])+4}" class="lv">${fmt(v[li])}</text>
  <text x="${X(fi)}" y="${H-4}" class="pt">${P[fi]}</text><text x="${X(li)}" y="${H-4}" class="pt" text-anchor="end">${P[li]}</text></svg>`;
}
const cutT=v=>v>=1.15?'S':v>=.6?'A':v>=.15?'B':v>=-.45?'C':'D',TRANK={S:4,A:3,B:2,C:1,D:0};
function rngHTML(d){const x=vw(d);if(!x||!'SABCD'.includes(x.t)||x.se==null)return '';const lo=cutT(x.s-x.se),hi=cutT(x.s+x.se);return lo===hi?'':`<small class="rng" title="With the ± range this champion could sit anywhere from ${lo} to ${hi}">could be ${lo===x.t?hi:hi===x.t?lo:lo+' to '+hi}</small>`;}
const champURL=c=>SITE+role+'/'+slug(c)+'/';
// why something moved, only from facts: this patch's change (patch notes), a big shift in pick rate, or a change too small to tell from chance
const CHW={buff:'Buffed',nerf:'Nerfed'};
// next patch tag on chips and table rows: says that the change is coming, not that it happened
const BDG={buff:'<path d="M5 1.5 9 8H1z"/>',nerf:'<path d="M1 2h8L5 8.5z"/>',trap:'<path d="M4 1h2l-.3 5.2H4.3zM4.1 7.3h1.8V9H4.1z"/>'};
const badge=(k,t,lab)=>`<span class="bdg ${k}" title="${t}"><svg viewBox="0 0 10 10" aria-hidden="true">${BDG[k]}</svg><span class="sr">${lab}</span></span>`;
// next-patch change and "trap" sit as small marks on the portrait corner, so names stay on one line
const nxTag=(d,cl='')=>`<span class="nxp ${d.nx}${cl}" title="${d.nx==='buff'?'Buff':'Nerf'} coming in ${META.next.patch} (${META.next.date})${d.nxt?': '+d.nxt:''}"><svg viewBox="0 0 10 10" aria-hidden="true">${BDG[d.nx]}</svg>${META.next.patch}<span class="sr"> ${d.nx} coming</span></span>`;
const badges=d=>(d.nx&&META.next?nxTag(d):'')+(isTrap(d)?badge('trap','Trap: picked a lot, still losing','trap'):'');
const nxFlag=d=>`<span class="flag ${d.nx}" title="${d.nx==='buff'?'Buff':'Nerf'} coming in ${META.next.patch} (${META.next.date})${d.nxt?': '+d.nxt:''}">${d.nx} soon</span>`;
// links to the patch notes page when it has the champion or item
const nlink=(p,c,item)=>((META.notes||{})[p]||[]).includes(c)?` <a class="nxa" href="${SITE}patch/${p}/${item?'i-':''}${slug(c)}/">All numbers</a>`:'';   // the change's own page: its address is the link to share
const chLine=d=>d.ch?`${CHW[d.ch[0]]||'Changed'}: ${d.ch[1]}`:'';
const ITW={buff:'buffed',nerf:'nerfed'};
const itLine=d=>d.it?`Core item ${ITW[d.it[0][1]]||'changed'}: ${d.it.map(x=>x[0]).join(', ')}`:'';
const pkShift=d=>{if(d.pk0==null||!d.pick)return '';const r=d.pick/d.pk0;return (r>=1.5||r<=1/1.5)&&Math.max(d.pick,d.pk0)>=1?`pick rate ${d.pk0.toFixed(1)}% → ${d.pick.toFixed(1)}%`:'';};
const chance=d=>d.trz!=null&&Math.abs(d.trz)<1.64;
function share(c){const url=c?champURL(c):PAGE==='home'?SITE:SITE+role+'/',title=c?`${c} ${ROLES.find(r=>r[0]===role)[1]}, patch ${META.patch} | LoL Tier List`:document.title;
  if(navigator.share&&matchMedia('(pointer:coarse)').matches){navigator.share({title,url}).catch(()=>{});return;}
  const done=()=>{const t=document.createElement('div');t.className='toast';t.textContent='Link copied';document.body.appendChild(t);setTimeout(()=>t.remove(),1800);};
  (navigator.clipboard?navigator.clipboard.writeText(url):Promise.reject()).then(done).catch(()=>{prompt('Copy this link',url);});}
const CMIN=150;
// build: OP.GG's most common summoner spells, runes, starting items, core items and boots (Global Emerald+), and in "More"
// the next options with how often they are taken and how often they win, plus Riot's own description of each spell and keystone.
// OP.GG does not say when players take which option, so nothing here says "take X against Y".
const LK=()=>META.lk||{i:{},s:{},r:{}};
const bimg=(kind,id,cl='')=>{const L=LK(),nm=kind==='item'?L.i[id]:kind==='sum'?(L.s[id]||[])[0]:(L.r[id]||[])[0];return `<img class="${cl}" src="${SITE}img/${kind}/${id}.webp" alt="${nm||''}" title="${nm||''}" width="28" height="28" loading="lazy">`;};
// win rate by game length (OP.GG trends, Global Emerald+): each bucket against the champion's own win rate. Bucket sizes
// are estimates (OP.GG gives none), so a value is grey when its gap could be luck. The sentence only speaks when short
// and long games clearly differ (update.py: 2+ points and beyond sampling noise).
function glHTML(d){const g=d.gl;if(!g||ARCH)return '';
  const W=340,H=112,L=14,R=14,T=22,Bm=24,xs=i=>L+i*(W-L-R)/4;
  const span=Math.max(5,...g.b.map(x=>Math.abs(x[1]-g.w)))+1.2,ys=v=>T+(H-T-Bm)*(1-(v-(g.w-span))/(2*span));
  const pts=g.b.map((x,i)=>[xs(i),ys(x[1])]),path=pts.map((p,i)=>(i?'L':'M')+p[0].toFixed(1)+' '+p[1].toFixed(1)).join(' ');
  const LB=['<25','25-30','30-35','35-40','40+'],avgY=ys(g.w);
  const area=`M${xs(0)} ${avgY} `+pts.map(p=>'L'+p[0].toFixed(1)+' '+p[1].toFixed(1)).join(' ')+` L${xs(4)} ${avgY} Z`;
  const svg=`<svg class="glc" viewBox="0 0 ${W} ${H}" role="img" aria-label="Win rate by game length: ${g.b.map((x,i)=>LB[i]+' minutes '+x[1].toFixed(1)+'%').join(', ')}">
    <path d="${area}" class="gla"/><line x1="${L}" x2="${W-R}" y1="${avgY}" y2="${avgY}" class="glm"/>
    <path d="${path}" class="gll"/>
    ${g.b.map((x,i)=>`<circle cx="${pts[i][0]}" cy="${pts[i][1]}" r="4" class="${x[3]?'on':'off'}"><title>${LB[i]} min: ${x[1].toFixed(1)}% win in about ${kfmt(x[2])} games${x[3]?'':', too few to be sure it differs'}</title></circle>
      <text x="${pts[i][0]}" y="${pts[i][1]-9}" class="glv${x[3]?'':' off'}">${x[1].toFixed(1)}</text>
      <text x="${pts[i][0]}" y="${H-6}" class="glx">${LB[i]}</text>`).join('')}
  </svg>`;
  const v=g.v==='late'?`Wins more the longer the game goes: <b>+${g.d.toFixed(1)}</b> points over 35 minutes compared with under 25.`:g.v==='early'?`Wins more in short games: <b>${Math.abs(g.d).toFixed(1)}</b> points better under 25 minutes than over 35.`:'About the same at every game length.';
  return `<div class="caph"><p class="cap">Win rate by game length <span class="mu">OP.GG Emerald+, minutes</span></p></div><div class="glw">${svg}<p class="glk"><span class="glkm"></span>${d.c}'s usual ${g.w.toFixed(1)}% <span class="glkh"></span>too few games to be sure</p></div><p class="glt">${v}</p>`;}
// build card: one short row per part (spells, runes, skills, start, core, boots) with OP.GG's most common pick and its share
// of games. Tapping a row opens the other options: share, win rate (grey when within sampling noise of the usual pick),
// and the matchups where players switch to that option (OP.GG matchup builds, d.bd.vs). Nothing here says what to do;
// it shows what players actually do, and against whom.
const pct=v=>v<10?v.toFixed(1)+'%':Math.round(v)+'%';
const weakVs=(win,games,ref)=>ref&&games&&ref[1]&&Math.abs(win-ref[0])<1.64*Math.sqrt(2500/games+2500/ref[1]);
function buildHTML(d){const b=d.bd;if(!b||ARCH)return '';const L=LK(),chg=new Set((d.it||[]).map(x=>x[0])),vs=b.vs||{};
  const items=ids=>ids.map(id=>bimg('item',id,chg.has(L.i[id])?'chg':'')).join(''),inames=ids=>ids.map(i=>L.i[i]||'').join(' + ');
  const ab=k=>`<img src="${SITE}img/spell/${slug(d.c)}_${k.toLowerCase()}.webp" alt="${k}" title="${k}" width="26" height="26" loading="lazy">`;
  // each part: [label, options, icons(o), name(o), share(o), win(o), games(o), key(o) for the switch data]
  const P=[['Spells',b.sp,o=>o[0].map(i=>bimg('sum',i)).join(''),o=>o[0].map(i=>(L.s[i]||[])[0]).join(' + '),o=>o[1],o=>o[2],o=>o[3],o=>'sp:'+o[0].join(',')],
    ['Runes',b.rn,o=>`${bimg('rune',o[0],'rn')}${bimg('rune',o[2],'rn tr')}`,o=>`${(L.r[o[0]]||[])[0]||''} + ${(L.r[o[2]]||[])[0]||''}`,o=>o[6],o=>o[7],o=>o[5],o=>'rn:'+o[0]],
    ['Start',b.st,o=>items(o[0]),o=>inames(o[0]),o=>o[1],o=>o[2],o=>o[3],o=>'st:'+o[0].join(',')],
    ['Core',b.co,o=>items(o[0]),o=>o[0].map(i=>L.i[i]||'').join(', '),o=>o[1],o=>o[2],o=>o[3],o=>'co:'+o[0].join(',')],
    ['Boots',b.bo,o=>items([o[0]]),o=>L.i[o[0]]||'',o=>o[1],o=>o[2],o=>o[3],o=>'bo:'+o[0]]];
  // [type of opponent or null, [[opponent, % of games with this option in that matchup, games], ...]]
  const faces=k=>{const v=vs[k];if(!v)return '';const ex=v[1].map(([c,sh,n])=>`<span class="bvs" title="${d.c} players take it in ${sh.toFixed(0)}% of ${n.toLocaleString('en-US')} games against ${c}">${pic(c,'pic xs')}${c} <b>${pct(sh)}</b></span>`);
    return v[0]?`More vs <b class="bty">${v[0]}</b>, like ${ex[0]}`:`More vs ${ex.join('')}`;};
  const part=([lab,opts,ic,nm,sh,wn,gm,key])=>{if(!opts||!opts.length)return '';const o=opts[0],ref=[wn(o),gm(o)];
    const head=`<span class="blab">${lab}</span><span class="bic">${ic(o)}</span><span class="bnm">${nm(o)}</span><span class="bsh">${pct(sh(o))}</span>`;
    if(opts.length<2)return `<div class="brow">${head}<span class="bch"></span></div>`;
    const seen=new Set([key(o)]);
    const alt=opts.slice(1).map(x=>{const weak=weakVs(wn(x),gm(x),ref),f=seen.has(key(x))?'':faces(key(x));seen.add(key(x));
      return `<div class="balt"><span class="bic">${ic(x)}</span><span class="bnm">${nm(x)}</span><span class="bst">${pct(sh(x))} · <span class="${weak?'wk':''}"${weak?' title="Too few games to say it wins more or less than the usual pick"':''}>${wn(x).toFixed(1)}% win</span></span>${f?`<span class="bsw">${f}</span>`:''}</div>`;}).join('');
    return `<details class="brow sm-d"><summary>${head}<span class="bch" aria-hidden="true"></span></summary><div class="dc"><div class="bwin">${nm(o)}: ${wn(o).toFixed(1)}% win${lab==='Core'||lab==='Boots'?'. Item win rates run high, whoever finishes items is often ahead already.':''}</div>${alt}</div></details>`;};
  const sk=b.sk?`<div class="brow"><span class="blab">Skills</span><span class="bic">${b.sk[0].split('').map(ab).join('')}</span><span class="bnm">${b.sk[0].split('').join(' > ')}</span><span class="bsh" title="Levels 1 to 3">start ${b.sk[1].split('').join(' ')}</span><span class="bch"></span></div>`:'';
  const rows=[part(P[0]),part(P[1]),sk,part(P[2]),part(P[3]),part(P[4])].join('');
  if(!rows)return '';
  return `<div class="caph"><p class="cap">Build <span class="mu">OP.GG Emerald+</span></p><a class="ctrl" href="${opgg(d.c,'build')}" target="_blank" rel="noopener">Full build ↗</a></div>`
    +`<div class="bld">${rows}</div><p class="bnote">% = share of games. Tap a row for what else players take.</p>`;
}
// matchups from OP.GG's full matchup lists (Global): Emerald+, or Diamond+ when the view is Diamond+ or Master+. Up to 5 hardest
// and 5 easiest opponents with 150+ games, ranked after pulling each toward the champion's own win rate (update.py), as
// [opponent, win rate of this champion, games, clear]. Older patches only have OP.GG's three hardest matchups (ctr).
function ctrs(d){const dia=R()!=='e'&&d.mud,m=dia?d.mud:d.mu,ok=a=>(a||[]).filter(x=>Array.isArray(x)&&x[2]>=CMIN);
  if(m)return {m,rk:dia?'Diamond+':'Emerald+',cs:ok(m.h),gs:ok(m.g)};
  const ee=ok(d.ctr);return {rk:'Emerald+',cs:ee,gs:[],thin:!ee.length&&(d.ctr||[]).length>0};}
function ctrHTML(d){
  const {m,rk,cs,gs,thin}=ctrs(d);const inRole=c=>DATA[role].some(x=>x.c===c);
  const all=`<a class="ctrl" href="${opgg(d.c,'counters')}" target="_blank" rel="noopener">All matchups ↗</a>`;
  const head=`<div class="caph"><p class="cap">Matchups <span class="mu">OP.GG ${rk}${m?`, vs ${d.c}'s usual ${m.o.toFixed(1)}%`:''}</span></p>${all}</div>`;
  if(!cs.length&&!gs.length)return thin||((d.ctr||[]).length)||m?`${head}<p class="mi0">OP.GG's matchups for ${d.c} each have under ${CMIN} games, or none differs from ${d.c}'s usual win rate.</p>`:'';
  const card=([c,wr,n,cl],good)=>{const weak=cl===0,inner=`${pic(c,'pic xs')}<span>${c}</span><small${weak?' class="lowdemo"':''}>${wr.toFixed(0)}% · ${kfmt(n)} games</small>`,
    tip=`${d.c} wins ${wr.toFixed(1)}% of ${n.toLocaleString('en-US')} games against ${c}`+(m?(weak?`. Too few games to be sure that differs from ${d.c}'s usual ${m.o.toFixed(1)}%.`:`, against ${m.o.toFixed(1)}% usually.`):''),cl2=`cc${good?' good':''}`;
    return inRole(c)?`<button type="button" class="${cl2}" data-c="${c}" title="${tip}">${inner}</button>`:`<span class="${cl2}" title="${tip}">${inner}</span>`;};
  const grid=(L,good)=>`<div class="ctr">${L.map(x=>card(x,good)).join('')}</div>`;
  const more=cs.length>3||gs.length>3;
  const foot=m&&[...cs,...gs].some(x=>x[3]===0)?`<p class="bnote"><b class="lowdemo">Grey</b> = too few games to be sure. Only matchups with ${CMIN}+ games.</p>`:'';
  return `${head}${cs.length?`<p class="mlab">Hardest for ${d.c}</p>${grid(cs.slice(0,3),0)}`:''}${gs.length?`<p class="mlab">Easiest for ${d.c}</p>${grid(gs.slice(0,3),1)}`:''}`
    +(more?`<details class="pmore sm-d"><summary>More matchups</summary><div class="dc">${cs.length>3?`<p class="mlab">Also hard</p>${grid(cs.slice(3),0)}`:''}${gs.length>3?`<p class="mlab">Also easy</p>${grid(gs.slice(3),1)}`:''}</div></details>`:'')+foot
    +(META.cpf&&!ARCH?`<button type="button" class="cpgo" data-cpgo="${d.c}">Who beats ${d.c}? <span>See every pick ranked</span></button>`:'');
}
// counter-pick finder (layout "Counter pick"): tap the enemy laner, see who wins most against it in this role. From the
// enemy's own OP.GG matchup list turned around (Emerald+, or Diamond+ for the Diamond+ and Master+ views), ranked by the
// gap to what an average opponent gets, pulled toward 0 by sample size like the panel's matchups (update.py). Loads
// data/<patch>-counters.json the first time it opens.
let CPD=null,CPE='',CPall=false;
function renderCounter(){
  if(!META.cpf||ARCH){$('board').innerHTML='<p class="empty">The counter-pick finder only covers the current patch.</p>';return;}
  if(!CPD){$('board').innerHTML='<p class="empty">Loading matchups…</p>';fetch(`${SITE}data/${META.cpf}`).then(r=>r.json()).then(j=>{CPD=j;if(mode==='counter')renderCounter();}).catch(()=>{$('board').innerHTML='<p class="empty">Could not load the matchups. Reload to try again.</p>';});return;}
  const rk=R()==='e'?'e':'d',D=CPD[rk],RN={top:'Top',jungle:'Jungle',mid:'Mid',adc:'ADC',support:'Support'}[role]||role;
  const list=(DATA[role]||[]).filter(d=>tierOf(d)).slice().sort((a,b)=>((stat(b)||{}).pick||0)-((stat(a)||{}).pick||0));
  if(CPE&&!list.some(d=>d.c===CPE))CPE='';
  const grid=`<div class="cpg" id="cpg">${list.map(d=>`<button type="button" class="cpe${d.c===CPE?' on':''}" data-cpe="${d.c}" data-n="${d.c.toLowerCase()}" aria-pressed="${d.c===CPE}">${pic(d.c)}<span>${d.c}</span></button>`).join('')}</div>`;
  let res='';
  if(CPE){const rows=((D.r||{})[role]||{})[CPE]||[];
    const item=([i,wr,n,cl])=>{const c=D.names[i],d=list.find(x=>x.c===c),tt=d?tierOf(d):null,w=wr/10;
      return `<button type="button" class="cpr${isMine(c)?' mine':''}" data-c="${c}" title="${c} wins ${w.toFixed(1)}% of ${n.toLocaleString('en-US')} games against ${CPE}${cl?'':', too few to be sure it differs'}">${pic(c)}<span class="cpn">${isMine(c)?'<span class="mst">★</span>':''}${c}${tt?`<span class="tg sm" style="--T:var(${colT(tt)})">${tt}</span>`:''}</span><span class="cpgm">${kfmt(n)} games</span><span class="cpw${cl?(w>=50?' good':' bad'):' lowdemo'}">${w.toFixed(1)}%</span></button>`;};
    const mine=rows.filter(r=>isMine(D.names[r[0]])),shown=CPall?rows:rows.slice(0,matchMedia('(min-width:981px)').matches?24:12);
    res=`<div class="cph"><div class="cpsel">${pic(CPE)}<div><h3>Best picks into ${CPE}</h3><p class="cap">${RN}, OP.GG ${rk==='e'?'Emerald+':'Diamond+'}: win rate against ${CPE} in lane. Ranked with the number of games in mind, so 52% over 2,000 games beats 55% over 250.</p></div><button type="button" class="cpchg" id="cpchange">Change enemy</button></div></div>`
      +(mine.length?`<p class="mlab">Your champions</p><div class="cpl">${mine.map(item).join('')}</div><p class="mlab">Everyone</p>`:'')
      +(rows.length?`<div class="cpl">${shown.map(item).join('')}</div>${rows.length>shown.length||CPall?`<button type="button" class="xmore" id="cpmore" aria-expanded="${CPall}">${CPall?'Show fewer':`Show all ${rows.length}`}</button>`:''}<p class="bnote"><b class="lowdemo">Grey</b> = too few games to be sure it differs from an average pick. Only matchups with 150+ games. Tap a champion for its build and more.</p>`:`<p class="empty">No matchup against ${CPE} has 150+ games yet.</p>`);}
  $('board').innerHTML=`<div class="cp"><button type="button" class="cpback" data-mode="tiers">← Back to the tier list</button>${CPE?`<div id="cpres">${res}</div>`:`<div class="cph"><h3>Counter pick</h3><p class="cap">Tap the enemy ${RN} laner to see who wins most against them. Most played first.</p></div><input type="search" class="cpq" id="cpq" placeholder="Find the enemy champion" autocomplete="off">${grid}`}</div>`;
}
document.addEventListener('input',e=>{if(e.target.id!=='cpq')return;const v=e.target.value.trim().toLowerCase();document.querySelectorAll('#cpg .cpe').forEach(b=>{b.hidden=!!v&&!b.dataset.n.includes(v);});});
// bot lane duos (panel, ADCs and supports): the champion's 10 most played partners from OP.GG, each against the champion's
// own win rate, pulled toward it by sample size (update.py); grey when the gap could be luck. Links to the partner's page.
function duoHTML(d){const D=d.duo;if(!D||!D.l||!D.l.length||ARCH)return '';const pr=role==='adc'?'support':'adc',pn=role==='adc'?'supports':'ADCs';
  const card=([c,wr,n,cl])=>`<a class="cc${cl&&wr>D.o?' good':''}" href="${SITE}${pr}/${slug(c)}/" title="${d.c} with ${c}: ${wr.toFixed(1)}% win in ${n.toLocaleString('en-US')} games${cl?'':', too few to be sure it differs'}">${pic(c,'pic xs')}<span>${c}</span><small${cl?'':' class="lowdemo"'}>${wr.toFixed(0)}% · ${kfmt(n)} games</small></a>`;
  const grid=L=>`<div class="ctr">${L.map(card).join('')}</div>`;
  return `<div class="caph"><p class="cap">Best ${pn} with ${d.c} <span class="mu">OP.GG Emerald+, vs ${d.c}'s usual ${D.o.toFixed(1)}%</span></p></div>${grid(D.l.slice(0,3))}`
    +(D.l.length>3?`<details class="pmore sm-d"><summary>All ${D.l.length} most played ${pn}</summary><div class="dc">${grid(D.l.slice(3))}</div></details>`:'');}
// the cards under the list: one role on role pages; every role on the homepage, plus its strongest picks
function renderSide(){if(!DATA[role])return;
  const ALL=PAGE==='home';
  if(ALL&&DATA===CUR&&CUR._meta.part)ensureFull().then(()=>{if(!CUR._meta.part)renderSide();});
  const RNm=Object.fromEntries(ROLES),items=ALL?ROLES.flatMap(([r])=>(DATA[r]||[]).map(d=>[r,d])):DATA[role].map(d=>[role,d]);
  const VN=VNM(),sx=d=>stat(d)||{},vv=d=>SV(d),rl=r=>ALL?RNm[r]+' · ':'',TRK={Z:0,S:1};
  const row=(r,d,sub,pill,cls)=>`<li><button type="button" class="irow" ${ALL?`data-jr="${r}" data-jc="${d.c}"`:`data-c="${d.c}"`}>${pic(d.c)}<span class="in"><b>${d.c}</b><small>${sub}</small></span><span class="pill ${cls}">${pill}</span></button></li>`;
  const none='<li class="none">None in this view.</li>';
  $('maph').textContent=(ALL?'All roles':RNm[role])+' this patch';
  $('insg').classList.toggle('all',ALL);$('xsc').hidden=!ALL;
  if(ALL){const st=items.filter(([r,d])=>TRK[tierOf(d)]!=null).sort((a,b)=>TRK[tierOf(a[1])]-TRK[tierOf(b[1])]||SV(b[1])-SV(a[1]));
    $('xs').innerHTML=st.map(([r,d])=>{const t=tierOf(d);return `<button type="button" class="xchip" data-jr="${r}" data-jc="${d.c}" style="--R:var(--R${r})" title="${d.c}, ${RNm[r]}: ${t} tier, ${fmt(SV(d))}"><span class="ri">${RICON[r]}</span>${pic(d.c)}<span class="xn">${d.c}</span><span class="tg sm" style="--T:var(--${t})">${t}</span><b>${fmt(SV(d))}</b></button>`;}).join('')||'<p class="mi0">No Z or S picks in this view.</p>';
    const mb=$('xmore');mb.dataset.n=st.length;mb.hidden=st.length<=(matchMedia('(max-width:640px)').matches?8:12);mb.textContent=$('xs').classList.contains('all')?'Show fewer':`Show all ${st.length}`;
    $('xsh').innerHTML=`Strongest picks <span class="vn">${VN}</span>`;}
  $('traps').innerHTML=items.filter(([r,d])=>vv(d)!=null&&(sx(d).pick||0)>=5&&vv(d)<=-.3).sort((a,b)=>vv(a[1])-vv(b[1])).slice(0,6).map(([r,d])=>row(r,d,`${rl(r)}${sx(d).pick.toFixed(1)}% pick · ${kfmt(sx(d).n)} games`,fmt(vv(d)),'neg')).join('')||none;
  // best bans: score x pick rate, adjusted for how often it is already banned. All roles: summed over every role the champion is above average in.
  let bans=[];
  if(!ALL)bans=items.filter(([r,d])=>vv(d)!=null&&vv(d)>0&&(sx(d).pick||0)>=1.5).map(([r,d])=>[r,d,vv(d)*sx(d).pick/(100-(sx(d).ban||0)),`${sx(d).pick.toFixed(1)}% pick · ${sx(d).ban==null?'?':sx(d).ban.toFixed(0)}% ban`]);
  else{const by=new Map();for(const [r,d] of items){const x=sx(d);if(vv(d)==null||x.pick==null)continue;if(!by.has(d.c))by.set(d.c,[]);by.get(d.c).push([r,d,x]);}
    for(const L of by.values()){const ban=L.reduce((m,x)=>x[2].pick>m[2].pick?x:m)[2].ban||0,pos=L.filter(x=>vv(x[1])>0).sort((a,b)=>vv(b[1])*b[2].pick-vv(a[1])*a[2].pick);if(!pos.length)continue;
      const sub=pos.length===1?`${RNm[pos[0][0]]} ${tierOf(pos[0][1])} · ${pos[0][2].pick.toFixed(1)}% pick · ${ban.toFixed(0)}% ban`:`${pos.slice(0,2).map(x=>RNm[x[0]]+' '+tierOf(x[1])).join(', ')} · ${ban.toFixed(0)}% ban`;
      bans.push([pos[0][0],pos[0][1],pos.reduce((t,x)=>t+vv(x[1])*x[2].pick,0)/(100-ban),sub]);}}
  $('bans').innerHTML=bans.sort((a,b)=>b[2]-a[2]).slice(0,6).map(([r,d,,sub])=>row(r,d,sub,fmt(vv(d)),'pos')).join('')||none;
  $('bansh').innerHTML=`Best bans <span class="vn">${VN}</span>`;$('trapsh').innerHTML=`Popular, but losing <span class="vn">${VN}</span>`;
  const mv=Object.values(items.filter(([r,d])=>d.tr!=null&&d.pick>=1&&Math.abs(d.tr)>=.4&&!chance(d)).reduce((o,x)=>{const k=x[1].c;if(!o[k]||Math.abs(x[1].tr)>Math.abs(o[k][1].tr))o[k]=x;return o;},{})).sort((a,b)=>b[1].tr-a[1].tr);
  $('movers').innerHTML=[...mv.filter(x=>x[1].tr>0).slice(0,3),...mv.filter(x=>x[1].tr<0).slice(-3)].map(([r,d])=>row(r,d,`${rl(r)}${chLine(d)||itLine(d)||(s=>s&&s[0].toUpperCase()+s.slice(1))(pkShift(d))||(chance(d)?'Too small to be sure':`now ${d.t} in Emerald+ · ${fmt(d.score)}`)}`,`${d.tr>0?'↑':'↓'} ${fmt(d.tr)}`,d.tr>0?'pos':'neg')).join('')+(mv.length&&mv.length<4?`<li class="none">Everyone else moved too little since ${META.prev_patch} to be sure it isn't luck.</li>`:'')||'<li class="none">No big moves this patch.</li>';
  $('movh').textContent=`Moved most since ${META.prev_patch}`;
  $('movc').hidden=!!ARCH;
  // all roles: skip entries whose champions are already listed (the same change shows up in several roles), show the first six
  const seen=new Set(),nx=(ALL?ROLES.map(([r])=>r):[role]).flatMap(r=>(NEXT[r]||[]).map(x=>[r,...x])).filter(([r,c])=>{const ns=c.split(',').map(x=>x.trim());if(ns.every(n=>seen.has(n)))return false;ns.forEach(n=>seen.add(n));return true;});
  const NXL=ALL?6:99;
  $('next').innerHTML=nx.map(([r,c,t,kd],i)=>{const names=c.split(',').map(x=>x.trim()),one=names.length===1&&(DATA[r]||[]).some(d=>d.c===names[0]);
    const icon=names.length>1?`<span class="pstack">${names.slice(0,3).map(n=>pic(n)).join('')}</span>`:`<span class="pw">${names[0] in (META.nitems||{})?(META.nitems[names[0]]?`<img class="pic" src="${SITE}img/item/${META.nitems[names[0]]}.webp" alt="" width="64" height="64" loading="lazy" onerror="this.remove()">`:''):pic(names[0])}</span>`;
    const inner=`${icon}<span class="in"><b>${c}</b><small>${ALL&&one?RNm[r]+': ':''}${t}</small></span><span class="pill ${kd==='buff'?'pos':'neg'}">${kd}</span>`;
    return `<li${i>=NXL?' class="xtra"':''}>${one?`<button type="button" class="irow" ${ALL?`data-jr="${r}" data-jc="${names[0]}"`:`data-c="${names[0]}"`}>${inner}</button>`:`<div class="irow">${inner}</div>`}</li>`;}).join('');
  const nb=$('nxmore');nb.dataset.n=nx.length;nb.hidden=nx.length<=NXL;nb.textContent=$('next').classList.contains('all')?'Show fewer':`Show all ${nx.length}`;
  $('nextcap').innerHTML=`Patch ${META.next.patch} on ${META.next.date}, from the ${(META.notes||{})[META.next.patch]?`<a href="${SITE}patch/${META.next.patch}/">patch preview</a>`:'patch preview'}.`;
  $('nextc').hidden=!!ARCH||!nx.length;
}
// chart layout: pick rate (x, log) against score (y) for the chosen rank and region
function renderChart(){if(!$('sv'))$('board').innerHTML=`<div class="card chart-card"><div class="chart-h"><b>Pick rate vs strength</b><span>Right = picked more, up = wins more. Bottom right are the traps. Tap a portrait to open it.</span></div><div class="fig" id="fig"><svg id="sv" role="img" aria-label="Pick rate against score"></svg></div></div>`;drawMap();}
function drawMap(){if(!DATA[role]||!$('sv'))return;
  const s=$('sv'),W=s.clientWidth,H=s.clientHeight;if(!W)return;
  const P=d=>(stat(d)||{}).pick,Y=d=>SV(d);
  const list=DATA[role].filter(d=>Y(d)!=null&&P(d)>0);
  const m={l:58,r:24,t:40,b:42},small=W<520;
  const x=p=>m.l+(Math.log(Math.max(.4,Math.min(26,p)))-Math.log(.4))/(Math.log(26)-Math.log(.4))*(W-m.l-m.r);
  const ymin=-4.6,ymax=4.2,y=v=>m.t+(ymax-Math.max(ymin,Math.min(ymax,v)))/(ymax-ymin)*(H-m.t-m.b);
  let g='';
  g+=`<rect x="${x(5)}" y="${y(0)}" width="${W-m.r-x(5)}" height="${y(ymin)-y(0)}" fill="var(--neg)" opacity=".07"/>`;
  g+=`<rect x="${x(5)}" y="${y(ymax)}" width="${W-m.r-x(5)}" height="${y(0)-y(ymax)}" fill="var(--pos)" opacity=".07"/>`;
  [-4,-2,0,2].forEach(v=>{g+=`<line x1="${m.l}" x2="${W-m.r}" y1="${y(v)}" y2="${y(v)}" stroke="var(--line)" ${v===0?'stroke-width="1.5" stroke="var(--mut)"':''}/><text class="ax" x="${m.l-8}" y="${y(v)+4}" text-anchor="end">${v>0?'+':''}${v}</text>`;});
  (small?[1,5,20]:[.5,1,2,5,10,20]).forEach(p=>{g+=`<line x1="${x(p)}" x2="${x(p)}" y1="${m.t}" y2="${H-m.b}" stroke="var(--line)" ${p===5?'stroke-dasharray="4 4" stroke="var(--mut)"':''}/><text class="ax" x="${x(p)}" y="${H-m.b+18}" text-anchor="middle">${p}%</text>`;});
  g+=`<text class="ax" x="${W-m.r}" y="${H-6}" text-anchor="end">Pick rate, ${DSRC()} (log scale)</text>`;
  g+=`<text class="ax" transform="translate(14 ${(m.t+H-m.b)/2}) rotate(-90)" text-anchor="middle">Score, ${VNM()}</text>`;
  g+=`<text class="q" x="${W-m.r}" y="${m.t-14}" text-anchor="end">↗ Strong and popular</text>`;
  g+=`<text class="q" x="${W-m.r}" y="${y(ymin)-8}" text-anchor="end">↘ Popular, losing</text>`;
  g+=`<text class="q" x="${m.l}" y="${m.t-14}">↖ Strong, rarely picked</text>`;
  // labels: every name that fits next to its portrait (right, left, above, below) without covering another label or portrait
  const boxes=[],lab={},RR0=small?9:12;
  const pri=list.slice().sort((a,b)=>(b.c===pick)-(a.c===pick)||Math.abs(Y(b))*Math.sqrt(P(b))-Math.abs(Y(a))*Math.sqrt(P(a)));
  const lim=small?12:999;
  pri.forEach(d=>{if(q&&!hit(d.c))return;if(d.c!==pick&&Object.keys(lab).length>=lim)return;
    const cx=x(P(d)),cy=y(Y(d)),w=d.c.length*6.6+4,r=(d.c===pick?RR0+5:RR0)+5;
    for(const [bx,by,side] of [[cx+r,cy-8,'r'],[cx-r-w,cy-8,'l'],[cx-w/2,cy-r-15,'t'],[cx-w/2,cy+r-1,'b']]){
      if(bx<m.l-6||bx+w>W-m.r+6||by<m.t-6||by+16>H-m.b+4)continue;
      if(boxes.some(b=>bx<b[0]+b[2]&&bx+w>b[0]&&by<b[1]+16&&by+16>b[1]))continue;
      if(list.some(o=>{if(o===d)return false;const ox=x(P(o)),oy=y(Y(o));return ox+RR0>bx&&ox-RR0<bx+w&&oy+RR0>by+2&&oy-RR0<by+14;}))continue;
      boxes.push([bx,by,w]);lab[d.c]=[side,bx,by,w];break;}});
  const RR=small?9:12;
  g+=`<defs><clipPath id="cc" clipPathUnits="objectBoundingBox"><circle cx=".5" cy=".5" r=".5"/></clipPath></defs>`;
  list.slice().sort((a,b)=>(a.c===pick)-(b.c===pick)||P(a)-P(b)).forEach(d=>{const t=tierOf(d)||'E',cx=x(P(d)),cy=y(Y(d)),on=d.c===pick,r=on?RR+5:RR;
    g+=`<g class="dot${on?' on':''}${hit(d.c)?'':' dim'}" data-c="${d.c}" transform="translate(${cx.toFixed(1)} ${cy.toFixed(1)})"><title>${d.c} ${fmt(Y(d))}, ${P(d).toFixed(1)}% pick</title><circle r="${r+2.5}" fill="var(${on?'--acc':colT(t)})"/><image href="${IMGBASE}${slug(d.c)}.webp" x="${-r}" y="${-r}" width="${2*r}" height="${2*r}" clip-path="url(#cc)" preserveAspectRatio="xMidYMid slice"/></g>`;});
  list.filter(d=>lab[d.c]).forEach(d=>{const on=d.c===pick,[side,bx,by,w]=lab[d.c],tx=side==='r'?bx:side==='l'?bx+w:bx+w/2;g+=`<text x="${tx.toFixed(1)}" y="${(by+12).toFixed(1)}"${side==='l'?' text-anchor="end"':side==='r'?'':' text-anchor="middle"'} style="font-weight:${on?700:600}">${d.c}</text>`;});
  s.innerHTML=g;
}
function renderGrade(){
  const sx=v=>(Math.max(-.2,Math.min(1,v))+.2)/1.2*100;
  $('grade').innerHTML=`<div class="gr h"><span></span><span>Grades follow win rate</span><span>Grades follow popularity</span><span class="cv">Win rates vs OP.GG</span></div>`+GRADE.map(([n,w,p,c])=>{const bar=(v,col)=>`<div class="gb"><span class="z" style="left:${sx(0)}%"></span><i style="left:${v<0?sx(v):sx(0)}%;width:${Math.abs(sx(v)-sx(0))}%;background:var(${col})"></i>${(()=>{const e=Math.max(sx(v),sx(0));const s=(v<0?"−":"")+Math.abs(v).toFixed(2);return e>78?`<em class="in" style="right:${100-e}%">${s}</em>`:`<em style="left:${e}%">${s}</em>`})()}</div>`;return `<div class="gr"><b>${n}</b>${bar(w,'--pos')}${bar(p,'--faint')}<span class="cv" style="text-align:right;font-variant-numeric:tabular-nums">${c==null?'n/a':c.toFixed(2)}</span></div>`;}).join('');
}
function openPanel(o){$('panel').classList.toggle('open',o&&narrow());$('scrim').classList.toggle('open',o&&narrow());}
function render(){
  if(!DATA[role]){ensureFull().then(()=>{if(DATA[role])render();});return;}
  const list=DATA[role];
  if(!list.some(d=>d.c===pick&&tierOf(d)))pick=(list.find(d=>tierOf(d)==='Z')||list.find(d=>tierOf(d)==='S')||list[0]).c;
  renderControls();renderBoard();renderPanel();renderSide();drawMap();

}
function select(c,open){pick=c;try{history.replaceState(null,'',location.pathname+location.search+'#'+slug(c));}catch(e){}document.querySelectorAll('.chip').forEach(b=>b.setAttribute('aria-pressed',b.dataset.c===pick));document.querySelectorAll('.tv tbody tr').forEach(r=>r.classList.toggle('on',r.dataset.c===pick));renderPanel();drawMap();if(open)openPanel(true);}
function toggleGuide(o){const g=$('guide');o=o??g.hidden;g.hidden=!o;$('gbtn').setAttribute('aria-expanded',o);}
function setView(r,g){if(LIM())return;rank=r||rank;reg=g||reg;try{localStorage.setItem('tl-view',rank+'|'+reg);}catch(e){}if(sortK.startsWith('r_'))sortK='cur';flipRender(render);}
function search(){
  q=$('q').value.trim().toLowerCase();
  if(q&&!ARCH&&CUR._meta.part)ensureFull().then(()=>{if($('q').value.trim())search();});
  const out=[];if(q)for(const [r,n] of ROLES)for(const d of (DATA[r]||[]))if(hit(d.c))out.push([r,n,d]);
  out.sort((a,b)=>(starts(a[2].c)?0:1)-(starts(b[2].c)?0:1)||b[2].pick-a[2].pick);
  $('res').innerHTML=out.slice(0,8).map(([r,n,d])=>{const t=tierOf(d)||d.t;return `<button type="button" data-jr="${r}" data-jc="${d.c}"><span class="rc">${pic(d.c,'pic xs')}${d.c}<span class="rr">${n}</span></span><span class="tg" style="--T:var(${colT(t)})">${t}</span></button>`;}).join('')||(q?'<button type="button" disabled>No match</button>':'');
  $('res').style.display=q?'block':'none';
  renderBoard();
}
document.addEventListener('click',e=>{
  if(DOC)return;
  const t=e.target;
  const st=t.closest('[data-star]');if(st){toggleMine(st.dataset.star);return;}
  const sh=t.closest('[data-share]');if(sh){share(sh.dataset.share);return;}
  if(t.closest('#filt')){const b=$('bar'),o=!b.classList.contains('open');b.classList.toggle('open',o);$('filt').setAttribute('aria-expanded',o);return;}
  const pb=t.closest('[data-patch]');if(pb){setPatch(pb.dataset.patch);return;}
  const r=t.closest('[data-r]'),vr=t.closest('[data-rk],[data-rg]'),c=t.closest('[data-c]'),j=t.closest('[data-jr]');
  if(j){if(j.tagName==='A'){if(e.metaKey||e.ctrlKey||e.shiftKey||e.altKey)return;e.preventDefault();}$('q').value='';q='';$('res').style.display='none';navRole(j.dataset.jr,j.dataset.jc);openPanel(true);if(!narrow())$('board').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'});return;}
  if(r){navRole(r.dataset.r);return;}
  if(t.closest('[data-go]')){e.preventDefault();if(mode==='chart'||mode==='counter'){mode='tiers';renderControls();renderBoard();}$('board-sec').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});return;}
  if(t.closest('#gbtn')){toggleGuide();return;}
  {const ce=t.closest('[data-cpe]');if(ce){CPE=ce.dataset.cpe;CPall=false;renderCounter();const r_=$('cpres');if(r_)r_.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'nearest'});return;}}
  if(t.closest('#cpmore')){CPall=!CPall;renderCounter();return;}
  {const cg=t.closest('[data-cpgo]');if(cg){CPE=cg.dataset.cpgo;CPall=false;mode='counter';renderControls();renderBoard();if(narrow())openPanel(false);$('board-sec').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});return;}}
  if(t.closest('#cpchange')){CPE='';renderCounter();return;}
  if(t.closest('#nxmore')){const x=$('next'),all=!x.classList.contains('all'),b=$('nxmore');x.classList.toggle('all',all);b.setAttribute('aria-expanded',all);b.textContent=all?'Show fewer':`Show all ${b.dataset.n}`;return;}
  if(t.closest('#xmore')){const x=$('xs'),all=!x.classList.contains('all');x.classList.toggle('all',all);$('xmore').setAttribute('aria-expanded',all);$('xmore').textContent=all?'Show fewer':`Show all ${$('xmore').dataset.n||x.children.length+3}`;return;}
  if(vr&&!vr.disabled){setView(vr.dataset.rk,vr.dataset.rg);return;}
  const md=t.closest('[data-mode]'),so=t.closest('[data-sort]');
  if(md){if(md.tagName==='A')e.preventDefault();mode=md.dataset.mode;try{if(mode==='tiers'||mode==='table')localStorage.setItem('tl-mode',mode);}catch(e2){}renderControls();renderBoard();if(md.tagName==='A')$('board-sec').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});return;}
  if(so){const c=so.dataset.sort;if(sortK===c)sortD=-sortD;else{sortK=c;sortD=c==='c'?1:-1;}renderBoard();return;}
  if(c){select(c.dataset.c,true);return;}
  if(t.id==='x'||t.id==='scrim'){openPanel(false);return;}
  if(t.id==='sincex'){$('since').hidden=true;return;}
  if(!t.closest('.search'))$('res').style.display='none';
  if(!t.closest('#bar'))toggleGuide(false);
});
document.addEventListener('keydown',e=>{if(DOC)return;if(e.key==='/'&&document.activeElement!==$('q')&&!/INPUT|SELECT|TEXTAREA/.test(document.activeElement.tagName)){e.preventDefault();$('q').focus();return;}if(e.key==='Escape'){openPanel(false);$('res').style.display='none';toggleGuide(false);}});
if(!DOC){$('patchsel').addEventListener('change',e=>setPatch(e.target.value));
$('q').addEventListener('input',search);
$('q').addEventListener('keydown',e=>{if(e.key==='Enter'){const b=$('res').querySelector('[data-jr]');if(b)b.click();}});}
async function loadPatches(){try{const r=await fetch(SITE+'data/patches.json',{cache:'no-cache'});const j=await r.json();
  $('patchsel').innerHTML=j.patches.map(p=>`<option value="${p.patch===META.patch?'':p.patch}">Patch ${p.patch}</option>`).join('');
  const want=new URLSearchParams(location.search).get('patch');if(want&&want!==META.patch)setPatch(want);}catch(e){}}
async function setPatch(p){
  if(!p||p===META.patch){DATA=CUR;ARCH=null;}else{try{const r=await fetch(SITE+'data/'+p+'.json');if(!r.ok)throw 0;DATA=await r.json();ARCH=DATA._meta;}catch(e){DATA=CUR;ARCH=null;}}
  $('patchsel').value=ARCH?ARCH.patch:'';
  const u=new URL(location.href);if(ARCH)u.searchParams.set('patch',ARCH.patch);else u.searchParams.delete('patch');try{history.replaceState(null,'',u);}catch(e){}
  document.body.classList.toggle('archived',!!ARCH);
  $('arch').hidden=!ARCH;
  if(ARCH)$('arch').innerHTML=`<span>You're looking at <b>patch ${ARCH.patch}</b>${ARCH.kind==='limited'?' (Global Emerald+ only, older patches keep less data)':''}.</span><button type="button" data-patch="">Back to ${META.patch}</button>`;
  if(!DATA[role].some(d=>d.c===pick))pick=null;
  render();
}
const isRole=h=>ROLES.some(([k])=>k===h);
const roleFromPath=()=>{const m=location.pathname.match(/\/(top|jungle|mid|adc|support)\/(?:[a-z0-9]+\/?)?$/);return m?m[1]:null;};
const champFromHash=()=>{const h=decodeURIComponent(location.hash.slice(1)).toLowerCase();const d=DATA[role].find(x=>slug(x.c)===h);return d?d.c:null;};
function navRole(r,champ){
  if(PAGE==='champ'){location.href=SITE+r+'/'+location.search+(champ?'#'+slug(champ):'');return;}
  role=r;pick=champ||null;
  if(PAGE==='home'){try{history.replaceState(null,'',SITE+location.search+'#'+(champ?slug(champ):r));}catch(e){}render();return;}
  const url=SITE+r+'/'+location.search+(champ?'#'+slug(champ):'');try{history.pushState(null,'',url);}catch(e){try{history.replaceState(null,'','#'+(champ?slug(champ):r));}catch(e2){}}render();}
function fromURL(){const h=location.hash.slice(1);role=roleFromPath()||(isRole(h)?h:null)||role;if(!DATA[role]){ensureFull().then(()=>{if(DATA[role])fromURL();});return;}
  let c=champFromHash();
  // homepage: a #champion link can belong to another role than the one remembered; look it up once every role is loaded
  if(!c&&PAGE==='home'&&h&&!isRole(h)){
    if(CUR._meta.part&&!ARCH){ensureFull().then(()=>{if(!CUR._meta.part)fromURL();else render();});return;}
    const want=decodeURIComponent(h).toLowerCase(),r=ROLES.map(([k])=>k).find(k=>(DATA[k]||[]).some(x=>slug(x.c)===want));if(r){role=r;c=champFromHash();}}
  pick=c||(PAGE==='champ'&&INIT_CHAMP?INIT_CHAMP:pick);
  render();}
addEventListener('popstate',fromURL);
addEventListener('hashchange',()=>{const h=location.hash.slice(1);if(isRole(h)){navRole(h);return;}const c=champFromHash();if(c&&c!==pick)select(c,false);});
$('theme').addEventListener('click',()=>{const r=document.documentElement;const dark=r.dataset.theme?r.dataset.theme==='dark':matchMedia('(prefers-color-scheme: dark)').matches;const next=dark?'light':'dark';r.dataset.theme=next;try{localStorage.setItem('tl-theme',next);}catch(e){}const m=document.querySelector('meta[name=theme-color]');if(m)m.content=next==='dark'?'#0b0c0f':'#f5f6f8';});
// smooth open and close for expandable parts (details.sm-d, content in one .dc box); instant with reduced motion
document.addEventListener('click',e=>{const sm=e.target.closest('details.sm-d>summary');if(!sm)return;const d=sm.parentElement,c=d.querySelector(':scope>.dc');
  if(!c||matchMedia('(prefers-reduced-motion: reduce)').matches)return;e.preventDefault();if(d._a){d._a.cancel();d._a=null;}
  if(d.open&&!d.classList.contains('closing')){d.classList.add('closing');const h=c.offsetHeight;d._a=c.animate([{height:h+'px',opacity:1},{height:'0px',opacity:0}],{duration:200,easing:'cubic-bezier(.4,0,.2,1)'});d._a.onfinish=()=>{d.open=false;d.classList.remove('closing');d._a=null;};}
  else{d.classList.remove('closing');d.open=true;const h=c.offsetHeight;d._a=c.animate([{height:'0px',opacity:0},{height:h+'px',opacity:1}],{duration:260,easing:'cubic-bezier(.2,.7,.2,1)'});d._a.onfinish=()=>{d._a=null;};}});
if(PAGE==='patch'){
// patch notes page: mark the champions you starred on the tier list
const mine=[...document.querySelectorAll('.pn-ix[data-pc]')].filter(a=>MINE.some(m=>m===a.dataset.pc||m.endsWith('|'+a.dataset.pc)));
mine.forEach(a=>a.classList.add('mine'));
// the address bar always holds a link that previews right in chats: index entries open the change's own page, and
// in-page jumps (#champions, #items) scroll without adding #something to the address
document.addEventListener('click',e=>{const a=e.target.closest('a[href^="#"]');if(!a||e.ctrlKey||e.metaKey)return;const el=document.getElementById(a.getAttribute('href').slice(1));if(!el)return;e.preventDefault();el.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'});});
// a change's own page (/patch/<p>/<champion>/) opens at its card
if(INIT_CHAMP&&!location.hash){const el=document.getElementById(INIT_CHAMP);if(el){el.classList.add('pn-focus');requestAnimationFrame(()=>el.scrollIntoView({block:'start'}));}}
// "Copy link" on each card: the change's own page, so chats show that change. Phones get the share sheet.
document.addEventListener('click',e=>{const b=e.target.closest('.pn-share');if(!b)return;const u=b.dataset.u,lab=b.textContent,done=t=>{b.textContent=t;setTimeout(()=>b.textContent=lab,1600);};
  if(navigator.share&&matchMedia('(pointer:coarse)').matches){navigator.share({title:b.dataset.t,url:u}).catch(()=>{});return;}
  (navigator.clipboard?navigator.clipboard.writeText(u):Promise.reject()).then(()=>done('Copied'),()=>{b.title=u;done('Copy failed, link in tooltip');});});
if(mine.length){const el=$('pnmine');el.hidden=false;el.innerHTML='★ Your starred champions in this patch: '+mine.map(a=>`<a href="${a.getAttribute('href')}">${a.dataset.pc}</a>`).join(', ')+'.';}
}else if(PAGE==='method'){
$('sites').innerHTML=SITES.map(s=>`<tr><td data-l="Site"><b>${s[1]?`<a href="${s[1]}" rel="noopener">${s[0]}</a>`:s[0]}</b></td><td data-l="Home">${s[2]}</td><td data-l="Read">${s[3]}</td><td data-l="Verdict">${s[4]}</td></tr>`).join('');
{const b=META.backtest;$('btline').textContent=`Check: for the ${b.n} champion-role pairs that were not changed this patch, last patch's numbers line up with this patch's at r = ${b.r.toFixed(2)} (1 = perfect). Pulling toward zero made last patch a better guess (error ${b.mse_shrunk} vs ${b.mse_raw}).${b.cover!=null?` And the ± range: ${b.cover}% of them landed inside last patch's range. With nothing but luck moving them that would be about 90%, so the rest is real movement from item changes and the meta, which no ± can see coming.`:''}`;}
renderGrade();
}else{
new ResizeObserver(()=>{if(mode==='chart')drawMap();}).observe($('board'));
$('legend').innerHTML=`<span class="k" title="Win rate points above the role average"><b class="smp">+1.2</b>win rate vs role average</span><span class="k" title="Few games, so the score could be off"><b class="smp lowsc">+0.4</b>few games</span><span class="k" title="The score clearly moved since ${META.prev_patch}"><b class="smp"><b class="tri up">↑</b><b class="tri dn">↓</b></b>since ${META.prev_patch}</span>${META.next?`<span class="k" title="Buff or nerf coming in ${META.next.patch} (${META.next.date})"><span class="nxp buff"><svg viewBox="0 0 10 10" aria-hidden="true">${BDG.buff}</svg>${META.next.patch}</span>coming ${META.next.date}</span>`:''}<span class="k" title="Picked a lot, still losing"><span class="bdg trap"><svg viewBox="0 0 10 10" aria-hidden="true">${BDG.trap}</svg></span>trap</span>`;
{const bar=$('bar'),setH=()=>document.documentElement.style.setProperty('--barh',(getComputedStyle(bar).position==='sticky'?bar.offsetHeight:0)+'px');new ResizeObserver(()=>{setH();fitTable();$('q').placeholder=$('q').clientWidth<190?'Search':'Find a champion';}).observe(bar);setH();addEventListener('resize',fitTable);}
role=INIT_ROLE;
// the homepage always opens like a first visit (Top); #adc in the address picks a role. Drop the old remembered role.
try{localStorage.removeItem('tl-role');}catch(e){}
fromURL();
sinceVisit();
loadPatches();
setTimeout(()=>('requestIdleCallback' in window?requestIdleCallback:setTimeout)(()=>ensureFull()),1500);
}
}
