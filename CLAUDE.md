# LoL tier list: how to update this site

Marvin (high Diamond / low Master, EUW) asks for an update each new patch, usually just "update it".
Hosting: Cloudflare Pages, project `lol-tierlist`, connected to this repo. Build command: none. Output directory: `public`.
Every push to `main` goes live by itself within about a minute. Nothing for Marvin to click.

## Layout

- `public/index.html` + `public/fonts/` : the live site. Never hand-edit index.html, it is generated.
- `pipeline/template.html` : the page (HTML, CSS, JS, all texts). Data goes in at `__DATA__`.
- `pipeline/tiers.json` : the data for the current patch. Source of truth for what the site shows.
- `pipeline/assets/mark.svg` : the logo (tier-row icon), used for favicon, brand mark and og.png.
- `pipeline/build.py` : `python3 pipeline/build.py` writes `public/index.html` from template + tiers.json.
- `pipeline/data`, `pipeline/data2` : raw numbers read from the stat sites for the current patch.
- `pipeline/update.py` : the whole method, raw files to tiers.json in one run (`python3 pipeline/update.py`).
  Prints a backtest (last patch vs this patch for unchanged champions), fitted spreads and the tiers.
- `pipeline/patch.json` : patch numbers, previous patch code for the trend files, next patch preview per role
  (shown on the site and used for buff/nerf flags), champions changed this patch (excluded from the backtest).
- `pipeline/data/samples.json` : OP.GG "Total analyzed samples" per dataset. It counts 10 per match, so
  games for a champion = pick% / 100 x samples / 10 (checked against U.GG game counts, they match).
- `pipeline/data/prev/` : last patch's OP.GG Global Emerald+ files, for the trend arrows and the backtest.

## Update procedure (each patch, every two weeks)

1. Find the patch number and the date of the next patch (official patch notes). Note big buffs/nerfs.
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
   - Consensus = Global .30, EUW .20, KR .20, Master+ .20 (OP.GG and U.GG), NA .10. ± = 1.64 x combined sd.
   - High elo = Diamond+ (OP.GG, U.GG, Blitz, dpm.lol at 1, League of Graphs at 0.5) 40%, Master+ (OP.GG, U.GG) 35%,
     EUW Diamond+ and Master+ 25%.
   - Tiers, same rules for both views, no hand edits: Z score>=1.8, every dataset >=1.5, pick>=2; P pick<1.5 and
     >=.6; S>=1.15 and above average in every region; A>=.6; B>=.15; C>=-.45; else D.
   - Notes are written by update.py from the numbers. Change the wording rules there, not by hand.
   - Also collect OP.GG EUW Diamond+ and Master+ (`opgg_euw_{d,m}_{role}.csv`), the previous patch Global Emerald+
     (`data/prev/`), and the "Total analyzed samples" number for every OP.GG dataset into samples.json.
4. Update the texts in `pipeline/template.html`: title and meta tags, top bar pill "Patch xx.xx", hero pills
   ("Updated ...", "Next patch ..."), headline, lede counts, the NEXT list ("Changing on ..."), method and limits
   bullets that name champions, footer line, patch info links. Notes per champion live in tiers.json.
   Rewrite notes that no longer match the numbers.
   Writing rules from Marvin: blunt, no em dashes, must not sound AI-written, explain jargon.
5. `python3 pipeline/build.py`, then `python3 pipeline/scripts/assets.py` (favicon, apple-touch-icon and the
   og.png link preview with the best pick per role; it reads the patch and date from the template pills). Then check with playwright (pipeline/scripts/shot3.py, ovf.py): no JS errors,
   no horizontal overflow at 390px, look at desktop, dark mode and the mobile sheet.
6. Commit "Patch 26.xx" and push to main. Check https://lol-tierlist.pages.dev after a minute.

## Keep

- Footer must keep Riot's Legal Jibber Jabber notice. No ads and no Riot logos (fan project rules).
- Fonts are self-hosted on purpose (no Google Fonts requests from a German site).
