# Note: Must have ffmpeg installed for this to work

import numpy as np

import librosa
import librosa.display

import matplotlib.pyplot as plt

import subprocess

import sys
from os import walk
import os
import tempfile

'''
audio_path = './training_data/summer.mp3'

y, sr = librosa.load(audio_path)

y_harmonic, y_percussive = librosa.effects.hpss(y)

tempo, beat_frames = librosa.beat.beat_track(y=y_percussive, sr=sr)

print('Tempo: {:.2f} bpm'.format(tempo))

beat_times = librosa.frames_to_time(beat_frames, sr=sr)

print(beat_times)

librosa.output.times_csv('summer.csv', beat_times)  
'''
beat_times = [0]
with open('energy.csv') as f:
    lines = f.readlines()
    lines = [line for line in lines if line != '\n']
    for i, row in enumerate(lines):
        if i % 4 == 0:
            sec = float(row.strip())
            beat_times.append(sec)

def getDuration(filename):
    result = subprocess.Popen(['ffprobe', filename], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for l in result.stdout.readlines():
        l = l.decode('utf-8')
        if 'Duration' in l:
            return l[ l.index(':')+1 : l.index('.')].strip()
    raise Exception('Video length not found for ' + filename)

def getSec(timestamp):
    h, m, s = timestamp.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)

vids = []
for (dirpath, dirnames, filenames) in walk(sys.argv[1]):
    vids.extend([dirpath+'/'+name for name in filenames])

print(vids)


sep = 5 # Clips from the same video must be at least this many seconds apart

'''
vid_index = 0
for i in range(len(beat_times) - 1):
    interval = beat_times[i+1] - beat_times[i]
    #print(interval)
    if (vid_index >= len(vids)):
        break
         
    length = getLength(vids[vid_index])
'''

clips = []
beat_index = 0
interval = beat_times[beat_index + 1] - beat_times[beat_index]

for i in range(len(vids)):
    if beat_index + 1 >= len(beat_times):
        break

    length = getSec(getDuration(vids[i]))

    time = 0
    while time+interval < length:
        clips.append((vids[i], str(time), str(interval)))
        
        beat_index += 1
        time = time+interval+sep
        interval = beat_times[beat_index + 1] - beat_times[beat_index]

print(beat_times)
print(clips)



#with tempfile.TemporaryDirectory() as directory:
directory = 'tmp'
concat_str = ''
for i in range(len(clips)):
    mp4_name = 'out'+str(i)+'.mp4'
    cmd = ['ffmpeg', '-ss', clips[i][1], '-i', clips[i][0], '-c', 'copy', '-t', clips[i][2], directory + '/' + mp4_name]
    subprocess.call(cmd)

    mp4_name2 = 'out_'+str(i)+'.mp4'
    cmd = ['ffmpeg', '-fflags', '+genpts', '-avoid_negative_ts', 'make_zero', '-i', directory + '/' + mp4_name, '-c', 'copy', directory + '/' + mp4_name2]
    subprocess.call(cmd)
    concat_str += "file '"+ mp4_name2 +"'\n"
    #concat_str += ts_name + '|'

with open(directory + '/list.txt', 'w') as f:
    f.write(concat_str)
exit()
concat_str = concat_str[:-1]
print(concat_str)

full_vid_name = directory+'/full.mp4'
cmd = ['ffmpeg', '-fflags', '+genpts', '-avoid_negative_ts', 'make_zero', '-i', concat_str, '-c', 'copy', full_vid_name]
subprocess.call(cmd)

song_name = 'training_data/energy.mp3'
cmd = ['ffmpeg', '-i', full_vid_name, '-i', song_name, '-c', 'copy', '-shortest', '-map', '0:v:0', '-map', '1:a:0', 'final.mp4']
subprocess.call(cmd)

print(directory)

print('DONEEE')



    


# ('test_videos/dance.mp4', '0', '0.093')    


#t = getLength('test_videos/VID_20190308_163349.mp4')
#if ()

'''
ffmpeg -ss 30 -i input.mp4 -c copy -t 10 output.mp4
'''

'''
ffmpeg -i input.mp4 -c copy int1.ts
ffmpeg -i "concat:int1.ts|int2.ts" -c copy output.mp4
'''

'''
ffmpeg -i output.mp4 -i training_data/energy.mp3 -c copy -shortest -map 0:v:0 -map 1:a:0 final.mp4
'''

'''
ffmpeg -i test_videos/VID_20190308_163349.mp4 -filter_complex "
    [0:v]trim=5:10,setpts=PTS-STARTPTS[v0];
    [0:v]trim=60:65,setpts=PTS-STARTPTS[v1];
    [v0][v1]concat=n=2:v=1:a=0[out]
" -map "[out]" output.mp4
'''