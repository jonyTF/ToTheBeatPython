# Note: Must have ffmpeg installed for this to work

import librosa
import subprocess
import sys
from os import walk

def getDuration(filename):
    # Get the duration of media file `filename`
    result = subprocess.Popen(['ffmpeg', '-i', filename], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for l in result.stdout.readlines():
        l = l.decode('utf-8')
        if 'Duration' in l:
            return l[ l.index(':')+1 : l.index('.')].strip()
    raise Exception('Video length not found for ' + filename)

def getFrameRate(filename):
    # Get the frame rate of media file `filename`
    result = subprocess.Popen(['ffmpeg', '-i', filename], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for l in result.stdout.readlines():
        l = l.decode('utf-8')
        if 'Video' in l:
            return float(l[l.rindex(',', 0, l.index('fps'))+1:l.index('fps')].strip())
    raise Exception('Framerate not found for ' + filename)

def getSec(timestamp):
    # Get the amount of seconds in a timestamp of format HH:MM:SS
    h, m, s = timestamp.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)

def getBeatTimesFromMusic(path, split_every_n_beat):
    # Get the beat times using librosa from an audio file `path`
    y, sr = librosa.load(path)
    y_harmonic, y_percussive = librosa.effects.hpss(y)
    tempo, beat_frames = librosa.beat.beat_track(y=y_percussive, sr=sr)
    beat_times_init = librosa.frames_to_time(beat_frames, sr=sr)

    beat_times = [0]
    for i in range(len(beat_times_init)):
        if i % split_every_n_beat == 0:
            beat_times.append(beat_times_init[i])
    beat_times.append(getSec(getDuration(path)))

    return beat_times

def getBeatTimesFromCSV(path, split_every_n_beat):
    # Get the beat times from a csv file `path`
    beat_times = [0]
    with open(path) as f:
        lines = f.readlines()
        lines = [line for line in lines if line != '\n']
        for i, row in enumerate(lines):
            if i % split_every_n_beat == 0:
                sec = float(row.strip())
                beat_times.append(sec)
    beat_times.append(getSec(getDuration(audio_path)))

    return beat_times

def exportBeatTimesAsCSV(beat_times, path):
    librosa.output.times_csv(path, beat_times)  

###########
# OPTIONS #
###########
audio_path = './training_data/creativeminds.mp3'    # Path of the song being used
sep = 5                                             # Clips from the same video must be at least this many seconds apart
resolution_w = 1920                                 # Output resolution of video (WIDTH)
resolution_h = 1080                                 # Output resolution of video (HEIGHT)
fps = 30                                            # Output FPS of video
vid_directory = sys.argv[1]                         # Directory that stores the videos to edit together
split_every_n_beat = 8                              # The beat at which clips are split at 
preset = 'ultrafast'                                # FFMPEG preset to encode the videos
output_file_name = 'output.mp4'                     # The video file to export

#
# Get beat_times and the list of videos
#
beat_times = getBeatTimesFromMusic(audio_path, split_every_n_beat)

vids = []
for (dirpath, dirnames, filenames) in walk(vid_directory):
    vids.extend([dirpath+'/'+name for name in filenames])

#
# Create the `clips` list, which stores information to split the videos
# Each index of clips is organized as such:
# (video_index, start_frame, end_frame, speed_factor)
#   video_index : int   - The index of the video in `vids`
#   start_frame : int   - The frame to start cutting the video
#   end_frame   : int   - The frame to stop cutting the video
#   speed_factor: float - The factor by which to multiply the PTS of the video to fix speed issues with forcing the input frame rates to `fps`
#
clips = []
tot_frames = 0
beat_index = 0
interval = beat_times[beat_index + 1] - beat_times[beat_index]

for i in range(len(vids)):
    if beat_index + 1 >= len(beat_times):
        break

    length = getSec(getDuration(vids[i]))

    # Needed to fix speed issues as a result of forcing frame rate to `fps`
    orig_fps = getFrameRate(vids[i])
    factor = fps / orig_fps

    cur_time = 0

    # While still enough time left in the video
    while cur_time+interval < length:
        cur_time_fn = cur_time * fps
        interval_fn = interval * fps

        # Correct the frame number if it doesn't match up with the current beat_time
        correct_frame = int(beat_times[beat_index] * fps)
        if tot_frames != correct_frame:
            interval_fn += correct_frame - tot_frames

        clips.append((i, int(cur_time_fn), int(cur_time_fn) + int(interval_fn), factor))
        tot_frames += int(interval_fn)
        
        cur_time = int(cur_time+interval+sep)
        beat_index += 1
        if beat_index + 1 >= len(beat_times):
            break

        interval = beat_times[beat_index + 1] - beat_times[beat_index]

#
# Use filter_complex to combine videos at the specified frame splits 
#
cmd = ['ffmpeg']
cmd.append('-i')
cmd.append(audio_path)

for i in range(len(vids)):
    cmd.append('-r')
    cmd.append(str(fps))
    cmd.append('-i')
    cmd.append(vids[i])

cmd.append('-filter_complex')
filter_str = ''
concat_str = ''
for i in range(len(clips)):
    # Add 1 to stream_num because the song is the 0th input
    stream_num = clips[i][0] + 1
    factor = clips[i][3]
    start_pts = clips[i][1]
    end_pts = clips[i][2]
    trim_str = f'[{stream_num}:v]\
                setpts={factor:.3f}*PTS,\
                trim=start_pts={start_pts}:end_pts={end_pts},\
                setpts=PTS-STARTPTS,\
                scale=w={resolution_w}:h={resolution_h}:force_original_aspect_ratio=decrease\
                [v{i}];'
    filter_str += trim_str
    concat_str += f'[v{i}]'
concat_str += f'concat=n={len(clips)}[out]'
filter_str += concat_str

cmd.append(filter_str)
cmd.append('-shortest')
cmd.append('-map')
cmd.append('[out]')
cmd.append('-map')
cmd.append('0:a')
cmd.append('-preset')
cmd.append(preset)
cmd.append('-r')
cmd.append(str(fps))
cmd.append('-y')
cmd.append(output_file_name)
subprocess.call(cmd)

print('DONE')