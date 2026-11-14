"""Build public/index.html from pipeline/template.html + pipeline/tiers.json."""
import os
here=os.path.dirname(os.path.abspath(__file__))
t=open(os.path.join(here,'template.html'),encoding='utf-8').read()
d=open(os.path.join(here,'tiers.json'),encoding='utf-8').read()
assert t.count('__DATA__')==1
open(os.path.join(here,'..','public','index.html'),'w',encoding='utf-8').write(t.replace('__DATA__',d))
print('built public/index.html')
