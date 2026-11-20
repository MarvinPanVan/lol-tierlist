// OP.GG collector for the LoL tier list. Runs inside a browser tab that is open on any op.gg page (built-in browser,
// javascript_tool): paste this whole file, then for example
//   await TLC.run('16.23', ['stats','prev'])             // 60 tier list pages + last patch's 15 Global pages (E+, D+, M+), ~3 min
//   await TLC.run('16.23', ['matchups','builds'])        // counters E+/D+ and build pages, ~35 min
//   await TLC.run('16.23', ['vs','runes','length','duos'])  // matchup builds, runes, trends and synergies pages, ~60 min
// Each run saves ONE file, lol-tierlist-<patch>-<parts>.json, through a download (a save window opens on Marvin's PC;
// he saves it to Downloads/lol-tierlist-data/). Then in the container: device_stage_files, and
//   python3 pipeline/collect/import_bundle.py <staged file> <length> <number sum>
// with the length and sum that run() returns, so a damaged or partial file is never used. Progress: TLC.status().
// Missed the save window? TLC.save() offers the last run's file again.
// Rules kept here: OP.GG's internal patch number (16.xx = 26.xx), 0.4 s between pages, never the visible tables.
(() => {
const ROLES = ['top', 'jungle', 'mid', 'adc', 'support'];
const EX = {'Wukong': 'monkeyking', 'Nunu & Willump': 'nunu', 'Renata Glasc': 'renata'};
const slug = n => EX[n] || n.toLowerCase().replace(/[^a-z0-9]/g, '');
const sleep = ms => new Promise(r => setTimeout(r, ms));
// OP.GG streams its page data in many <script>self.__next_f.push([1,"..."])</script> pieces that can split a record in
// the middle, so join them first, then undo the JSON escaping of quotes.
const fx = h => h.replace(/\\"/g, '"').replace(/"\]\)<\/script><script>self\.__next_f\.push\(\[1,"/g, '');
const get = async url => fx(await (await fetch(url)).text());
function bal(t, i) {   // the balanced [...] or {...} starting at i
  let d = 0, j = i, inS = false;
  for (; j < t.length; j++) { const ch = t[j];
    if (inS) { if (ch === '\\') { j++; continue; } if (ch === '"') inS = false; continue; }
    if (ch === '"') inS = true; else if (ch === '{' || ch === '[') d++; else if (ch === '}' || ch === ']') { d--; if (d === 0) break; } }
  return t.slice(i, j + 1);
}
function chunks(t) {   // resolves React references like "$L9a" to the chunk "9a:[...]"
  const memo = {};
  return id => { if (id in memo) return memo[id]; memo[id] = undefined;
    const m = new RegExp('(?:\\[1,"|\\\\n)' + id + ':').exec(t); if (!m) return undefined;
    const s = m.index + m[0].length; if (t[s] !== '[' && t[s] !== '{') return undefined;
    try { memo[id] = JSON.parse(bal(t, s)); } catch (e) {} return memo[id]; };
}
// tier list page: every champion of one role at one region and rank
function parseStats(t, pos) {
  const out = [], re = new RegExp('\\{"key":"[^"]+","name":"((?:[^"\\\\]|\\\\.)*)","image_url":"[^"]*","positionName":"' + pos + '","positionWinRate":([\\d.]+),"positionPickRate":([\\d.]+),"positionBanRate":([\\d.]+)', 'g');
  const seen = new Set(); let m;
  while ((m = re.exec(t))) { const name = JSON.parse('"' + m[1] + '"'); if (seen.has(name)) continue; seen.add(name);
    let [w, p, b] = [+m[2], +m[3], +m[4]]; if (w <= 1) { w *= 100; p *= 100; b *= 100; }
    out.push([name, w.toFixed(2), p.toFixed(2), b.toFixed(2)]); }
  const sm = t.replace(/<[^>]+>/g, ' ').match(/Total analyzed samples\D{0,40}([\d,]+)/);
  return {rows: out, samples: sm ? +sm[1].replace(/,/g, '') : null};
}
// counters page: every opponent with games and wins of this champion
function parseCtr(t) {
  const out = [], seen = new Set(), re = /\{"play":(\d+),"win":(\d+),"win_rate":[\d.]+,"champion":\{"image_url":"[^"]*","name":"((?:[^"\\]|\\.)*)"/g; let m;
  while ((m = re.exec(t))) { const nm = JSON.parse('"' + m[3] + '"'); if (seen.has(nm)) continue; seen.add(nm); out.push([nm, +m[1], +m[2]]); }
  return out;
}
// build page: spells, core items, boots, starting items (rows *_N), rune pages, skill order
function parseBuild(t) {
  const chunk = chunks(t);
  const findAlt = (n, d = 0) => { if (d > 40) return null;
    if (Array.isArray(n)) { for (const x of n) { const a = findAlt(x, d + 1); if (a) return a; } }
    else if (n && typeof n === 'object') { if (typeof n.alt === 'string') return n.alt; for (const k in n) { const a = findAlt(n[k], d + 1); if (a) return a; } }
    else if (typeof n === 'string') { const r = n.match(/^\$L?([0-9a-f]+)$/); if (r) { const c = chunk(r[1]); if (c !== undefined) return findAlt(c, d + 1); } }
    return null; };
  function walk(n, acc, d = 0) { if (d > 60) return;
    if (Array.isArray(n)) { if (n.includes('Games') && typeof n[0] === 'string' && /^[\d,]+$/.test(n[0])) acc.games = +n[0].replace(/,/g, ''); for (const x of n) walk(x, acc, d + 1); }
    else if (n && typeof n === 'object') { if (n.metaId != null && (n.metaType === 'item' || n.metaType === 'spell')) { acc.ids.push([n.metaId, findAlt(n)]); return; } for (const k in n) walk(n[k], acc, d + 1); }
    else if (typeof n === 'string') { const r = n.match(/^\$L?([0-9a-f]+)$/); if (r) { const c = chunk(r[1]); if (c !== undefined) walk(c, acc, d + 1); return; }
      const m = n.match(/^([\d.]+)%$/); if (m) acc.pct.push(+m[1]); } }
  function rows(key) { const out = [], seen = new Set(), re = new RegExp('"' + key + '_(\\d+)"', 'g'); let m;
    while ((m = re.exec(t))) { const n = +m[1]; if (seen.has(n)) continue; const s = t.lastIndexOf('["$"', m.index); if (s < 0) continue;
      let node; try { node = JSON.parse(bal(t, s)); } catch (e) { continue; } seen.add(n);
      const acc = {ids: [], pct: [], games: null}; walk(node, acc); out.push({ids: acc.ids.map(x => x[0]), names: acc.ids.map(x => x[1]), pick: acc.pct[0] ?? null, win: acc.pct[1] ?? null, games: acc.games}); }
    return out; }
  let runes = []; const di = t.indexOf('"data":{"rune_pages"');
  if (di >= 0) { try { runes = runePages(JSON.parse(bal(t, di + 7))); } catch (e) {} }
  // skill order: the row with the skill icons; max order from the icons, the 15 levels from the letter badges
  let skill = null, p = t.indexOf('"metaType":"skill"');
  if (p > 0) { const s = t.lastIndexOf('["$","tr"', p); try { const node = JSON.parse(bal(t, s)); const acc = {max: [], lv: [], pct: [], games: null};
    (function w(n, d) { if (d > 60) return;
      if (Array.isArray(n)) { if (n.includes('Games') && typeof n[0] === 'string' && /^[\d,]+$/.test(n[0])) acc.games = +n[0].replace(/,/g, ''); for (const x of n) w(x, d + 1); }
      else if (n && typeof n === 'object') { if (n.metaType === 'skill' && n.extraData) { acc.max.push(n.extraData); return; }
        if (n.translate === 'no' && typeof n.children === 'string' && /^[QWER]$/.test(n.children)) { acc.lv.push(n.children); return; } for (const k in n) w(n[k], d + 1); }
      else if (typeof n === 'string') { const r = n.match(/^\$L?([0-9a-f]+)$/); if (r) { const c = chunk(r[1]); if (c !== undefined) w(c, d + 1); return; }
        const m = n.match(/^([\d.]+)%$/); if (m) acc.pct.push(+m[1]); } })(node, 0);
    skill = [acc.max.join(''), acc.lv.join(''), acc.pct[0] ?? null, acc.pct[1] ?? null, acc.games]; } catch (e) {} }
  return {sp: rows('spells_table'), co: rows('core_items'), bo: rows('boots'), st: rows('starter_items'), rn: runes, skill};
}
// rune pages (build page: 2, runes page: up to 5) as [keystone, main tree, second tree, [3 runes], [2 runes], games, pick per mille, win per mille]
function runePages(R) {
  const act = a => (a || []).flat().filter(x => x && x.isActive).map(x => x.id);
  return (R.rune_pages || []).slice(0, 5).map(p => { const b = (p.builds || [])[0] || {};
    const wins = (p.builds || []).reduce((s, x) => s + (x.win || 0), 0), plays = (p.builds || []).reduce((s, x) => s + (x.play || 0), 0);
    const wr = p.win_rate != null ? p.win_rate : (plays ? wins / plays : null);
    return [p.id || (p.primary_rune && p.primary_rune.id), b.primary_perk_style && b.primary_perk_style.id, b.perk_sub_style && b.perk_sub_style.id,
            act(b.main_runes).slice(1), act(b.sub_runes), p.play, Math.round((p.pick_rate || 0) * 1000), wr == null ? null : Math.round(wr * 1000)]; });
}
function parseRunesPage(t) { const di = t.indexOf('"data":{"rune_pages"'); if (di < 0) return null; try { return runePages(JSON.parse(bal(t, di + 7))); } catch (e) { return null; } }
// trends page: win rate by game length, [[bucket start (0 = under 25), win %], ...]
function parseLen(t) { const i = t.indexOf('"xAxisKey":"game_length"'); if (i < 0) return null; const seg = t.slice(Math.max(0, i - 1500), i);
  const ds = seg.lastIndexOf('"data":['); return [...(ds < 0 ? seg : seg.slice(ds)).matchAll(/\{"game_length":(\d+),"rate":([\d.]+),"average":([\d.]+)/g)].map(m => [+m[1], +m[2]]); }
// synergies page: the 10 most played partners per other position, [position, partner, games, wins]
function parseSyn(t) { const out = [], seen = new Set(), re = /\{"play":(\d+),"synergy_position":"([A-Z]+)","win_rate":([\d.]+),"pick_rate":[\d.eE-]+,"synergy_champion_name":"((?:[^"\\]|\\.)*)"/g; let m;
  while ((m = re.exec(t))) { const nm = JSON.parse('"' + m[4] + '"'), k = m[2] + '|' + nm; if (seen.has(k)) continue; seen.add(k); out.push([m[2], nm, +m[1], Math.round(+m[3] * +m[1])]); }
  return out; }
// build page -> the stored build format (see CLAUDE.md): x10 for spells and items, per mille for runes
const x10 = v => v == null ? null : Math.round(v * 10);
const packBuild = b => [b.sp.map(r => [r.ids, x10(r.pick), x10(r.win)]), b.rn, b.co.map(r => [r.ids, x10(r.pick), x10(r.win), r.games]),
  b.bo.map(r => [r.ids[0], x10(r.pick), x10(r.win), r.games]), b.st.map(r => [r.ids, x10(r.pick), x10(r.win), r.games])];
const packVs = (b, n) => ({n, sp: b.sp.map(r => [r.ids, r.pick]), rn: b.rn.map(r => [r[0], r[6] / 10]), bo: b.bo.map(r => [r.ids[0], r.pick]), co: b.co.map(r => [r.ids, r.pick]), st: b.st.map(r => [r.ids, r.pick])});

const S = {part: null, done: 0, total: 0, errors: []};
async function each(list, fn) { S.total = list.length; S.done = 0; for (const x of list) { try { await fn(x); } catch (e) { S.errors.push(S.part + ' ' + JSON.stringify(x).slice(0, 80) + ': ' + e); } S.done++; await sleep(400); } }
async function run(patch, parts, prevPatch) {
  const q = (tier = 'emerald_plus', region = 'global') => `region=${region}&tier=${tier}&patch=${patch}`;
  const out = {patch, made: null, parts};
  let keys = null;   // "role|champion" for every champion listed in Global Emerald+
  const needKeys = async () => { if (keys) return keys; keys = [];
    for (const r of ROLES) { const s = parseStats(await get(`/lol/champions?${q()}&position=${r}`), r === 'adc' ? 'ADC' : r.toUpperCase()); s.rows.forEach(x => keys.push(r + '|' + x[0])); await sleep(400); }
    return keys; };
  if (parts.includes('stats')) { S.part = 'stats'; out.stats = {}; out.samples = {};
    const sets = [['global', 'emerald_plus', 'e'], ['euw', 'emerald_plus', 'e'], ['kr', 'emerald_plus', 'e'], ['na', 'emerald_plus', 'e'],
      ...['global', 'euw', 'kr', 'na'].flatMap(g => [[g, 'diamond_plus', 'd'], [g, 'master_plus', 'm']])];
    await each(sets.flatMap(([g, tier, k]) => ROLES.map(r => [g, tier, k, r])), async ([g, tier, k, r]) => {
      const s = parseStats(await get(`/lol/champions?${q(tier, g)}&position=${r}`), r === 'adc' ? 'ADC' : r.toUpperCase());
      out.stats[`opgg_${g}_${k}_${r}`] = s.rows; if (s.samples) out.samples[`opgg_${g}_${k}`] = s.samples; }); }
  if (parts.includes('prev')) {   // last patch's final Global numbers at Emerald+, Diamond+, Master+ (starting point, trend arrows, backtest); OP.GG keeps the previous patch
    const pv = prevPatch || patch.replace(/\d+$/, m => String(+m - 1).padStart(2, '0'));
    S.part = 'prev'; out.prev = {patch: pv, rows: {e: {}, d: {}, m: {}}, samples: {}};
    await each([['emerald_plus', 'e'], ['diamond_plus', 'd'], ['master_plus', 'm']].flatMap(([t, k]) => ROLES.map(r => [t, k, r])), async ([t, k, r]) => {
      const s = parseStats(await get(`/lol/champions?region=global&tier=${t}&patch=${pv}&position=${r}`), r === 'adc' ? 'ADC' : r.toUpperCase());
      out.prev.rows[k][r] = s.rows; if (s.samples) out.prev.samples[k] = s.samples; }); }
  if (parts.includes('matchups')) { await needKeys(); S.part = 'matchups'; out.counters = {e: {}, d: {}};
    for (const [tier, k] of [['emerald_plus', 'e'], ['diamond_plus', 'd']])
      await each(keys, async key => { const [r, c] = key.split('|'); out.counters[k][key] = parseCtr(await get(`/lol/champions/${slug(c)}/counters/${r}?${q(tier)}`)); }); }
  if (parts.includes('builds')) { await needKeys(); S.part = 'builds'; out.builds = {}; out.skills = {};
    await each(keys, async key => { const [r, c] = key.split('|'); const b = parseBuild(await get(`/lol/champions/${slug(c)}/build/${r}?${q()}`));
      out.builds[key] = packBuild(b); out.skills[key] = b.skill; }); }
  if (parts.includes('vs')) { await needKeys(); S.part = 'vs'; out.vs = {};
    if (!out.counters) throw new Error('vs needs the matchups part in the same run (it uses the 6 most played opponents)');
    const jobs = keys.flatMap(key => (out.counters.e[key] || []).slice().sort((a, b) => b[1] - a[1]).slice(0, 6).map(([o, n]) => [key, o, n]));
    await each(jobs, async ([key, o, n]) => { const [r, c] = key.split('|'); const b = parseBuild(await get(`/lol/champions/${slug(c)}/build/${r}?${q()}&target_champion=${slug(o)}`));
      (out.vs[key] = out.vs[key] || {})[o] = packVs(b, n); }); }
  if (parts.includes('runes')) { await needKeys(); S.part = 'runes'; out.rune_pages = {};
    await each(keys, async key => { const [r, c] = key.split('|'); const p = parseRunesPage(await get(`/lol/champions/${slug(c)}/runes/${r}?${q()}`)); if (p) out.rune_pages[key] = p; }); }
  if (parts.includes('length')) { await needKeys(); S.part = 'length'; out.game_length = {};
    await each(keys, async key => { const [r, c] = key.split('|'); const p = parseLen(await get(`/lol/champions/${slug(c)}/trends/${r}?${q()}`)); if (p && p.length) out.game_length[key] = p; }); }
  if (parts.includes('duos')) { await needKeys(); S.part = 'duos'; out.synergy = {};
    await each(keys.filter(k => k.startsWith('adc|') || k.startsWith('support|')), async key => { const [r, c] = key.split('|');
      const p = parseSyn(await get(`/lol/champions/${slug(c)}/synergies/${r}?${q()}`)); if (p.length) out.synergy[key] = p; }); }
  out.made = new Date().toISOString(); out.errors = S.errors.slice(); S.part = 'saving';
  const txt = JSON.stringify(out); let sum = 0; txt.replace(/-?\d+/g, x => { sum += +x; });
  const name = `lol-tierlist-${patch}-${parts.join('-')}.json`, a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([txt], {type: 'application/json'})); a.download = name; document.body.appendChild(a); a.click();
  S.part = 'saved'; window.TLC_last = {name, txt}; return {file: name, length: txt.length, sum, errors: S.errors.length};
}
function save() {   // offers the last run's file again (if the save window was closed or missed)
  const L = window.TLC_last; if (!L) return 'nothing to save'; const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([L.txt], {type: 'application/json'})); a.download = L.name; document.body.appendChild(a); a.click(); return L.name;
}
window.TLC = {run, save, status: () => ({...S, errors: S.errors.length}), parseStats, parseCtr, parseBuild, parseRunesPage, parseLen, parseSyn, packBuild, packVs, get};
})();
'TLC ready';
