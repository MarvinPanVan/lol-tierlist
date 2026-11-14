# LoL tier list: how to update this site

Marvin (high Diamond / low Master, EUW) asks for an update each new patch, usually just "update it".
Hosting: Cloudflare Pages, project `lol-tierlist`, connected to this repo. Build command: none. Output directory: `public`.
Every push to `main` goes live by itself within about a minute. Nothing for Marvin to click.

## Layout

- `public/index.html` + `public/fonts/` : the live site. Never hand-edit index.html, it is generated.
- `pipeline/template.html` : the page layout, CSS and JS. build.py ships the CSS and JS as shared cached files
  (`public/assets/app.<hash>.css/js`); each page only keeps a small inline config (`window.TL`).
  Look: dark by default (light only if the visitor picks it), gold accent, own position icons, tinted tier rows,
  Z/S as big art cards, A/B normal chips, C/D compact. Page headers are plain HTML made by build.py.
  Tier list CSS is one block near the end of the stylesheet ("the tier list, one system"): every tier row uses the same
  column grid (auto-fill, min 190px; phones 2 columns) so columns line up; Z/S cards span 2 columns with splash art.
  Change it there, not with new overrides elsewhere. The Chart layout is never remembered between visits (only Tiers and
  Table are), and the header "Tier list" link switches back from the chart.
- `pipeline/tiers.json` : the data for the current patch. Source of truth for what the site shows.
- `pipeline/assets/mark.svg` : the logo (tier-row icon), used for favicon, brand mark and og.png.
- `pipeline/build.py` : `python3 pipeline/build.py` builds every page from template + tiers.json: `public/index.html`,
  one page per role (`public/<role>/index.html`, own title, description and link preview), `public/method/` (site
  grades, method, sources), `404.html`, `robots.txt`, `sitemap.xml`, and the patch archive in `public/data/`.
  Template blocks: `<!--B-->` only on tier list pages, `<!--M-->` only on the method page, `<!--N-->` only on patch notes pages. Placeholders `__ROOT__`,
  `__PAGE__`, `__ROLE__`, `__TITLE__`, `__DESC__`, `__URL__`, `__OGIMG__`, `__PATCH__` are filled per page.
- Each page embeds only its own role plus a slim `_meta` (with `best` per role and `hist` = number of patches); the
  site fetches `data/<patch>.json` when you switch roles or search, and quietly after the first render.
- Share pages and link previews: chats never see the `#part` of a link, so every change has `/patch/<p>/<champion>/` and
  `/patch/<p>/i-<item>/` (noindex, own og title/text/picture, JS sends visitors to the card). "Copy link" on each card copies
  it (phones: share sheet). Pictures: build.py writes their HTML to `pipeline/.og_jobs.json`, assets.py renders only changed
  ones to `public/og/patch/` (hashes in `data/og_hashes.json`). Champion pages use their splash art as preview.
- Method page check: `backtest.cover` = % of unchanged champions whose value lands inside last patch's ± range (about 85-90%
  is healthy; far below means the ± is too narrow).
- Patch notes pages: `/patch/<patch>/` for every patch in `patch.json` `notes`, `/patch/` = the newest live one. Built by
  build.py (`notes_body`): a short version made from the data (counts, clear score moves since last patch, items with how
  many listed champions build them, starred champions via JS), a sticky index (buffs / nerfs / adjusted / items), then per
  champion: tier chips per role now (plus the change since last patch, grey = too small to be sure), "Riot says" (`why`: Riot's
  stated reason, short and in our own words), "So far" (live patch only: most played role, Global Emerald+ win and pick
  rate last patch → now from `wr0`/`pk0`, verdict from `trz`), "Means" (fixed rules in `meaning()`: which ranks change,
  only scaling, % health, base stats per level; or a hand-written `m` that only says what the numbers show), then the
  numbers grouped by ability (`ab` = ability names) with only the changed numbers marked (`_diff`, rank by rank).
  Items show who builds them (OP.GG core/boots/starter) and an icon from `public/img/item/<id>.webp` (icons workflow).
  No guessing about how a change plays out.
  Linked from the nav ("Patch notes"), the footer, the homepage data line, the next-patch card and every panel
  line about a change ("All numbers" → `/patch/<p>/#<champion>` or `#i-<item>`). CSS classes all start with `pn-`.
