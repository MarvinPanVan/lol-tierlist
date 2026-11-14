# LoL tier list

A League of Legends tier list for every role, rebuilt each patch from nine stat sites (OP.GG, U.GG, Blitz, dpm.lol, League of Graphs, METAsrc, Mobalytics, Lolalytics, lol.ps).
Scores are win rate above the role average, corrected for sample size and one-trick inflation, with a separate high elo view (Diamond+ and Master+).

Live: https://lol-tierlist.pages.dev

`public/` is the site. `pipeline/` has the raw data, the scoring scripts and the page template; `python3 pipeline/build.py` rebuilds the site.

LoL Tier List was created under Riot Games' "Legal Jibber Jabber" policy using assets owned by Riot Games. Riot Games does not endorse or sponsor this project.
