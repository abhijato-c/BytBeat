import yt_dlp
import os

outpath='C:/Users/Abhijato/Music'
fil=open('Songfile.txt','r')
urls={x.split('^')[0]:x.split('^')[1] for x in fil if x.split('^')[0]+'.m4a' not in os.listdir(outpath) and x.split('^')[1]!=''}
fil.close()

for sname in urls.keys():
    print("Downloading : "+sname)
    video=yt_dlp.YoutubeDL({'format':'251',
                            'paths':{'home':outpath},
                            'outtmpl':sname+'.m4a',
                            })
    print(urls[sname])
    try:
        video.download([urls[sname]])
    except:
        print("failed to download "+sname)