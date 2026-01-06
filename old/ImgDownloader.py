import requests
import os

songs=[x.split('^')[0] for x in open('Songfile.txt','r')]
imgs=[x[:-4] for x in list(os.listdir('imgs'))]
missing=[x for x in songs if x not in imgs]
missing=list(reversed(missing))
d={x.split('^')[0]:x.split('^')[1][32:43] for x in open('Songfile.txt','r')}

for sng in missing:
    print(sng)
    url=f'https://img.youtube.com/vi/{d[sng]}/hqdefault.jpg'
    fil=open('imgs/'+sng+'.jpg','wb')
    fil.write(requests.get(url).content)
    fil.close()