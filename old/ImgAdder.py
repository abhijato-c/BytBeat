import os

path='C:/Users/Abhijato/Music Center/'

for song in ['Kimi no na wa-Sparkle.mp4', 'The Days.mp4']:
    os.system(f'exiftool "-CoverArt<=imgs/{song[:-4]}.jpg" "{path}{song[:-4]}.m4a" -overwrite_original')