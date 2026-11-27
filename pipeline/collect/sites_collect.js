// Collector for the other stat sites (U.GG, Blitz, dpm.lol, League of Graphs). Paste this whole file into a tab that is
// open on the site (javascript_tool), then call the site's function. Each one reads the rendered page (never the site's
// API), and saves ONE file through a download, named lol-tierlist-<patch>-<what>, that import_sites.py understands:
//   U.GG     https://u.gg/lol/tier-list?rank=diamond_plus&region=world  -> await TLS.ugg('16.23')
//            then the same tab at ?rank=master_plus&region=world         -> await TLS.ugg('16.23')   (saves ugg.json with both)
//   Blitz    https://blitz.gg/lol/tierlist, viewport at least 1440 wide, pick Diamond+ in the rank menu by clicking
//            (the URL parameter alone is ignored)                         -> await TLS.blitz('16.23')  (blitz_d.txt)
//   dpm.lol  https://dpm.lol/tierlist (default Diamond+, all regions), viewport at least 1440 wide (narrower hides the
//            delta and games columns and every row is skipped)        -> await TLS.dpm('16.23')    (dpm_d.txt)
//   League of Graphs, in Claude in Chrome (the built-in browser gets stuck in its Cloudflare check):
//            https://www.leagueofgraphs.com/champions/tier-list/diamond  -> TLS.log('16.23')          (log_d-v2.csv)
//            An ad-blocker notice may cover the page; the table underneath is read anyway, leave the notice alone.
//            Chrome tool output is blocked when it contains & = ?, so keep returned text free of them.
// U.GG keeps the first rank in sessionStorage until the second one is read; the paste has to be repeated after the
// page changes rank, since navigation clears the functions. U.GG only draws rows in the FRONT tab (tabs_select first):
// in a background tab it read 15 of 265 rows. One tab per site, and never navigate a tab away before its file is in
// the folder: the save window needs the page that made the file ("Die Datei konnte nicht gespeichert werden").
// Each returns {file, length, sum, rows}; check length and sum against the staged file before importing.
// Missed the save window? TLS.save() offers the last file again.
// Lessons kept here: U.GG and dpm.lol only render the rows on screen, so they are read while scrolling (dpm in small
// steps, or rows get skipped); League of Graphs calls junglers "Jungler"; Blitz ignores ?tier= unless picked in the menu.
(() => {
const sleep = ms => new Promise(r => setTimeout(r, ms));
let last = null;
// A page may start only one download by itself; later ones are silently blocked. So each file also gets a gold button:
// a real click on it (Marvin's, or the computer tool's) always starts the download. Same as opgg_collect.js.
function offer(name, txt) {
  const go = () => { const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([txt], {type: 'text/plain'})); a.download = name;
    document.body.appendChild(a); a.click(); };
  const old = document.getElementById('tlc-save'); if (old) old.remove();
  const b = document.createElement('button'); b.id = 'tlc-save'; b.textContent = 'SAVE TIER LIST FILE: ' + name;
  b.style.cssText = 'position:fixed;top:80px;left:50%;transform:translateX(-50%);z-index:2147483647;padding:16px 24px;font:700 16px sans-serif;background:#e0b050;color:#000;border:0;border-radius:8px;cursor:pointer';
  b.onclick = () => { go(); b.textContent = 'Save window opened for ' + name + ' (click again if it did not)'; };
  document.body.appendChild(b); go();
}
function dl(name, txt, rows) {
  last = {name, txt}; offer(name, txt);
  let sum = 0; txt.replace(/-?\d+/g, x => { sum += +x; }); return {file: name, length: txt.length, sum, rows};
}
// scrolls the page (or a scroll box) to the end in small steps, calling grab() after each step
async function sweep(grab, step = 150, box = null) {
  const el = box || document.scrollingElement; el.scrollTop = 0; await sleep(600); grab();
  let stuck = 0;
  for (let i = 0; i < 2000 && stuck < 8; i++) {
    const before = el.scrollTop; el.scrollTop = before + step; await sleep(120); grab();
    stuck = el.scrollTop === before ? stuck + 1 : 0;
  }
  await sleep(500); grab();
}
const pc = s => (s || '').replace('%', '').trim();

async function ugg(patch) {   // slug;role;tier;win;pick;ban;games
  const rk = /master_plus/.test(location.search) ? 'm' : /diamond_plus/.test(location.search) ? 'd' : null;
  if (!rk) throw new Error('open the page with ?rank=diamond_plus or ?rank=master_plus');
  const rows = new Map();
  await sweep(() => document.querySelectorAll('.rt-tr-group').forEach(g => {
    const a = g.querySelector('a[href*="/lol/champions/"]'), img = g.querySelector('.role img'); if (!a || !img) return;
    const slug = a.getAttribute('href').split('/')[3], c = [...g.querySelectorAll('.rt-td')].map(x => x.innerText.trim());
    if (!/^\d/.test(c[4] || '') || !/\d/.test(c[8] || '')) return;
    rows.set(img.alt + '|' + slug, [slug, img.alt, c[3], pc(c[4]), pc(c[5]), pc(c[6]), c[8].replace(/,/g, '')].join(';'));
  }), 300);
  const by = {}; for (const [k, v] of rows) { const r = k.split('|')[0]; (by[`${rk}|${r}`] = by[`${rk}|${r}`] || []).push(v); }
  const store = JSON.parse(sessionStorage.getItem('tls-ugg') || '{}');
  for (const k in by) store[k] = by[k].join('\n');
  sessionStorage.setItem('tls-ugg', JSON.stringify(store));
  const have = ['d', 'm'].filter(x => Object.keys(store).some(k => k.startsWith(x + '|')));
  const counts = Object.fromEntries(Object.entries(store).map(([k, v]) => [k, v.split('\n').length]));
  if (have.length < 2) return {rank: rk, rows: rows.size, counts, next: rk === 'd' ? 'now open ?rank=master_plus&region=world and run again' : 'now open ?rank=diamond_plus&region=world and run again'};
  return dl(`lol-tierlist-${patch}-ugg.json`, JSON.stringify(store), counts);
}

async function blitz(patch) {   // lines "S=Name/role/win Name/role/win ..."
  const h = (document.querySelector('h1') || {}).innerText || '';   // "LoL Tier List ... Patch 26.23 for Diamond+"
  if (!/Diamond\+/.test(h)) throw new Error('page shows: ' + h + ' (pick Diamond+ in the rank menu first)');
  const out = {}; let n = 0;
  document.querySelectorAll('section.tier-list-row').forEach(sec => {
    const t = ((sec.firstElementChild && sec.firstElementChild.querySelector('img') || {}).alt || '').replace(/\s*Tier$/i, '').trim();
    if (!t) return;
    sec.querySelectorAll('a[href*="/lol/champions/"]').forEach(a => {
      const m = a.getAttribute('href').match(/\/lol\/champions\/([^/]+)\/build\/([a-z]+)/), w = (a.innerText.match(/([\d.]+)%/) || [])[1];
      if (!m || !w) return; (out[t] = out[t] || []).push(`${m[1]}/${m[2]}/${w}`); n++;
    });
  });
  const txt = Object.entries(out).map(([t, v]) => t + '=' + v.join(' ')).join('\n') + '\n';
  return dl(`lol-tierlist-${patch}-blitz_d.txt`, txt, n);
}

async function dpm(patch) {   // rank;Name|lane;lane%;tier;win;delta;pick;games
  const rows = new Map();
  const box = [...document.querySelectorAll('*')].find(e => e.scrollHeight > e.clientHeight + 200 && /auto|scroll/.test(getComputedStyle(e).overflowY) && e.querySelector('[data-index]')) || null;
  await sweep(() => document.querySelectorAll('[data-index]').forEach(r => {
    const a = r.querySelector('a[href*="lane="]'); if (!a) return;
    const lane = (a.getAttribute('href').match(/lane=([a-z]+)/) || [])[1], x = r.innerText.split('\n').map(s => s.trim()).filter(Boolean);
    if (!lane || x.length < 8) return;
    rows.set(x[0], [x[0].padStart(3, '0'), x[1] + '|' + lane, ...x.slice(2, 8)].join(';'));
  }), 150, box);
  const txt = [...rows.values()].sort().join('\n') + '\n';
  return dl(`lol-tierlist-${patch}-dpm_d.txt`, txt, rows.size);
}

function log(patch) {   // champion;role;tier;pop;win;ban with role T/J/M/B/S
  const R = {Top: 'T', Jungler: 'J', Jungle: 'J', Mid: 'M', Middle: 'M', Bottom: 'B', AD: 'B', ADC: 'B', Support: 'S'}, out = [], miss = [];
  document.querySelectorAll('table tr').forEach(tr => {
    const td = [...tr.querySelectorAll('td')]; if (td.length < 6) return;
    const words = td[1].innerText.trim().split(/\s+/), role = R[words[words.length - 1]];
    if (!role) { miss.push(td[1].innerText.trim()); return; }
    const name = words.slice(0, -1).join(' '), v = td.slice(2).map(x => x.innerText.trim());
    out.push([name, role, ...v.slice(0, 4).map(pc)].join(';'));
  });
  if (miss.length) return {error: 'unknown role words', miss: miss.slice(0, 10)};
  return dl(`lol-tierlist-${patch}-log_d-v2.csv`, 'champion,role,tier,pop,win,ban\n' + out.join('\n') + '\n', out.length);
}

function save() { if (!last) return 'nothing to save'; offer(last.name, last.txt); return last.name; }
window.TLS = {ugg, blitz, dpm, log, save, sweep};
})();
'TLS ready';
