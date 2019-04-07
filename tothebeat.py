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
    result = subprocess.Popen(['ffmpeg', '-i', filename], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
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

print('Cutting clips...', end='')
sys.stdout.flush()

for i in range(len(clips)):
    mp4_name = 'out'+str(i)+'.mp4'
    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'panic', '-ss', clips[i][1], '-i', clips[i][0], '-t', clips[i][2], '-avoid_negative_ts', 'make_zero', '-c', 'copy', '-y', directory + '/' + mp4_name]
    #cmd = ['ffmpeg', '-i', clips[i][0], '-ss', clips[i][1], '-t', clips[i][2], '-c', 'copy', '-y', directory + '/' + mp4_name]
    subprocess.call(cmd)

    mp4_corrected_name = 'out'+str(i)+'_c.mp4' # Correct the length
    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'panic', '-ss', '0', '-i', directory + '/' + mp4_name, '-t', clips[i][2], '-avoid_negative_ts', 'make_zero', '-c', 'copy', '-y', directory + '/' + mp4_corrected_name]
    subprocess.call(cmd)

    concat_str += "file '"+ mp4_corrected_name +"'\n"
    #concat_str += ts_name + '|'

concat_file = directory + '/list.txt'
with open(concat_file, 'w') as f:
    f.write(concat_str)

print('Finished.')
sys.stdout.flush()

print('Combining clips...', end='')
sys.stdout.flush()
full_vid_name = directory+'/full.mp4'
cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'panic', '-f', 'concat', '-safe', '0', '-i', concat_file, '-c', 'copy', '-y', full_vid_name]
subprocess.call(cmd)
print('Finished.')
sys.stdout.flush()

print('Adding audio...', end='')
sys.stdout.flush()
song_name = 'training_data/energy.mp3'
cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'panic', '-i', full_vid_name, '-i', song_name, '-c', 'copy', '-shortest', '-map', '0:v:0', '-map', '1:a:0', '-y', 'final.mp4']
subprocess.call(cmd)
print('Finished')
sys.stdout.flush()

print('Temp directory: ', directory)

print('DONEEE')



    


# ('test_videos/dance.mp4', '0', '0.093')    


#t = getLength('test_videos/VID_20190308_163349.mp4')
#if ()


''' ### Normal cut
ffmpeg -i input.mp4 -ss 00:27 -t 00:15 -acodec copy -vcodec copy -y output_nc.mp4
'''

''' ### Keyframe cut
ffmpeg -ss 00:27 -i input.mp4 -t 00:15 -avoid_negative_ts make_zero -acodec copy -vcodec copy -y output_kc.mp4
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