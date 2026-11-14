import os; os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # run from anywhere; paths are relative to pipeline/
import pandas as pd, numpy as np, json
# Final tiers: model score as the base, adjusted by judgment (robustness, elo, region, sample).
FINAL = {
'top': {
 'S': ['Malphite','Darius','Kayle','Shen','Singed'],
 'A': ['Gangplank','Fiora','Camille','Teemo','Sion','Urgot','Kled'],
 'B': ['Garen','Irelia','Zaahen','Gwen','Ornn','Cho\'Gath','Riven','Sett','Pantheon','Illaoi'],
 'C': ['Nasus','Mordekaiser','Kennen','Tryndamere','Olaf','Jax','Volibear','Dr. Mundo','Tahm Kench','Gragas','Aatrox'],
 'D': ['Renekton','Akali','Yone','Yasuo','Gnar','Yorick','Ambessa','Jayce','K\'Sante','Trundle'],
 'P': ['Poppy','Quinn','Anivia','Warwick','Lissandra','Wukong'],
},
'jungle': {
 'S': ['Wukong','Lillia','Zac','Nunu & Willump','Zyra'],
 'A': ['Bel\'Veth','Sejuani','Cho\'Gath','Fiddlesticks','Briar','Shyvana','Warwick','Udyr','Elise','Nidalee'],
 'B': ['Shaco','Ekko','Kindred','Evelynn','Taliyah','Master Yi','Rammus','Talon','Xin Zhao'],
 'C': ['Naafiri','Kayn','Hecarim','Sylas','Kha\'Zix','Diana','Karthus'],
 'D': ['Viego','Graves','Jarvan IV','Amumu','Vi','Nocturne','Rengar','Lee Sin','Zed','Qiyana'],
 'P': ['Rek\'Sai','Sion','Zaahen','Darius','Ivern','Skarner'],
},
'mid': {
 'Z': ['Ekko'],
 'S': ['Vex','Katarina','Vladimir','Ahri','Hwei'],
 'A': ['Twisted Fate','LeBlanc','Diana','Aurora','Zoe','Lissandra','Annie','Fizz'],
 'B': ['Taliyah','Xerath','Akshan','Aurelion Sol','Veigar','Kassadin','Lux','Talon','Anivia'],
 'C': ['Zed','Yone','Syndra','Qiyana','Malzahar'],
 'D': ['Yasuo','Galio','Irelia','Akali','Viktor','Sylas','Locke','Cassiopeia','Azir','Orianna','Mel','Ryze'],
 'P': ['Pantheon','Vel\'Koz'],
},
'adc': {
 'Z': ['Xayah','Kog\'Maw'],
 'S': ['Jinx'],
 'A': ['Zeri','Twitch','Yasuo','Corki','Sivir','Viktor'],
 'B': ['Miss Fortune','Draven','Smolder','Jhin','Ziggs','Aphelios','Samira'],
 'C': ['Tristana','Ashe'],
 'D': ['Yunara','Kai\'Sa','Varus','Vayne','Lucian','Kalista','Caitlyn','Ezreal'],
 'P': ['Swain','Vel\'Koz','Karthus','Aurelion Sol','Hwei','Veigar','Nilah'],
},
'support': {
 'S': ['Rell','Leona','Braum','Senna','Alistar','Thresh','Zilean'],
 'A': ['Rakan','Blitzcrank','Maokai','Poppy','Sona','Janna'],
 'B': ['Seraphine','Soraka','Vel\'Koz','Nami'],
 'C': ['Zyra','Renata Glasc','Galio'],
 'D': ['Milio','Lulu','Tahm Kench','Pyke','Morgana','Bard','Nautilus','Brand','Lux','Swain','Karma','Xerath','Pantheon','Neeko','Yuumi'],
 'P': ['Taric','Amumu'],
},
}
NOTES = {
 ('top','Malphite'):'Above average in all 5 datasets with 6.8% pick rate. Weaker in Master+ (+0.9) than Emerald.',
 ('top','Darius'):'Rare combo: very popular AND winning. Best in Master+ (+1.9), so not just a low-elo stomp.',
 ('top','Kayle'):'Buffed in 26.22 (Q and R cooldowns). Scaling pick, +2.3 in Master+.',
 ('top','Shen'):'Buffed in 26.22. Smallest regional spread of the S tier; safe everywhere.',
 ('top','Singed'):'Top of the raw numbers in every region, but almost only mains play him. Strong, not a blind pick for most.',
 ('top','Gangplank'):'#1 on Lolalytics and lol.ps (KR), 26-27% ban in KR. Only +0.2 in EUW. Very high skill floor.',
 ('top','Fiora'):'Average-ish in Emerald, elite in Master+ (+2.1). Pays off with skill.',
 ('top','Sion'):'Huge region split: +2.6 in KR, -1.4 in NA.',
 ('top','Kled'):'Good in Emerald, below average in Master+.',
 ('top','Garen'):'Most popular top laner in EUW (8.3%). Fine in Emerald, neutral in Master+.',
 ('top','Irelia'):'13% ban, but only slightly above average.',
 ('top','Olaf'):'Lolalytics S-, every OP.GG view says average. Lolalytics outlier.',
 ('top','Yone'):'Lolalytics S-. Actual win rate is below average in every region. Popular, not strong.',
 ('top','Jayce'):'10% pick in KR, -1.7 to -3.5 pp everywhere. Trap.',
 ('top',"K'Sante"):'Worst popular top laner (about -3.7 global). W buff coming in 26.23.',
 ('top','Gnar'):'Q ratios buffed in 26.23. Currently bottom five.',
 ('top','Ambessa'):'4.5% pick, -2 pp everywhere.',
 ('top','Wukong'):'Fine top, but under 1% pick there; he is a jungler first.',
 ('top','Lissandra'):'Lolalytics S- off a 0.5% pick rate. Classic off-role specialist inflation.',
 ('jungle','Wukong'):'Most played of the S tier (6.7%). Drops to +0.8 in Master+.',
 ('jungle','Zyra'):'Only 1.9% pick but positive everywhere, +2.9 in Master+.',
 ('jungle','Lillia'):'Consistent in every region.',
 ('jungle','Nunu & Willump'):'Underplayed (2%). Strong in NA and Master+.',
 ('jungle','Zac'):'Lowest regional spread of any S-tier jungler.',
 ('jungle',"Bel'Veth"):'+1.2 to +1.4 in every dataset including Master+. Very robust.',
 ('jungle','Sejuani'):'Strong in Emerald (+2.0 EUW), only +0.4 in Master+.',
 ('jungle',"Cho'Gath"):'S+ on Lolalytics. Good, but only +0.6 in Master+.',
 ('jungle','Warwick'):'Great in EUW/KR, slightly negative in NA, flat in Master+.',
 ('jungle','Nidalee'):'KR +2.1, Master+ +2.4, EUW -0.7. Skill-gated.',
 ('jungle','Shaco'):'17.5% ban. NA +2.5 but KR -1.2.',
 ('jungle','Master Yi'):'Q nerf lands in 26.23. Already only slightly above average.',
 ('jungle','Lee Sin'):'13% pick, 15% ban, -1.7 consensus. In KR he has 24% pick and 47% ban. Pro-play darling, solo queue loser.',
 ('jungle','Qiyana'):'Worst jungler in the data: 7.8% pick, -3.4, plus a 16% ban rate.',
 ('jungle','Viego'):'8% pick, below average. Lolalytics A.',
 ('jungle','Graves'):'7.3% pick, below average except NA.',
 ('jungle','Jarvan IV'):'8.1% pick, below average everywhere.',
 ('jungle','Vi'):'E buff coming in 26.23.',
 ('jungle',"Rek'Sai"):'Best raw numbers of any jungler (+2.1 to +3.3 everywhere incl. Master+) but only 1.35% pick, mostly mains.',
 ('jungle','Darius'):'14% ban is from top lane; few play him jungle.',
 ('mid','Ekko'):'Most robust pick in the whole game: +2.2 to +2.5 in all five datasets.',
 ('mid','Ahri'):'11.5% pick and still +0.7 to +1.5. That combination is rare.',
 ('mid','Katarina'):'KR +2.5, Master+ +1.9, EUW only +0.4.',
 ('mid','Vex'):'Underplayed (2.9%). Strong everywhere.',
 ('mid','LeBlanc'):'Q ratio nerf in 26.23. 43% ban in KR.',
 ('mid','Fizz'):'NA +2.5, Master+ -0.4. Low-elo friendlier.',
 ('mid','Zoe'):'KR and Master+ ~+2, EUW/NA ~+0.2. Skill-gated.',
 ('mid','Taliyah'):'Average in Emerald, +2.3 in Master+.',
 ('mid','Syndra'):'9% pick, below average. E nerf in 26.23.',
 ('mid','Zed'):'25% ban for an average champion.',
 ('mid','Locke'):'Most banned mid (30%) and one of the worst win rates. Ban rate measures annoyance, not strength.',
 ('mid','Orianna'):'5% pick, -2 pp. Pro favorite, solo queue trap.',
 ('mid','Mel'):'Reworked in 26.22, still -2.1. More buffs in 26.23.',
 ('mid','Galio'):'Shield buff in 26.23.',
 ('mid','Azir'):'Range and W buff in 26.23.',
 ('mid','Viktor'):'Buffed in 26.22, still -1.1 mid. Plays better bot.',
 ('mid','Akali'):'8% pick, 18% ban, -1.1.',
 ('mid','Pantheon'):'+1.6 to +2.1 everywhere but under 1% pick.',
 ('adc','Xayah'):'Best real marksman: +1.8 to +2.1 in all five datasets at 8.4% pick.',
 ('adc',"Kog'Maw"):'+1.8 to +2.8 everywhere. Needs a peel/enchanter support.',
 ('adc','Jinx'):'10.8% pick and still +0.7 to +1.3.',
 ('adc','Zeri'):'KR +2.1, NA +0.1.',
 ('adc','Yasuo'):'Bot Yasuo outperforms mid Yasuo by about 2 pp.',
 ('adc','Viktor'):'Better bot (+0.75) than mid (-1.1).',
 ('adc','Jhin'):'S+ on Lolalytics because their formula rewards popularity. Actual win rate only slightly above average.',
 ('adc',"Kai'Sa"):'Most picked ADC (24%), below average everywhere.',
 ('adc','Caitlyn'):'21% ban rate for a -1.6 champion. Banned a lot, loses more than she wins.',
 ('adc','Ezreal'):'Worst major pick in the game: 15% pick, -3.4 to -4.0 everywhere. W and R buffs in 26.23.',
 ('adc','Smolder'):'Buffed in 26.22 (+1.2 pp vs 26.21 per ggez.gg).',
 ('adc','Swain'):'Mage bot. +3.6 to +5.0 everywhere incl. Master+. Real, but 1% pick and draft-dependent.',
 ('adc',"Vel'Koz"):'Mage bot. Up to +5 in NA. R tweak in 26.23.',
 ('support','Rell'):'Highest consensus support. KR and Master+ +2.7.',
 ('support','Thresh'):'Nerfed in 26.22 and still +1 at 13.8% pick.',
 ('support','Zilean'):'KR +3.0, NA only +0.4.',
 ('support','Leona'):'Best in NA (+2.4). Simple and strong.',
 ('support','Nami'):'EUW +1.3, KR -1.4. Region-dependent.',
 ('support','Lulu'):'13% pick, 16% ban, below average everywhere.',
 ('support','Nautilus'):'11.8% pick, -0.8. Popular, not good.',
 ('support','Karma'):'7.8% pick, -1.5. Biggest support trap.',
 ('support','Pyke'):'24% ban, -0.7.',
 ('support','Yuumi'):'-2.3 Emerald, -5.5 in Master+.',
 ('support','Bard'):'Q buff in 26.23.',
 ('support','Taric'):'+3.2 in Master+, but 1.2% pick.',
 ('support','Zyra'):'Fine in Emerald, -2.2 in Master+.',
}
LABEL={'S':'S','A':'A','B':'B','C':'C','D':'D','P':'Pocket picks'}
data={}
for role,tiers in FINAL.items():
    t=pd.read_csv(f'out_{role}.csv').set_index('champion')
    seen=set(); data[role]=[]
    for tier,champs in tiers.items():
        for c in champs:
            assert c in t.index, (role,c)
            assert c not in seen, (role,c); seen.add(c)
            r=t.loc[c]
            f=lambda v: None if pd.isna(v) else round(float(v),2)
            data[role].append({'c':c,'t':tier,'score':f(r.score),'pick':f(r.pick_g),'ban':f(r.ban_g),
              'g':f(r['global']),'euw':f(r.euw),'kr':f(r.kr),'na':f(r.na),'m':f(r.mplus),
              'll':r.ll_tier if isinstance(r.ll_tier,str) else '','note':NOTES.get((role,c),'')})
    # sanity: list any champs with score>0.6 & pick>=1.5 not placed
    miss=t[(~t.index.isin(seen))&(t.pick_g>=1.5)]
    print(role,'placed',len(seen),'| unplaced with pick>=1.5%:',', '.join(f"{i}({r.score:.2f})" for i,r in miss.iterrows()))
    for tier,champs in tiers.items():
        sc=[t.loc[c,'score'] for c in champs]
        print('  ',tier,'score range %.2f..%.2f'%(min(sc),max(sc)))
for k in NOTES: assert k[1] in [d['c'] for d in data[k[0]]], k
json.dump(data,open('tiers.json','w'),ensure_ascii=False)
print('ok')
