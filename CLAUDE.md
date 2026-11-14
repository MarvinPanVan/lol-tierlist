# LoL tier list: how to update this site

Marvin (high Diamond / low Master, EUW) asks for an update each new patch, usually just "update it".
Hosting: Cloudflare Pages, project `lol-tierlist`, connected to this repo. Build command: none. Output directory: `public`.
Every push to `main` goes live by itself within about a minute. Nothing for Marvin to click.

## Layout

- `public/index.html` + `public/fonts/` : the live site. Never hand-edit index.html, it is generated.
- `pipeline/template.html` : the page (HTML, CSS, JS, all texts). Data goes in at `__DATA__`.
- `pipeline/tiers.json` : the data for the current patch. Source of truth for what the site shows.
- `pipeline/build.py` : `python3 pipeline/build.py` writes `public/index.html` from template + tiers.json.
- `pipeline/data`, `pipeline/data2` : raw numbers read from the stat sites for the current patch.
- `pipeline/scripts` : the scoring scripts used for 26.22. Run order: model, tiers, final, merge2, highelo3.
  They are only partly reproducible: the League of Graphs and METAsrc merge, the Diamond+/Master+ site counts
  (`ndia`, `nm`) and some note texts were done ad hoc. On the next update, consolidate everything into one
  `pipeline/update.py` that goes from raw files to tiers.json in one run, and check it reproduces the numbers.

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
3. Score (same method as 26.22, keep it unless Marvin asks to change it):
   - Per dataset: win rate minus the pick-weighted role average.
   - Shrinkage n/(n+K), K = 0.25/0.012^2 (about 1736 games). Game counts from U.GG where available.
   - Specialist penalty 0.4*ln(2/pick) when pick < 2%.
   - Consensus = Global .30, EUW .20, KR .20, Master+ .20, NA .10 (OP.GG Emerald+), then judged by hand.
     S must be positive in every region. Pick < 1.5% goes to P ("Mains only").
   - High elo = Diamond+ (OP.GG, U.GG, Blitz, dpm.lol at 1, League of Graphs at 0.5) 50%, Master+ (OP.GG, U.GG) 35%,
     EUW Emerald+ 15%. Cutoffs: Z hi>=1.8 and pick_d>=2 and dia>=1.5 and m>=1.5; P pick_d<1.5 and hi>=.6;
     S>=1.15, A>=.6, B>=.15, C>=-.45, else D.
   - Z tier in the consensus: only if clearly ahead everywhere. Empty Z is fine.
   - `nx` = 'buff' / 'nerf' for champions changed in the NEXT patch preview, else null.
4. Update the texts in `pipeline/template.html`: headline, lede (patch, date read, counts), the "Changing on ..."
   list, notes per champion live in tiers.json. Rewrite notes that no longer match the numbers.
   Writing rules from Marvin: blunt, no em dashes, must not sound AI-written, explain jargon.
5. `python3 pipeline/build.py`, then check with playwright (pipeline/scripts/shot3.py, ovf.py): no JS errors,
   no horizontal overflow at 390px, look at desktop, dark mode and the mobile sheet.
6. Commit "Patch 26.xx" and push to main. Check https://lol-tierlist.pages.dev after a minute.

## Keep

- Footer must keep Riot's Legal Jibber Jabber notice. No ads and no Riot logos (fan project rules).
- Fonts are self-hosted on purpose (no Google Fonts requests from a German site).
