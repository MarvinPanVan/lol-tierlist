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
const DS=[['g','Global'],['euw','EUW'],['kr','KR'],['na','NA'],['dia','Diamond+'],['m','Master+']];
const GRID=[['Global','g','dia','m'],['EUW','euw','euwd','euwm'],['KR','kr','krd','krm'],['NA','na','nad','nam']],RK=['Emerald+','Diamond+','Master+'];
const DSP=GRID.flatMap(([n,...ks])=>ks.map((k,i)=>[k,n+' '+RK[i]]));
const DSN=Object.fromEntries(DSP);
const META=CUR._meta;let ARCH=null;
// pages carry one role; the rest of the patch loads on demand (and quietly after the first render)
let FULLP=null;
function ensureFull(){if(!CUR._meta.part)return Promise.resolve();return FULLP||(FULLP=fetch(SITE+'data/'+META.patch+'.json').then(r=>{if(!r.ok)throw 0;return r.json();}).then(j=>{for(const [r] of ROLES)if(!CUR[r])CUR[r]=j[r];CUR._meta.part=false;}).catch(()=>{FULLP=null;}));}
const NEXT=META.next.roles;
const GRADE=META.grade;
const SITES=[
["OP.GG","https://op.gg/lol/champions","Korea","Global, EUW, KR, NA (Emerald+), Diamond+, Master+, EUW Diamond+ and Master+, last patch","Clean numbers and sample totals, the base of the consensus"],
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
let role='top',lens='score',pick=null,q='',mode='tiers',sortK='score',sortD=-1;
try{const s=localStorage.getItem('tl-mode');if(s)mode=s;}catch(e){}
try{const s=localStorage.getItem('tl-lens');if(s)lens=s;}catch(e){}
const keyOf=()=>lens;
const SK=()=>lens==='score'?'g':lens==='hi'?'dia':lens;
const stat=(d,k=SK())=>{const x=d.st&&d.st[k];return x?{n:x[0],pick:x[1],ban:x[2],wr:x[3]}:k==='g'?{n:d.games,pick:d.pick,ban:d.ban,wr:d.wr}:null;};
const LOWN=1500;
const isLow=d=>{if(lens==='score')return d.se>=.8;const x=stat(d);return !x||x.n<LOWN;};
function hiTier(d){return d.ht||null;}
function tierOf(d){
  if(lens==='score')return d.t;
  if(lens==='hi')return hiTier(d);
  const v=d[lens];if(v==null)return null;
  const pk=(stat(d)||d).pick;
  if(pk<1.5&&v>=.8)return 'P';
  if(v>=2.5&&pk>=2)return 'Z';
  return v>=1.5?'S':v>=.8?'A':v>=.2?'B':v>=-.5?'C':'D';
}
const slug=c=>c.toLowerCase().replace(/[^a-z0-9]/g,'');
const ALIAS={mf:'Miss Fortune',tf:'Twisted Fate',j4:'Jarvan IV',asol:'Aurelion Sol',ww:'Warwick',gp:'Gangplank',tk:'Tahm Kench',lb:'LeBlanc',ks:"K'Sante",xz:'Xin Zhao',yi:'Master Yi',mundo:'Dr. Mundo',morde:'Mordekaiser',nunu:'Nunu & Willump',renata:'Renata Glasc',kog:"Kog'Maw",kha:"Kha'Zix",cho:"Cho'Gath",vel:"Vel'Koz",bel:"Bel'Veth",rek:"Rek'Sai"};
const hit=c=>{if(!q)return true;const k=slug(q);return !k||slug(c).includes(k)||ALIAS[k]===c||c.toLowerCase().includes(q);};
const starts=c=>{const k=slug(q);return slug(c).startsWith(k)||ALIAS[k]===c;};
const pic=(c,cl='pic')=>`<img class="${cl}" src="${IMGBASE}${slug(c)}.webp" alt="" width="64" height="64" loading="lazy" decoding="async" onerror="this.remove()">`;
const LIM=()=>!!(ARCH&&ARCH.kind==='limited');
function tri(d){if(d.tr==null||Math.abs(d.tr)<.6)return '';const up=d.tr>0;return `<span class="tri ${up?'up':'dn'}" title="${up?'Up':'Down'} ${Math.abs(d.tr).toFixed(1)} since ${META.prev_patch}">${up?'↑':'↓'}</span>`;}
function ticks(d){if(LIM())return '';return DS.map(([k])=>{const v=d[k];if(v==null)return '<i></i>';const h=2+Math.min(Math.abs(v),3)/3*5;return `<i><b style="${v>=0?'bottom:7px':'top:8px'};height:${h.toFixed(1)}px;background:var(${v>=0?'--pos':'--neg'})"></b></i>`;}).join('');}
function renderControls(){if(!DATA[role])return;
  $('roles').innerHTML=ROLES.map(([k,n])=>`<button type="button" data-r="${k}" aria-pressed="${k===role}" aria-label="${n}">${RICON[k]}<span class="rl">${n}</span></button>`).join('');
  $('modes').innerHTML=[['tiers','Tiers'],['table','Table']].map(([k,n])=>`<button type="button" data-mode="${k}" aria-pressed="${k===mode}">${n}</button>`).join('');
  const lim=LIM(),nf=(lens!=='score')+(mode!=='tiers')+(!!ARCH)+(!!q);if($('filt'))$('filt').textContent=nf?`Filters (${nf})`:'Filters';
  $('views').innerHTML=[['score','Overall','Iron to Emerald'],['hi','High elo','Diamond and up']].map(([k,n,w])=>`<button type="button" class="two" data-l="${k}" aria-pressed="${k===lens}"${lim&&k==='hi'?' disabled title="Not available for this patch"':''}><span>${n}</span><small>${w}</small></button>`).join('');
  document.querySelectorAll('.gopt[data-l]').forEach(b=>{b.setAttribute('aria-pressed',b.dataset.l===lens);b.disabled=lim&&b.dataset.l==='hi';});
  $('ds').disabled=!!lim;
  $('ds').value=DSP.some(([k])=>k===lens)?lens:'';$('ds').classList.toggle('on',!!$('ds').value);
  const list=DATA[role],miss=list.filter(d=>tierOf(d)==null).length;
  $('hint').textContent=(lim?`Patch ${ARCH.patch}: Global Emerald+ only, same scoring and cutoffs.`:lens==='score'?'Overall, for Iron to Emerald. Blends Global, EUW, KR, NA and Master+.':lens==='hi'?'High elo, for Diamond and up. Diamond+ and Master+ games only, extra weight on EUW.':'Raw data: '+DSN[lens]+' only. Fewer games, so noisier.')+(miss?` ${miss} champions missing.`:'');
  $('legend').hidden=lim;
}
function renderTable(){if(!DATA[role])return;
  const list=DATA[role],k=keyOf();
  const lim=LIM(),cols=[['c','Champion'],['t','Tier'],[k,lens==='score'?'Score':lens==='hi'?'High elo':'Value'],...(lim||lens==='hi'?[]:[['hi','High elo']]),...(lim?[]:[['tr','Since '+META.prev_patch]]),['wr','Win %'],['pick','Pick %'],['ban','Ban %'],['games','Games'],...(lim?[]:[['ctr','Counters']])];
  const NA='<span class="mu">–</span>';
  const SC={wr:'wr',pick:'pick',ban:'ban',games:'n'};
  const val=(d,c)=>c==='t'?({Z:7,S:6,A:5,B:4,C:3,D:2,P:1}[tierOf(d)]||0):c==='c'?d.c:SC[c]?(stat(d)||{})[SC[c]]:d[c];
  const rows=list.filter(d=>tierOf(d)).slice().sort((a,b)=>{const x=val(a,sortK),y=val(b,sortK);if(typeof x==='string')return sortD*(x<y?-1:x>y?1:0);return sortD*((x??-999)-(y??-999));});
  const cell=(d,c)=>{const v=d[c];switch(c){case 'c':return `<td class="tc">${pic(d.c)}<b>${isMine(d.c)?'<span class="mst">★</span>':''}${d.c}</b>${d.nx?`<span class="flag ${d.nx}">${d.nx}</span>`:''}${d.mx!=null&&d.mx>=6?'<span class="flag mx" title="Its best players win far more than average">mastery</span>':''}</td>`;
    case 't':{const t=tierOf(d);return `<td><span class="tg" style="background:var(${colT(t)})">${t}</span></td>`;}
    case 'tr':return `<td class="n">${v==null?NA:Math.abs(v)<.05?'<span class="mu">0.0</span>':`<span style="color:var(${v>=0?'--pos':'--neg'})">${v>=0?'↑':'↓'} ${fmt(v)}</span>`}</td>`;
    case 'wr':case 'pick':case 'ban':{const w=val(d,c);return `<td class="n">${w==null?NA:w.toFixed(c==='ban'?0:1)}</td>`;}
    case 'ctr':{const cs=(HIGHV()?d.ctr_d:d.ctr)||d.ctr||[];return `<td><span class="ctrs">${cs.map(x=>`<img src="${IMGBASE}${slug(x)}.webp" alt="${x}" title="${x}" width="22" height="22" loading="lazy">`).join('')}</span></td>`;}
    case 'games':{const w=val(d,c);return `<td class="n${w!=null&&w<LOWN?' mu':''}">${w==null?NA:Math.round(w).toLocaleString('en-US')}</td>`;}
    case 'hi':return `<td class="n">${v==null?NA:`${fmt(v)} <span class="tg sm" style="background:var(${colT(d.ht)})">${d.ht||''}</span>`}</td>`;
    default:return `<td class="n"><b>${fmt(v)}</b>${c===k&&lens==='score'?` <span class="mu se">±${(d.se??0).toFixed(1)}</span>`:''}</td>`;}};
  $('board').innerHTML=`<div class="scroll tbl"><table class="tv"><thead><tr><th>#</th>${cols.map(([c,n])=>c==='ctr'?`<th><span class="thn">${n}</span></th>`:`<th><button type="button" data-sort="${c}" aria-sort="${sortK===c?(sortD<0?'descending':'ascending'):'none'}">${n}${sortK===c?(sortD<0?' ↓':' ↑'):''}</button></th>`).join('')}</tr></thead><tbody>${rows.map((d,i)=>`<tr data-c="${d.c}" class="${pick===d.c?'on':''}${hit(d.c)?'':' dim'}"><td class="n mu">${i+1}</td>${cols.map(([c])=>cell(d,c)).join('')}</tr>`).join('')}</tbody></table></div>`;
  fitTable();
}
function fitTable(){const t=document.querySelector('.tbl');if(!t)return;t.classList.remove('fit');if(!narrow()&&t.scrollWidth<=t.clientWidth+1)t.classList.add('fit');}
const LABT={Z:'Outlier: clearly ahead in every dataset with a real pick rate.',P:'Strong but rarely picked (under 1.5%). Mostly played by mains, so expect less if you are new to it.'};
let MINE=[];try{MINE=JSON.parse(localStorage.getItem('tl-mine')||'[]');}catch(e){}
const isMine=c=>MINE.includes(role+'|'+c)||MINE.includes(c);
function toggleMine(c){MINE=isMine(c)?MINE.filter(x=>x!==c&&x!==role+'|'+c):[...MINE,role+'|'+c];try{localStorage.setItem('tl-mine',JSON.stringify(MINE));}catch(e){}renderBoard();renderPanel();}
const isTrap=d=>{const x=stat(d),v=d[keyOf()];return !!x&&v!=null&&x.pick>=5&&v<=-.3;};
const kfmt=n=>n>=1e6?(n/1e6).toFixed(1)+'M':n>=1e4?Math.round(n/1e3)+'k':n>=1e3?(n/1e3).toFixed(1)+'k':String(Math.round(n));
const chipHTML=(d,k,tag,size='')=>{const low=isLow(d),x=stat(d),big=size==='big';return `<button type="button" class="chip${size?' '+size:''}${hit(d.c)?'':' dim'}${low?' low':''}" data-c="${d.c}" aria-pressed="${pick===d.c}"${big?` style="--art:url(${SITE}img/tile/${slug(d.c)}.webp)"`:''}${low?` title="${lens==='score'?`Few games, could be off by ±${d.se.toFixed(1)}`:`Only ${x?x.n.toLocaleString('en-US'):'a few'} games in ${DSN[SK()]}`}"`:''}>${pic(d.c)}<span class="nm">${!tag&&isMine(d.c)?'<span class="mst">★</span>':''}${d.c}${tag?`<span class="tg sm" style="background:var(${colT(tierOf(d))})">${tierOf(d)}</span>`:''}${(()=>{const tf=isTrap(d)?'<span class="flag trap" title="Picked a lot, still losing">trap</span>':'',nf=d.nx?`<span class="flag ${d.nx}">${d.nx}</span>`:'';return size==='sm'?(tf||nf):nf+tf;})()}</span><span class="sc">${tri(d)}<b>${fmt(d[k])}</b></span>${big&&x?`<span class="cm">${x.pick.toFixed(1)}% pick · ${kfmt(x.n)} games</span>`:''}</button>`;};
function poolHTML(mine){
  const best=mine[0],hiv=HIGHV(),cnt={};
  for(const d of mine)for(const c of ((hiv?d.ctr_d:d.ctr)||d.ctr||[]))if(!mine.some(m=>m.c===c))cnt[c]=(cnt[c]||0)+1;
  const bans=Object.entries(cnt).filter(([,n])=>n>=2).sort((a,b)=>b[1]-a[1]).slice(0,2);
  let t=mine.length>1?`Best of yours this patch: <b>${best.c}</b> (${tierOf(best)}, ${fmt(best[keyOf()])}).`:'';
  if(bans.length)t+=` Ban ${bans.map(([c,n])=>`<b>${c}</b>`).join(' or ')}: hard matchup for ${bans[0][1]} of your ${mine.length}.`;
  else if(mine.length===1){const cs=(hiv?best.ctr_d:best.ctr)||best.ctr;if(cs&&cs.length)t=`Hardest matchups for ${best.c}: ${cs.map(c=>`<b>${c}</b>`).join(', ')}.`;}
  return t?`<p class="mi">${t}</p>`:'';
}
function sinceVisit(){
  if(ARCH)return;if(!DATA[role]){ensureFull().then(()=>{if(DATA[role])sinceVisit();});return;}let seen=null;try{seen=JSON.parse(localStorage.getItem('tl-seen')||'null');}catch(e){}
  const list=DATA[role],rn=ROLES.find(r=>r[0]===role)[1],t=Object.assign({},seen&&seen.t||{});
  let html='';
  if(seen&&seen.p&&seen.p!==META.patch){
    const mv=list.filter(d=>d.tr!=null&&d.pick>=1&&Math.abs(d.tr)>=.4).sort((a,b)=>b.tr-a.tr);
    const up=mv.filter(d=>d.tr>0).slice(0,2),dn=mv.filter(d=>d.tr<0).slice(-2).reverse();
    const ch=list.filter(d=>isMine(d.c)&&t[role+'|'+d.c]&&t[role+'|'+d.c]!==d.t).map(d=>`<b>${d.c}</b> ${t[role+'|'+d.c]} → ${d.t}`);
    html=`<div class="since"><span><b>Patch ${META.patch} is in since your last visit.</b> ${rn}: ${[...up.map(d=>`<b>${d.c}</b> up ${fmt(d.tr)}`),...dn.map(d=>`<b>${d.c}</b> down ${fmt(d.tr)}`)].join(', ')||'no big moves'}.${ch.length?` Your champs: ${ch.join(', ')}.`:''}</span><button type="button" class="x2" id="sincex" aria-label="Close">×</button></div>`;
  }
  for(const d of list)if(isMine(d.c))t[role+'|'+d.c]=d.t;
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
  const list=DATA[role],k=keyOf();
  $('board').innerHTML=TIERS.map(([t,cap],ti)=>{
    const cs=list.filter(d=>tierOf(d)===t).sort((a,b)=>(b[k]??-99)-(a[k]??-99));
    if(!cs.length&&(t==='Z'||t==='P'))return '';
    const size=t==='Z'||t==='S'?'big':t==='C'||t==='D'?'sm':'';
    const body=cs.length?cs.map(d=>chipHTML(d,k,false,size)).join(''):'<span class="empty">None</span>';
    return `<div class="row" style="--T:var(${colT(t)})"><div class="lab"${LABT[t]?` title="${LABT[t]}"`:''}>${t}${cap?`<small>${cap}</small>`:''}</div><div class="chips${size==='big'?' bigs':size==='sm'?' smalls':''}">${body}</div></div>`;
  }).join('');
  const mine=list.filter(d=>isMine(d.c)&&tierOf(d)).sort((a,b)=>(b[k]??-99)-(a[k]??-99));
  if(mine.length)$('board').insertAdjacentHTML('afterbegin',`<div class="row mine-row" style="--T:var(--acc)"><div class="lab" title="Your champions, saved in this browser only">★<small>Yours</small></div><div class="chips">${mine.map(d=>chipHTML(d,k,true)).join('')}${poolHTML(mine)}</div></div>`);
}
const OPGG={wukong:'monkeyking',nunuwillump:'nunu',renataglasc:'renata'};
const opgg=(c,pg='build')=>`https://op.gg/lol/champions/${OPGG[slug(c)]||slug(c)}/${pg}/${role}`;
const HIGHV=()=>lens==='hi'||['dia','m','euwd','euwm','krd','krm','nad','nam'].includes(lens);
function renderPanel(){if(!DATA[role])return;
  const d=DATA[role].find(x=>x.c===pick);if(!d){$('panel').innerHTML='';return;}
  const rn=ROLES.find(r=>r[0]===role)[1],ht=hiTier(d),sx=stat(d)||{};
  const hcell=k=>{const v=d[k];if(v==null)return `<td class="na">–</td>`;const a=Math.min(Math.abs(v),3)/3;return `<td class="${lens===k?'on':''}" style="--h:color-mix(in srgb,var(${v>=0?'--pos':'--neg'}) ${Math.round(6+a*44)}%,transparent)"><button type="button" data-l="${k}" title="${DSN[k]}: ${d.st&&d.st[k]?d.st[k][0].toLocaleString('en-US')+' games. ':''}Tap to rank everyone by it." aria-label="${DSN[k]} ${fmt(v)}, show the tier list from this dataset">${fmt(v)}</button></td>`;};
  const grid=`<table class="hm"><thead><tr><th></th>${RK.map(r=>`<th>${r}</th>`).join('')}</tr></thead><tbody>${GRID.map(([n,...ks])=>`<tr><th>${n}</th>${ks.map(hcell).join('')}</tr>`).join('')}</tbody></table>`;
  const rows=DSP.map(([k,n])=>{const v=d[k];if(v==null)return '';const c=Math.max(-4,Math.min(4,v)),w=Math.abs(c)/4*50;return `<div class="r"><span>${n}</span><div class="trk"><div class="fill" style="left:${c<0?50-w:50}%;width:${w}%;background:var(${v<0?'--neg':'--pos'})"></div></div><span class="val">${fmt(v)}</span></div>`;}).join('');
  const sites=Object.entries(d.sites||{}).filter(([k,v])=>v).map(([k,v])=>`<span class="site">${k}<b style="background:var(${colT(v)})">${v}</b></span>`).join('')+(d.ll?`<span class="site">Lolalytics, Emerald+<b style="background:var(${colT(d.ll)})">${d.ll}</b></span>`:'');
  const tr=d.tr==null||ARCH?'':`<p class="trend">Since ${META.prev_patch} (Global): ${Math.abs(d.tr)<.05?'<b>no change</b>':`<b style="color:var(${d.tr>0?'--pos':'--neg'})">${d.tr>0?'↑':'↓'} ${fmt(d.tr)}</b>`}</p>`;
  const tt=t=>t?`<span class="tg sm" style="background:var(${colT(t)})">${t}</span>`:'';
  $('panel').innerHTML=`<div class="pin"><div class="pban" style="--art:url(${SITE}img/splash/${slug(d.c)}.webp)"></div><div class="ph">${pic(d.c,'pic big')}<div class="pht"><h3>${d.c}</h3><p class="rolesub">${rn} · ${sx.n!=null?sx.n.toLocaleString('en-US'):'No'} games in ${DSN[SK()]}${d.mx!=null&&d.mx>=6?' · <b class="mxb">Rewards mastery</b>':''}</p></div><button type="button" class="x" id="x" aria-label="Close">×</button></div>
  <div class="acts"><button type="button" class="star" data-star="${d.c}" aria-pressed="${isMine(d.c)}">${isMine(d.c)?'★ In my champs':'☆ Add to my champs'}</button><a class="ext" href="${opgg(d.c)}" target="_blank" rel="noopener">Build on OP.GG ↗</a><button type="button" class="ext" data-share="${d.c}">Share</button>${!ARCH&&PAGE!=='champ'?`<a class="ext" href="${champURL(d.c)}">Full page</a>`:''}</div>
  <div class="kv"><div data-tip="Win rate points above the role average, corrected for sample size and one-tricks. ± is a rough 90% range."><span><u>Overall</u>${tt(d.t)}</span><strong>${fmt(d.score)}<small> ±${d.se.toFixed(1)}</small></strong>${rngHTML(d)}</div>${d.hi!=null?`<div data-tip="Same score using only Diamond+ and Master+ games, with extra weight on EUW."><span><u>High elo</u>${tt(ht)}</span><strong>${fmt(d.hi)}</strong></div>`:''}<div><span>Pick</span><strong>${sx.pick==null?'–':sx.pick.toFixed(1)+'%'}</strong></div><div><span>Ban</span><strong>${sx.ban==null?'–':sx.ban.toFixed(0)+'%'}</strong></div></div>
  ${LIM()?`<p class="cap">Win rate vs role average, Global Emerald+ only</p><div class="rows">${rows}</div>`:`<p class="cap">Win rate vs role average in points, by region and rank. Tap a cell to rank everyone by it.</p>${grid}`}
  ${d.note?`<p class="note">${d.note}</p>`:''}
  ${tr}${histHTML(d)}${d.nx?`<p class="nx ${d.nx}">${META.next.patch}: ${d.nxt}.</p>`:''}
  ${ctrHTML(d)}
  ${sites?`<p class="cap">What other sites give it</p><div class="sites">${sites}</div>`:''}</div>`;
}
let HIST=null,HISTP=null;
function histHTML(d){
  if((META.hist||0)<3||ARCH)return '';
  if(!HIST){if(!HISTP)HISTP=fetch(SITE+'data/history.json').then(r=>r.json()).then(j=>{HIST=j;renderPanel();}).catch(()=>{});return '';}
  const v=(HIST.roles[role]||{})[d.c],P=HIST.patches;if(!v||v.filter(x=>x!=null).length<3)return '';
  const W=320,H=78,L=8,R=40,T=8,B=20,nn=v.filter(x=>x!=null),lo=Math.min(-1,...nn),hi=Math.max(1,...nn);
  const X=i=>L+i/(P.length-1)*(W-L-R),Y=x=>T+(hi-x)/(hi-lo)*(H-T-B);
  let path='';v.forEach((x,i)=>{if(x==null)return;path+=(path&&v[i-1]!=null?'L':'M')+X(i).toFixed(1)+' '+Y(x).toFixed(1);});
  const li=v.length-1-[...v].reverse().findIndex(x=>x!=null),fi=v.findIndex(x=>x!=null);
  return `<p class="cap">Global Emerald+ by patch</p><svg class="hist" viewBox="0 0 ${W} ${H}" role="img" aria-label="${d.c} by patch: ${v.map((x,i)=>P[i]+' '+(x==null?'no data':fmt(x))).join(', ')}">
  <line x1="${L}" x2="${W-R}" y1="${Y(0)}" y2="${Y(0)}" class="z"/>
  <path d="${path}" class="ln"/>${v.map((x,i)=>x==null?'':`<circle cx="${X(i)}" cy="${Y(x)}" r="${i===li?4:2.6}" class="${x>=0?'p':'n'}"><title>${P[i]}: ${fmt(x)}</title></circle>`).join('')}
  <text x="${X(li)+8}" y="${Y(v[li])+4}" class="lv">${fmt(v[li])}</text>
  <text x="${X(fi)}" y="${H-4}" class="pt">${P[fi]}</text><text x="${X(li)}" y="${H-4}" class="pt" text-anchor="end">${P[li]}</text></svg>`;
}
const cutT=v=>v>=1.15?'S':v>=.6?'A':v>=.15?'B':v>=-.45?'C':'D',TRANK={S:4,A:3,B:2,C:1,D:0};
function rngHTML(d){if(!'SABCD'.includes(d.t)||d.se==null)return '';const lo=cutT(d.score-d.se),hi=cutT(d.score+d.se);return lo===hi?'':`<small class="rng" title="With the ± range this champion could sit anywhere from ${lo} to ${hi}">could be ${lo===d.t?hi:hi===d.t?lo:lo+' to '+hi}</small>`;}
const champURL=c=>SITE+role+'/'+slug(c)+'/';
function share(c){const url=c?champURL(c):PAGE==='home'?SITE:SITE+role+'/',title=c?`${c} ${ROLES.find(r=>r[0]===role)[1]}, patch ${META.patch} | LoL Tier List`:document.title;
  if(navigator.share&&matchMedia('(pointer:coarse)').matches){navigator.share({title,url}).catch(()=>{});return;}
  const done=()=>{const t=document.createElement('div');t.className='toast';t.textContent='Link copied';document.body.appendChild(t);setTimeout(()=>t.remove(),1800);};
  (navigator.clipboard?navigator.clipboard.writeText(url):Promise.reject()).then(done).catch(()=>{prompt('Copy this link',url);});}
function ctrHTML(d){
  const hiv=HIGHV(),cs=(hiv?d.ctr_d:d.ctr)||d.ctr;if(!cs||!cs.length)return '';
  const inRole=c=>DATA[role].some(x=>x.c===c);
  return `<p class="cap">Hardest matchups <span class="mu">(OP.GG, ${hiv&&d.ctr_d?'Diamond+':'Emerald+'})</span></p><div class="ctr">${cs.map(c=>inRole(c)?`<button type="button" class="cc" data-c="${c}">${pic(c,'pic xs')}${c}</button>`:`<span class="cc">${pic(c,'pic xs')}${c}</span>`).join('')}<a class="ctrl" href="${opgg(d.c,'counters')}" target="_blank" rel="noopener">All matchups ↗</a></div>`;
}
function renderSide(){if(!DATA[role])return;
  const list=DATA[role];
  const k=keyOf(),VN=lens==='score'?'Overall':lens==='hi'?'High elo':DSN[lens];
  const sx=d=>stat(d)||{},vv=d=>d[k];
  $('traps').innerHTML=list.filter(d=>vv(d)!=null&&(sx(d).pick||0)>=5&&vv(d)<=-.3).sort((a,b)=>vv(a)-vv(b)).map(d=>`<li><button type="button" data-c="${d.c}">${pic(d.c,'pic xs')}${d.c}</button><span>${sx(d).pick.toFixed(1)}% pick, ${fmt(vv(d))}</span></li>`).join('')||'<li><span>None in this view</span><span></span></li>';
  $('bans').innerHTML=list.filter(d=>vv(d)!=null&&vv(d)>0&&(sx(d).pick||0)>=1.5).map(d=>[d,vv(d)*sx(d).pick/(100-(sx(d).ban||0))]).sort((a,b)=>b[1]-a[1]).slice(0,5).map(([d])=>`<li><button type="button" data-c="${d.c}">${pic(d.c,'pic xs')}${d.c}</button><span>${fmt(vv(d))}, ${sx(d).pick.toFixed(1)}% pick, ${sx(d).ban==null?'?':sx(d).ban.toFixed(0)}% ban</span></li>`).join('')||'<li><span>None in this view</span><span></span></li>';
  $('bansh').innerHTML=`Best bans <span class="vn">${VN}</span>`;$('trapsh').innerHTML=`Popular, but losing <span class="vn">${VN}</span>`;
  const mv=list.filter(d=>d.tr!=null&&d.pick>=1&&Math.abs(d.tr)>=.4).sort((a,b)=>b.tr-a.tr);
  const mrow=d=>`<li><button type="button" data-c="${d.c}">${pic(d.c,'pic xs')}${d.c}</button><span class="mv ${d.tr>0?'up':'dn'}">${d.tr>0?'↑':'↓'} ${fmt(d.tr)}</span></li>`;
  $('movers').innerHTML=[...mv.filter(d=>d.tr>0).slice(0,4),...mv.filter(d=>d.tr<0).slice(-4)].map(mrow).join('');
  $('movh').textContent=`Moved most since ${META.prev_patch}`;
  $('movc').hidden=!!ARCH||!mv.length;
  $('next').innerHTML=NEXT[role].map(([c,t,k])=>`<li><span>${c}</span><span style="color:var(${k==='buff'?'--pos':'--neg'})">${t}</span></li>`).join('');
}
function drawMap(){if(!DATA[role])return;
  const s=$('sv'),W=s.clientWidth,H=s.clientHeight;if(!W)return;
  const k=lens==='score'||DSP.some(([x])=>x===lens)?(lens==='score'?'score':lens):'hi';
  const P=d=>(stat(d)||d).pick;
  const list=DATA[role].filter(d=>d[k]!=null&&P(d)>0);
  const m={l:58,r:16,t:18,b:40},small=W<520;
  const x=p=>m.l+(Math.log(Math.max(.4,Math.min(26,p)))-Math.log(.4))/(Math.log(26)-Math.log(.4))*(W-m.l-m.r);
  const ymin=-4,ymax=3.5,y=v=>m.t+(ymax-Math.max(ymin,Math.min(ymax,v)))/(ymax-ymin)*(H-m.t-m.b);
  let g='';
  g+=`<rect x="${x(5)}" y="${y(0)}" width="${W-m.r-x(5)}" height="${y(ymin)-y(0)}" fill="var(--neg)" opacity=".07"/>`;
  g+=`<rect x="${x(5)}" y="${y(ymax)}" width="${W-m.r-x(5)}" height="${y(0)-y(ymax)}" fill="var(--pos)" opacity=".07"/>`;
  [-4,-2,0,2].forEach(v=>{g+=`<line x1="${m.l}" x2="${W-m.r}" y1="${y(v)}" y2="${y(v)}" stroke="var(--line)" ${v===0?'stroke-width="1.5" stroke="var(--mut)"':''}/><text class="ax" x="${m.l-8}" y="${y(v)+4}" text-anchor="end">${v>0?'+':''}${v}</text>`;});
  (small?[1,5,20]:[.5,1,2,5,10,20]).forEach(p=>{g+=`<line x1="${x(p)}" x2="${x(p)}" y1="${m.t}" y2="${H-m.b}" stroke="var(--line)" ${p===5?'stroke-dasharray="4 4" stroke="var(--mut)"':''}/><text class="ax" x="${x(p)}" y="${H-m.b+18}" text-anchor="middle">${p}%</text>`;});
  g+=`<text class="ax" x="${W-m.r}" y="${H-6}" text-anchor="end">Pick rate (log scale)</text>`;
  g+=`<text class="ax" transform="translate(14 ${(m.t+H-m.b)/2}) rotate(-90)" text-anchor="middle">Score vs role average</text>`;
  g+=`<text class="q" x="${W-m.r-8}" y="${y(ymax)+18}" text-anchor="end">Strong and popular</text>`;
  g+=`<text class="q" x="${W-m.r-8}" y="${y(0)+20}" text-anchor="end">Popular, losing</text>`;
  g+=`<text class="q" x="${m.l+8}" y="${y(ymax)+18}">Strong, rarely picked</text>`;
  const boxes=[],lab=[];
  const pri=list.slice().sort((a,b)=>(b.c===pick)-(a.c===pick)||Math.abs(b[k])*Math.sqrt(P(b))-Math.abs(a[k])*Math.sqrt(P(a)));
  pri.forEach((d,i)=>{const cx=x(P(d)),cy=y(d[k]);const w=d.c.length*7+6;const bx=cx+8,by=cy-8;
    if(cx+8+w>W-m.r)return;const lim=small?6:16;if(d.c!==pick&&lab.length>=lim)return;
    if(boxes.some(b=>bx<b[0]+b[2]&&bx+w>b[0]&&by<b[1]+16&&by+16>b[1]))return;boxes.push([bx,by,w]);lab.push(d.c);});
  list.forEach(d=>{const t=tierOf(d)||'E',cx=x(P(d)),cy=y(d[k]),on=d.c===pick;
    g+=`<circle cx="${cx}" cy="${cy}" r="${on?9:6}" fill="var(${colT(t)})" stroke="${on?'var(--ink)':'var(--card)'}" stroke-width="${on?2.5:1.5}" data-c="${d.c}"><title>${d.c} ${fmt(d[k])}, ${P(d).toFixed(1)}% pick</title></circle>`;});
  list.filter(d=>lab.includes(d.c)).forEach(d=>{g+=`<text x="${x(P(d))+10}" y="${y(d[k])+4}" style="font-weight:${d.c===pick?700:500}">${d.c}</text>`;});
  s.innerHTML=g;
}
function renderGrade(){
  const sx=v=>(Math.max(-.2,Math.min(1,v))+.2)/1.2*100;
  $('grade').innerHTML=`<div class="gr h"><span></span><span>Grades follow win rate</span><span>Grades follow popularity</span><span class="cv">Win rates vs OP.GG</span></div>`+GRADE.map(([n,w,p,c])=>{const bar=(v,col)=>`<div class="gb"><span class="z" style="left:${sx(0)}%"></span><i style="left:${v<0?sx(v):sx(0)}%;width:${Math.abs(sx(v)-sx(0))}%;background:var(${col})"></i>${(()=>{const e=Math.max(sx(v),sx(0));const s=(v<0?"−":"")+Math.abs(v).toFixed(2);return e>78?`<em class="in" style="right:${100-e}%">${s}</em>`:`<em style="left:${e}%">${s}</em>`})()}</div>`;return `<div class="gr"><b>${n}</b>${bar(w,'--pos')}${bar(p,'--A')}<span class="cv" style="text-align:right;font-variant-numeric:tabular-nums">${c==null?'n/a':c.toFixed(2)}</span></div>`;}).join('');
}
function renderBest(){if(!$('best'))return;
  const tr={Z:0,S:1,A:2,B:3,C:4,D:5,P:6};
  $('best').innerHTML='<h2>Best pick per role (Overall)</h2>'+ROLES.map(([r,n])=>{const b=META.best&&META.best[r];const d=b?{c:b[0],t:b[1],score:b[2]}:CUR[r].filter(x=>x.t!=='P').sort((a,b)=>(tr[a.t]-tr[b.t])||(b.score-a.score))[0];return `<button type="button" data-jr="${r}" data-jc="${d.c}"><span class="br">${n}</span><span class="bn">${pic(d.c,'pic sm')}${d.c}</span><span class="bs">${fmt(d.score)}</span><span class="tg" style="background:var(${colT(d.t)})">${d.t}</span></button>`;}).join('');
}
function openPanel(o){$('panel').classList.toggle('open',o&&narrow());$('scrim').classList.toggle('open',o&&narrow());}
function render(){
  if(!DATA[role]){ensureFull().then(()=>{if(DATA[role])render();});return;}
  const list=DATA[role];
  if(!list.some(d=>d.c===pick&&tierOf(d)))pick=(list.find(d=>tierOf(d)==='Z')||list.find(d=>tierOf(d)==='S')||list[0]).c;
  renderControls();renderBoard();renderPanel();renderSide();drawMap();
  $('nexth').textContent=`Changing on ${META.next.date} (${META.next.patch} preview)`;
  $('nextc').hidden=!!ARCH||!NEXT[role].length;
  $('maph').textContent=ROLES.find(r=>r[0]===role)[1]+': picked a lot is not the same as winning';
}
function select(c,open){pick=c;try{history.replaceState(null,'',location.pathname+location.search+'#'+slug(c));}catch(e){}document.querySelectorAll('.chip').forEach(b=>b.setAttribute('aria-pressed',b.dataset.c===pick));document.querySelectorAll('.tv tbody tr').forEach(r=>r.classList.toggle('on',r.dataset.c===pick));renderPanel();drawMap();if(open)openPanel(true);}
function toggleGuide(o){const g=$('guide');o=o??g.hidden;g.hidden=!o;$('gbtn').setAttribute('aria-expanded',o);}
let lastMain='score';
function setLens(l){if(l==='score'||l==='hi'){lastMain=l;try{localStorage.setItem('tl-lens',l);}catch(e){}}if(sortK===lens||sortK==='score'||sortK==='hi'||DSP.some(([x])=>x===sortK))sortK=l;lens=l;flipRender(render);}
function search(){
  q=$('q').value.trim().toLowerCase();
  if(q&&!ARCH&&CUR._meta.part)ensureFull().then(()=>{if($('q').value.trim())search();});
  const out=[];if(q)for(const [r,n] of ROLES)for(const d of (DATA[r]||[]))if(hit(d.c))out.push([r,n,d]);
  out.sort((a,b)=>(starts(a[2].c)?0:1)-(starts(b[2].c)?0:1)||b[2].pick-a[2].pick);
  $('res').innerHTML=out.slice(0,8).map(([r,n,d])=>{const t=tierOf(d)||d.t;return `<button type="button" data-jr="${r}" data-jc="${d.c}"><span class="rc">${pic(d.c,'pic xs')}${d.c}<span class="rr">${n}</span></span><span class="tg" style="background:var(${colT(t)})">${t}</span></button>`;}).join('')||(q?'<button type="button" disabled>No match</button>':'');
  $('res').style.display=q?'block':'none';
  renderBoard();
}
document.addEventListener('click',e=>{
  if(PAGE==='method')return;
  const t=e.target;
  const st=t.closest('[data-star]');if(st){toggleMine(st.dataset.star);return;}
  const sh=t.closest('[data-share]');if(sh){share(sh.dataset.share);return;}
  if(t.closest('#filt')){const b=$('bar'),o=!b.classList.contains('open');b.classList.toggle('open',o);$('filt').setAttribute('aria-expanded',o);return;}
  const pb=t.closest('[data-patch]');if(pb){setPatch(pb.dataset.patch);return;}
  const r=t.closest('[data-r]'),l=t.closest('[data-l]'),c=t.closest('[data-c]'),j=t.closest('[data-jr]');
  if(j){$('q').value='';q='';$('res').style.display='none';navRole(j.dataset.jr,j.dataset.jc);openPanel(true);if(!narrow())$('board').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'});return;}
  if(r){navRole(r.dataset.r);return;}
  if(t.closest('#gbtn')){toggleGuide();return;}
  if(l){setLens(l.dataset.l);if(l.closest('#guide'))toggleGuide(false);return;}
  const md=t.closest('[data-mode]'),so=t.closest('[data-sort]');
  if(md){mode=md.dataset.mode;try{localStorage.setItem('tl-mode',mode);}catch(e){}renderControls();renderBoard();return;}
  if(so){const c=so.dataset.sort;if(sortK===c)sortD=-sortD;else{sortK=c;sortD=c==='c'?1:-1;}renderBoard();return;}
  if(c){select(c.dataset.c,true);return;}
  if(t.id==='x'||t.id==='scrim'){openPanel(false);return;}
  if(t.id==='sincex'){$('since').hidden=true;return;}
  if(!t.closest('.search'))$('res').style.display='none';
  if(!t.closest('#bar'))toggleGuide(false);
});
document.addEventListener('keydown',e=>{if(PAGE==='method')return;if(e.key==='/'&&document.activeElement!==$('q')&&!/INPUT|SELECT|TEXTAREA/.test(document.activeElement.tagName)){e.preventDefault();$('q').focus();return;}if(e.key==='Escape'){openPanel(false);$('res').style.display='none';toggleGuide(false);}});
if(PAGE!=='method'){$('patchsel').addEventListener('change',e=>setPatch(e.target.value));$('ds').addEventListener('change',e=>setLens(e.target.value||lastMain));
$('q').addEventListener('input',search);
$('q').addEventListener('keydown',e=>{if(e.key==='Enter'){const b=$('res').querySelector('[data-jr]');if(b)b.click();}});}
async function loadPatches(){try{const r=await fetch(SITE+'data/patches.json',{cache:'no-cache'});const j=await r.json();
  $('patchsel').innerHTML=j.patches.map(p=>`<option value="${p.patch===META.patch?'':p.patch}">Patch ${p.patch}</option>`).join('');
  const want=new URLSearchParams(location.search).get('patch');if(want&&want!==META.patch)setPatch(want);}catch(e){}}
async function setPatch(p){
  if(!p||p===META.patch){DATA=CUR;ARCH=null;}else{try{const r=await fetch(SITE+'data/'+p+'.json');if(!r.ok)throw 0;DATA=await r.json();ARCH=DATA._meta;}catch(e){DATA=CUR;ARCH=null;}}
  $('patchsel').value=ARCH?ARCH.patch:'';
  if(ARCH&&ARCH.kind==='limited'&&lens!=='score')lens='score';
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
function navRole(r,champ){try{localStorage.setItem('tl-role',r);}catch(e){}
  if(PAGE==='champ'){location.href=SITE+r+'/'+location.search+(champ?'#'+slug(champ):'');return;}
  role=r;pick=champ||null;
  if(PAGE==='home'){try{history.replaceState(null,'',SITE+location.search+'#'+(champ?slug(champ):r));}catch(e){}render();return;}
  const url=SITE+r+'/'+location.search+(champ?'#'+slug(champ):'');try{history.pushState(null,'',url);}catch(e){try{history.replaceState(null,'','#'+(champ?slug(champ):r));}catch(e2){}}render();}
function fromURL(){const h=location.hash.slice(1);role=roleFromPath()||(isRole(h)?h:null)||role;if(!DATA[role]){ensureFull().then(()=>{if(DATA[role])fromURL();});return;}pick=champFromHash()||(PAGE==='champ'&&INIT_CHAMP?INIT_CHAMP:pick);if(PAGE!=='home')try{localStorage.setItem('tl-role',role);}catch(e){}render();}
addEventListener('popstate',fromURL);
addEventListener('hashchange',()=>{const h=location.hash.slice(1);if(isRole(h)){navRole(h);return;}const c=champFromHash();if(c&&c!==pick)select(c,false);});
$('theme').addEventListener('click',()=>{const r=document.documentElement;const dark=r.dataset.theme?r.dataset.theme==='dark':matchMedia('(prefers-color-scheme: dark)').matches;const next=dark?'light':'dark';r.dataset.theme=next;try{localStorage.setItem('tl-theme',next);}catch(e){}const m=document.querySelector('meta[name=theme-color]');if(m)m.content=next==='dark'?'#0b0c0f':'#f5f6f8';});
if(PAGE==='method'){
$('sites').innerHTML=SITES.map(s=>`<tr><td data-l="Site"><b>${s[1]?`<a href="${s[1]}" rel="noopener">${s[0]}</a>`:s[0]}</b></td><td data-l="Home">${s[2]}</td><td data-l="Read">${s[3]}</td><td data-l="Verdict">${s[4]}</td></tr>`).join('');
{const b=META.backtest;$('btline').textContent=`Check: for the ${b.n} champion-role pairs that were not changed this patch, last patch's numbers line up with this patch's at r = ${b.r.toFixed(2)} (1 = perfect). Pulling toward zero made last patch a better guess (error ${b.mse_shrunk} vs ${b.mse_raw}).`;}
renderGrade();
}else{
new ResizeObserver(()=>drawMap()).observe($('fig'));
$('legend').innerHTML=`<span><u class="lowdemo">Dotted</u> score = few games. <span class="flag trap">trap</span> = picked a lot, still losing.</span>`;
{const bar=$('bar'),setH=()=>document.documentElement.style.setProperty('--barh',(getComputedStyle(bar).position==='sticky'?bar.offsetHeight:0)+'px');new ResizeObserver(()=>{setH();fitTable();$('q').placeholder=$('q').clientWidth<190?'Search':'Find a champion';}).observe(bar);setH();addEventListener('resize',fitTable);}
renderBest();
if(!['score','hi'].includes(lens))lens='score';
role=INIT_ROLE;
if(PAGE==='home'){try{const r=localStorage.getItem('tl-role');if(r&&isRole(r))role=r;}catch(e){}}
fromURL();
sinceVisit();
loadPatches();
setTimeout(()=>('requestIdleCallback' in window?requestIdleCallback:setTimeout)(()=>ensureFull()),1500);
}
}
