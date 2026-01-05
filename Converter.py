import os

inpath='C:/Users/Abhijato/Music/'
outpath='C:/Users/Abhijato/Music Center/'
songs=[x for x in os.listdir(inpath) if x not in os.listdir(outpath)]
for song in songs:
    if len(song.split('-'))>1:
        art=song.split('-')[0]
    else:
        art=''
    os.system(f'ffmpeg -i "{inpath}{song}" -metadata artist="{art}" -acodec aac "{outpath}{song[:-4]}.m4a" -y')