- `pipeline/privacy.html` : the privacy page (English + German), built to `public/privacy/`. Contact is Discord
  `marvinpanvan` only (Marvin's choice, no real name, no Impressum). If the site starts using anything new that
  touches visitors (another service, cookies, embeds), update this page.
- `public/data/history.json` : Global Emerald+ score per champion for the last 12 archived patches, written by
  build.py. The panel shows a small chart once 3 or more patches exist.
- Cloudflare Web Analytics is on for the Pages project (cookieless, injected by Cloudflare on deploy).
- Homepage: above the control bar is the patch story and stays fixed (Emerald+, all regions): a one-sentence data line,
  `headline`, `lede` and three art cards (the top three Z/S picks across roles, `strongest()` in build.py). Below the
  bar everything follows the visitor's rank and region: the list (Top by default), then "All roles this patch" with
  Strongest picks (every Z and S, P left out), Best bans across roles (per champion: score x pick summed over its roles
  with a positive score, divided by 100 - ban of its most-picked role), Popular but losing, Moved most and Changing next
  patch (deduplicated, first six with a "Show all" button). Role pages show the same cards for their role only (`renderSide` does both).
  Layouts: Tiers, Table and Chart (pick rate vs score; the nav link "Pick vs win" opens it). On desktop champion page
  headers hide the note and share button, because the card next to the list shows them.
  `/` always opens like a first visit (the logo leads there); `/#adc` opens ADC, `/#xayah` finds Xayah's role. Champion pages: `/mid/ahri/` for every listed champion (static header with art,
  tiers, note; the list loads below). They embed no data and load `data/<patch>.json`.
- Art: `public/img/tile/<slug>.webp` (square face crops) and `public/img/splash/<slug>.webp` (960x540), downloaded by
  the icons workflow (only missing files). In CSS custom properties use root paths (`/img/...`), because relative
  url() inside a CSS variable resolves against the stylesheet folder.
- URLs: `/mid/` is the mid page, `#katarina` selects a champion, `?patch=26.21` opens an archived patch. Old `/#mid`
  links still work.
- Patch archive: `public/data/<patch>.json` per patch and `patches.json` (newest 6). build.py always writes the
  current patch in full, so when a new patch comes in, the old file simply stays as the archive. Do not delete them.
  `pipeline/archive_limited.py <patch> <code>` makes a reduced Global-only archive from `data/prev/` (used for 26.21,
  because OP.GG only keeps the current and the previous patch).
- `pipeline/data`, `pipeline/data2` : raw numbers read from the stat sites for the current patch.
- `pipeline/update.py` : the whole method, raw files to tiers.json in one run (`python3 pipeline/update.py`).
  Prints a backtest (last patch vs this patch for unchanged champions), fitted spreads and the tiers.
- `pipeline/patch.json` : texts for the page headers (`updated`, `headline`, `lede` for the homepage, `takes` = two
  sentences per role, written by hand each patch from the numbers, Marvin's writing rules), patch numbers, previous patch code for the trend files, next patch preview per role
  (shown on the site and used for buff/nerf flags), `changes` = this patch's champion changes as
  {name: [buff|nerf|adjust, short line]} from Riot's notes, shown on the site, and `changed_this_patch` = the same names
  (no last-patch prior, excluded from the backtest). Summoner's Rift section only: the notes also have a "Classic"
  section (separate mode with old kits, e.g. 2011 Volibear) and ARAM changes. Those do not count (26.22 had 15 of them
  wrongly listed until 14 Nov).
  `notes` = {patch: {status live|preview, live (date), url, src, champs, items, other, none, skins, chromas}}. Each champion
  or item: {c, kind, short, (slot for items), (ab), (why), (m), lines: [[key, stat, old, new, tag, dir]]}. key Q/W/E/R/P/Base or "" for
  items; tag base (values per rank or low - high), cd, cost, ratio (scaling only), pct (% of target health), stats (base
  stats like "590 + 107/level"), mech (anything else, no rule applies); dir + better for the champion, - worse, ~ neither.
  Numbers copied exactly, text in our own short words. `changes` and `item_changes` must list the same names, kinds and
  short lines as `notes[patch]` (build.py stops with an error if not). Only Summoner's Rift, the client, ranked, map and
  new skins; never ARAM, Arena, Classic or other modes.
- `pipeline/data/samples.json` : OP.GG "Total analyzed samples" per dataset. It counts 10 per match, so
  games for a champion = pick% / 100 x samples / 10 (checked against U.GG game counts, they match).
- `pipeline/data/prev/` : last patch's OP.GG Global Emerald+ files, for the trend arrows and the backtest.

## Update procedure (each patch, every two weeks)

1. Find the patch number and the date of the next patch (official patch notes). Note big buffs/nerfs.
   Write the patch into `patch.json` `notes` with every number (status live), and the next patch from Riot Phroxzon's
   preview (status preview, numbers as far as the preview has them; strafe.com lists them as text). The old preview
   entry is replaced by the official notes once the patch is live.
2. Collect data for the new patch, ranked solo/duo. Save raw files in the same formats as now:
   - OP.GG champion stats, Emerald+: Global, EUW, KR, NA; plus Global Master+ and Global Diamond+.
     Always add `&patch=16.xx` (OP.GG's internal number, 16.22 = 26.22) or it serves an old patch.
     CSV: `champion,win,pick,ban` per role -> `data/opgg_{global,euw,kr,na}_e_{role}.csv`, `opgg_global_{m,d}_{role}.csv`.
   - U.GG tier list Diamond+ and Master+ (scroll the rendered table; do not hit their API directly).
     `data2/ugg_d.txt`, `ugg_m.txt`: `slug;role;tier;win;pick;ban;games`.
   - Blitz Diamond+ (`data2/blitz_d.txt`), dpm.lol Diamond+ (`dpm_d.txt`), Mobalytics high elo expert list (`moba_highelo.json`).
   - League of Graphs Diamond+ (`log_d.csv`) and METAsrc Diamond+ (`ms_d_{role}.txt`): open these in Claude in Chrome.
     The built-in browser gets stuck in a Cloudflare check on both. METAsrc drops `ranks=diamond+` on the first
     load, navigate twice. Chrome tool output is blocked when text contains "&", replace it with "and".
   - Lolalytics Emerald+ (runs about +1.6 points high on win rate, use only for shape) and lol.ps KR as cross-checks.
   - Reject optional cookies on every site. If a fetch gets blocked, use the browser, never work around a block.
   - Ask Marvin to be at his PC with the browser open if the cloud fetch cannot read a site.
3. Score: run `python3 pipeline/update.py`. Method (keep unless Marvin asks to change it):
   - Per dataset: win rate minus the pick-weighted role average.
   - Shrinkage: empirical Bayes per dataset and role. tau^2 = mean(delta^2) - mean(2500/n) over champions with
     n >= 300 (floor 0.35^2); shrunk = delta * tau^2 / (tau^2 + 2500/n).
   - One-trick penalty 0.4*ln(2/pick) when pick < 2%.
   - Views (Marvin chose this in 26.22): every list is one rank (Emerald+, Diamond+, Master+) x one region (All, EUW,
     KR, NA), 12 views, all scored the same way with the same tier rules. Site controls: Rank and Region buttons, the
     panel grid (tap a cell to switch), stored in localStorage `tl-view` as `rank|region`.
     - All regions = Global block .50, EUW .20, KR .20, NA .10, all at that rank, each shrunk. Global block: Emerald+ =
       OP.GG Global; Diamond+ = OP.GG, U.GG, Blitz, dpm.lol at 1 and League of Graphs at 0.5; Master+ = OP.GG and U.GG.
     - One region = that OP.GG dataset alone, shrunk. Pick rate for the one-trick penalty and Z/P = the view's OP.GG
       dataset (Global at that rank for All). ± = 1.64 x combined sd.
     - tiers.json: `e.v = {E, D, M, euw, kr, na, euwd, krd, nad, euwm, krm, nam: [score, ±, tier]}`; `score/se/t` =
       Emerald+ all regions (homepage, link previews, takes); `st` = games, pick, ban, win per OP.GG dataset.
   - Tiers, same rules for every view, no hand edits: Z score>=1.8, every dataset of the view >=1.5 raw, pick>=2;
     P pick<1.5 and >=.6; S>=1.15 and every dataset of the view above average; A>=.6; B>=.15; C>=-.45; else D.
   - Check after scoring: `python3 pipeline/scripts/verify_views.py` (independent recompute, must print 0 mismatches) and
     that the takes in patch.json still match the Emerald+ list and what they say about Diamond+/Master+.
   - Notes are written by update.py from the numbers. Change the wording rules there, not by hand.
   - Also collect OP.GG EUW, KR and NA Diamond+ and Master+ (`opgg_{euw,kr,na}_{d,m}_{role}.csv`), the previous patch
     Global Emerald+ (`data/prev/`), and the "Total analyzed samples" number for every OP.GG dataset into samples.json.
     Every one of these is a view of its own (see Views above).
   - OP.GG matchups (Global Emerald+ and Diamond+, every listed champion and role): fetch
     `/lol/champions/{key}/counters/{position}?region=global&tier=emerald_plus|diamond_plus&patch=16.xx` and regex the records
     `{"play":N,"win":W,"win_rate":..,"champion":{"image_url":..,"name":..}` (all opponents, 36-63 per champion). In the page,
     before ranking: per role, tau^2 = mean(delta^2 - 2500/n) over matchups with 300+ games (delta = matchup win rate minus the
     champion's own, in points); shrunk = delta * tau^2 / (tau^2 + 2500/n); keep the 5 lowest and 5 highest shrunk with 150+ games;
     clear = |delta| >= 1.64 * sqrt(2500/n). -> `data/opgg_matchups.json` {"e"|"d": {names, m: {"role|champ": {o: [games, wins],
     h|g: [[name index, games, wins, clear]]}}}}. Only ~29% (E+) / 23% (D+) of 150+ game matchups are clear; the rest is luck,
     which is why the raw lowest win rates are never used. The panel shows Diamond+ when the view is Diamond+ or Master+.
     `data/opgg_counters.json` (old positionCounters, 3 per champion) is only kept for archived patches.
   - OP.GG build stats (the build page, same fetch as builds below): spells_table_N, core_items_N, boots_N, starter_items_N
     rows plus `"data":{"rune_pages":[...]}`; RSC references (`$L9a`) are resolved by finding the chunk `9a:` and parsing it.
     IMPORTANT: OP.GG splits page data across `<script>self.__next_f.push([1,"...` tags, so first remove every
     `"])</script><script>self.__next_f.push([1,"` from the HTML, or chunks break mid-record. -> `data/opgg_build_stats.json`
     {"role|champ": [spells, rune pages, core builds, boots, starters]} (OP.GG's overview shows 2, 2, 3, 2, 2 of them;
     pick and win x10). Skill order: the row with `"metaType":"skill"` (max order in extraData, 15 level letters from the
     `translate:"no"` strong tags, pick, win, games) -> `data/opgg_skills.json`. update.py turns both into `bd` per champion.
     Build win rates are inflated (finishing items means you are ahead), so the card compares options with each other.
   - OP.GG matchup builds ("more vs" lines on the build card): for every champion and its 6 most played opponents fetch
     `/lol/champions/{key}/build/{position}?region=global&tier=emerald_plus&patch=16.xx&target_champion={opponent key}` and
     parse it like the build page -> `data/opgg_vs_builds.json` {"role|champ": {opponent: {n: games, sp, rn, bo, co, st:
     [[option, % of games]]}}}. update.py `switches()`: an option counts as "more vs X" when its share in that matchup is 10+
     points above its usual share and 3+ standard errors; if 2+ such opponents share a type (Riot's class tags, range > 325 =
     ranged, damage type from Data Dragon `info`, saved by the icons workflow in `ddragon_champions.json` "traits") that the
     other opponents mostly lack, the card names the type ("more vs ranged champions, like Teemo"). ~1,500 pages, ~60 min.
   - OP.GG runes page (`/lol/champions/{key}/runes/{position}?...`): up to 5 rune pages (the build page shows only 2) ->
     `data/opgg_rune_pages.json`, same format as the build page's rune pages (pick and win per mille).
   - OP.GG trends page (`/lol/champions/{key}/trends/{position}?...`): win rate by game length (under 25, 25-30, 30-35,
     35-40, 40+ minutes; the records `{"game_length":N,"rate":R,"average":50}` before `"xAxisKey":"game_length"`) ->
     `data/opgg_game_length.json`. OP.GG gives no game counts per bucket; update.py estimates them from the game lengths in
     our own Riot matches (`data/riot/matches_*.jsonl`) and only says "wins more in long/short games" when the gap between
     under 25 and 35+ is 2+ points and beyond that noise. League of Graphs and Lolalytics have similar curves but no counts.
   - OP.GG builds, for item changes: for every listed champion and role fetch (page JS, like below)
     `/lol/champions/{key}/build/{position}?region=global&tier=emerald_plus&patch=16.xx` (key: OP.GG slug, e.g.
     monkeyking, nunu, renata; position top/jungle/mid/adc/support). In the page data, rows keyed `core_items_N`,
     `boots_N`, `starter_items_N` hold `"metaType":"item","metaId":ID ... "alt":"Item name"`. Keep core_items_0/1 (first
     3 items), boots_0 and starter_items_0 -> `data/opgg_builds.json` {role: {champ: {c0, c1, b0, s0: [[id, name]]}}}.
     Pages are ~700 KB, so 248 of them take about 15 minutes; run it in the background and poll. In `patch.json`
     `item_changes` = {item: [buff|nerf|adjust, short line, core|starter]} from the notes' Summoner's Rift item section.
     The site names a changed item only when it is in a champion's core builds or boots, never starter items.
   - Getting data out of the browser: never copy it out of the page by reading it in pieces. The page saves ONE bundled
     JSON per collection run with a Blob download (`a.download='lol-tierlist-16.xx-<what>.json'`); a save window opens on
     Marvin's PC and he saves it to `Downloads/lol-tierlist-data/` (one click per file, so bundle everything of a run).
     Then `device_stage_files` copies it into the container; check length and number sum against the page before using it.
     The device shell does not run on his PC (virtualization is off in BIOS), so files there can't be moved or deleted.
   - Reading OP.GG: NEVER use the visible table. It stops at 55 rows ranked by OP.GG's own tier order, which silently
     drops losing champions (in 26.22 that hid K'Sante top, Jayce jungle and 9 others). Read the page data instead:
     open any op.gg champions page in the browser, then in page JS `fetch('/lol/champions?region=kr&tier=master_plus&
     position=top&patch=16.xx')`, take the HTML, replace `\\"` with `"` and regex the records
     `{"key":..,"name":..,"image_url":..,"positionName":"TOP","positionWinRate":..,"positionPickRate":..,"positionBanRate":..`
     (names are JSON-escaped, e.g. `Nunu \\u0026 Willump`; decode with JSON.parse). Each record also has
     `positionCounters` = three hardest matchups as {name, play, win}. "Total analyzed samples" is in the page text.
     Regions global/euw/kr/na, tiers emerald_plus/diamond_plus/master_plus, positions top/jungle/mid/adc/support,
     0.4 s between pages. Collecting all 65 pages takes about 2 minutes: run it, store in sessionStorage, read back.
     Check after collecting: pick rates per role add up to roughly 180-200% (two players per role per game) and the
     pick-weighted role average is about 50%.
4. Update the texts: in `patch.json` `updated`, `headline` (short, names the patch leaders, about 40 characters),
   `lede` (counts) and the five `takes`; the homepage leader cards are picked by build.py (Z tier, filled with the best S); in
   `pipeline/template.html` the top bar pill "Patch xx.xx", the NEXT list ("Changing on ..."), method and limits
   bullets that name champions, footer line, patch info links. Notes per champion live in tiers.json.
   Rewrite notes that no longer match the numbers.
   Writing rules from Marvin: blunt, no em dashes, must not sound AI-written, explain jargon.
5. `python3 pipeline/build.py`, then `python3 pipeline/scripts/assets.py` (favicon, apple-touch-icon, og.png and
   og-<role>.png link previews with portraits; it reads the patch from the top bar pill and the date from `updated` in patch.json). Then run `python3 pipeline/scripts/check_site.py` (serves public/ itself; JS errors and sideways scrolling at 390/1024/
   1440 in light and dark, broken links and images, meta, empty panels, the chart can be left, share pages redirect; must
   print "no problems"), and still look at screenshots yourself: desktop, dark mode, the mobile sheet.
6. Commit "Patch 26.xx" and push to main. Check https://lol-tierlist.pages.dev after a minute.
7. Mid-patch refresh around day 8 of each patch: same collection again (bigger samples), rerun, rebuild, push.
   Reminders for 26.23 are scheduled in Marvin's Claude session (20 Nov full update, 26 Nov refresh). After each
   refresh, schedule the next patch's two reminders.

## Riot API collector (prototype, development key)

- `.github/workflows/collect.yml` runs `pipeline/riot/collect.py` then `aggregate.py` on GitHub's servers and commits
  `pipeline/data/riot/matches_<region>_<version>.jsonl` and `agg_<version>.json` (champion win rates per role, lane
  matchups, ban rates). Trigger: change `pipeline/riot/run.txt` and push, or "Run workflow" on the Actions tab.
- The key lives only in the repo secret `RIOT_API_KEY`. Never copy or handle the key. A development key expires every
  24 hours: Marvin regenerates it on developer.riotgames.com (captcha) and pastes it into the secret himself.
- Stored per match: match id, version, duration, champion/position/team/win for the 10 players, banned champion ids.
  No player names or ids. Keep it that way.
- Not part of the scoring yet. Next: once the sample is big enough (and a production key is approved), add it as a
  dataset in update.py and use the matchups for counters. Production key: Marvin applied (Nov 2026), waiting for Riot; when approved it goes into the same secret.
- `pipeline/data/riot/agg_*.json` uses `pipeline/data/ddragon_champions.json` to name banned champions.

## Champion portraits

- `.github/workflows/icons.yml` runs `pipeline/scripts/icons.py`: downloads every champion portrait from Riot's Data
  Dragon, saves 64x64 webp to `public/img/champ/<slug>.webp` (slug = lowercase letters and digits of the name) and
  commits them. Re-run when a new champion comes out: change `pipeline/riot/icons.txt` and push.
- Images are served from the site itself, never hotlinked (same privacy reason as the fonts).
- Lolalytics best players per role (`data/lolalytics_best_<role>.csv`, top 20 per role) feed the "Rewards mastery" tag.

## Keep

- Footer must keep Riot's Legal Jibber Jabber notice. No ads and no Riot logos (fan project rules).
- Fonts are self-hosted on purpose (no Google Fonts requests from a German site).
