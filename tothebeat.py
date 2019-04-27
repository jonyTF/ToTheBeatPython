# Note: Must have ffmpeg installed for this to work

import librosa
import subprocess
import sys
from os import walk
import random

def createThumbnail(vid_path, img_path):
    cmd = ['ffmpeg', '-i', vid_path, '-vf', 'scale=w=320:h=240:force_original_aspect_ratio=decrease', '-vframes', '1', '-y', img_path]
    subprocess.call(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

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

def getBeatTimesFromCSV(csv_path, audio_path, split_every_n_beat):
    # Get the beat times from a csv file `path`
    beat_times = [0]
    with open(csv_path) as f:
        lines = f.readlines()
        lines = [line for line in lines if line != '\n']
        for i, row in enumerate(lines):
            if i % split_every_n_beat == 0:
                sec = float(row.strip())
                beat_times.append(sec)
    beat_times.append(getSec(getDuration(audio_path)))

    return beat_times

def isVideo(filename):
    return filename.split('.')[-1] in ('mp4', 'avi', 'mov', 'flv', 'wmv')

def exportBeatTimesAsCSV(beat_times, path):
    librosa.output.times_csv(path, beat_times)  

# TODO: Also allow user to just split music into beat chunks to manually add videos
# TODO: Make it so it splits videos so that the last frame of the current clip is not too similar to the first frame of the next clip <-- probably not possible since pixel difference calc doesn't show much
    # ACTUALLY: maybe use ffmpeg's scene detection 
# TODO: Fix weird error where it doesn't sync up to the beat when fps is 24 (not 30 or 60)

###########
# OPTIONS #
###########
# audio_path = './music/creativeminds.mp3'            # Path of the song being used
# output_file_name = 'output.mp4'                     # The video file to export
# resolution_w = 1920                                 # Output resolution of video (WIDTH)
# resolution_h = 1080                                 # Output resolution of video (HEIGHT)
# vids = []                                           # The videos/images to be stitched together
# vid_directory = sys.argv[1]                         # Directory that stores the videos to edit together
# sep = 5                                             # Clips from the same video must be at least this many seconds apart
# fps = 30                                            # Output FPS of video
# split_every_n_beat = 8                              # The beat at which clips are split at 
# preset = 'ultrafast'                                # FFMPEG preset to encode the videos

def getRenderVideoCmd(
    audio_path,
    output_file_name,
    resolution_w,
    resolution_h,
    sep=5,
    fps=30,
    split_every_n_beat=4,
    preset='ultrafast',
    csv_path='',
    vids=[],
    vid_directory=''
):
    #
    # Get beat_times and the list of videos
    #
    print('Getting beat times...')
    if csv_path == '':
        beat_times = getBeatTimesFromMusic(audio_path, split_every_n_beat)
    else:
        beat_times = getBeatTimesFromCSV(csv_path, audio_path, 1)
    print('Finished.')

    #
    # Get videos from given directory if vids isn't provided
    #
    if len(vids) == 0:
        if vid_directory != '':
            for (dirpath, dirnames, filenames) in walk(vid_directory):
                vids.extend([dirpath+'/'+name for name in filenames])
        else:
            raise Exception('Neither vids nor vid_directory was specified.')

    #
    # Create the `clips` list, which stores information to split the videos
    # Each index of clips is organized as such:
    # (video_index, start_frame, end_frame, speed_factor, zoompan_effect)
    #   video_index     : int   - The index of the video in `vids`.
    #   start_frame     : int   - The frame to start cutting the video
    #   end_frame       : int   - The frame to stop cutting the video
    #   speed_factor    : float - The factor by which to multiply the PTS of the video to fix speed issues with forcing the input frame rates to `fps`
    #   zoompan_effect  : str   - The zoompan_effect to use on the video/image
    #
    print('Generating clip list...')
    clips = []
    tot_frames = 0
    beat_index = 0
    interval = beat_times[beat_index + 1] - beat_times[beat_index]

    for i in range(len(vids)):
        if beat_index + 1 >= len(beat_times):
            break

        if isVideo(vids[i]):

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

                clips.append((i, int(cur_time_fn), int(cur_time_fn) + int(interval_fn), factor, ''))
                tot_frames += int(interval_fn)
                
                cur_time = int(cur_time+interval+sep)
                beat_index += 1
                if beat_index + 1 >= len(beat_times):
                    break

                interval = beat_times[beat_index + 1] - beat_times[beat_index]
        else:
            interval_fn = interval * fps

            # Correct the frame number if it doesn't match up with the current beat_time
            correct_frame = int(beat_times[beat_index] * fps)
            if tot_frames != correct_frame:
                interval_fn += correct_frame - tot_frames

            effect = ('zoom_in', 'zoom_out', 'pan_right', 'pan_left')[random.randint(0,3)]
            clips.append((i, 0, int(interval_fn), 1, effect))
            tot_frames += int(interval_fn)

            beat_index += 1
            interval = beat_times[beat_index + 1] - beat_times[beat_index]
    print('Finished.')

    #
    # Use filter_complex to combine videos at the specified frame splits 
    #
    print('Generating command string...')
    cmd = ['ffmpeg']
    cmd.append('-hide_banner')
    cmd.append('-loglevel')
    cmd.append('level+info')
    cmd.append('-i')
    cmd.append(audio_path)

    for i in range(len(vids)):
        if not isVideo(vids[i]):
            cmd.append('-loop')
            cmd.append('1')
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
        zoompan_effects = { # TODO: Have options to disable certain effects in main.py
            'zoom_in'   : f"zoompan=z='min(zoom+0.0015,1.5)':d={end_pts-start_pts}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={resolution_w}x{resolution_h}:fps={fps},",
            'zoom_out'  : f"zoompan=z='if(lte(zoom,1),1+0.0015*{end_pts-start_pts},max(zoom-0.0015,1.001))':d={end_pts-start_pts}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={resolution_w}x{resolution_h}:fps={fps},",
            'pan_right' : f"zoompan=z=1.1:d={end_pts-start_pts}:x='x+(zoom*ih-ih)/{end_pts-start_pts}':y='ih/2-(ih/zoom/2)':s={resolution_w}x{resolution_h}:fps={fps},",
            'pan_left'  : f"zoompan=z=1.1:d={end_pts-start_pts}:x='if(lte(x,0),zoom*ih-ih,max(x-(zoom*ih-ih)/{end_pts-start_pts},0.001))':y='ih/2-(ih/zoom/2)':s={resolution_w}x{resolution_h}:fps={fps},",
        }
        effect = zoompan_effects[clips[i][4]] if clips[i][4] != '' else ''

        w = resolution_w if effect == '' else 1920*4
        h = resolution_h if effect == '' else 1080*4

        trim_str =  (
            f'[{stream_num}:v]'
            f'scale=w={w}:h={h}:force_original_aspect_ratio=increase,'
            f'crop={w}:{h}:(in_w-{w})/2:(in_h-{h})/2,'
            f'setsar=1:1,'
            f'{effect}'
            f'setpts={factor:.3f}*PTS,'
            f'trim=start_pts={start_pts}:end_pts={end_pts},'
            f'setpts=PTS-STARTPTS'
            f'[v{i}];'
        )
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
    cmd.append('-pix_fmt')
    cmd.append('yuv420p')
    cmd.append('-r')
    cmd.append(str(fps))
    cmd.append('-y')
    cmd.append(output_file_name)
    print('Finished.')
    print(' '.join(cmd))

    return (cmd, tot_frames)

def renderVideo(data):
    # Run cmd, track progress
    cmd = data[0]
    tot_frames = data[1]

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    line = ''
    end_char = '\n'
    for c in iter(lambda: process.stdout.read(1), b''):
        c = c.decode('utf-8')
        if c != end_char:
            line += c
            if 'frame=' in line:
                end_char = 'x'
        else:
            if '[fatal]' in line:
                raise Exception('An error occurred: ' + line)
            elif 'frame=' in line:
                cur_frame = int(line[line.index('frame=')+6:line.index('fps')].strip())
                progress = cur_frame / tot_frames
                print(f'Render progress: {progress*100:.3f}%')
            line = ''
    
    print('Render complete.')

if __name__ == '__main__':
    renderVideo(getRenderVideoCmd(
        './music/creativeminds.mp3',
        'output.mp4',
        1920,
        1080,
        split_every_n_beat=8,
        vid_directory=sys.argv[1],
        #csv_path='./creativeminds.csv'
    ))
    '''
    ffmpeg -r 30 -i test_videos/pan.mp4 -loop 1 -i test_videos/ken.jpg -filter_complex "[0:v]trim=start_pts=0:end_pts=60,setpts=PTS-STARTPTS,scale=w=1920:h=1080:force_original_aspect_ratio=increase,setsar=1:1[v0];[1:v]scale=w=1920*4:h=1080*4:force_original_aspect_ratio=increase,crop=1920*4:1080*4:(in_w-1920*4)/2:(in_h-1080*4)/2,setsar=1:1,zoompan=z='if(lte(zoom,1),1+0.0015*60,max(zoom-0.0015,1.001))':d=60:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=30,trim=start_pts=0:end_pts=60,setpts=PTS-STARTPTS[v1];[v0][v1]concat=n=2[out]" -map "[out]" -preset ultrafast -y -r 30 lel.mp4
    ffmpeg -r 30 -i test_videos/pan.mp4 -loop 1 -i test_videos/ken.jpg -filter_complex "[0:v]trim=start_pts=0:end_pts=60,setpts=PTS-STARTPTS,scale=w=1920:h=1080:force_original_aspect_ratio=increase,setsar=1:1[v0];[1:v]scale=w=1920*4:h=1080*4:force_original_aspect_ratio=increase,crop=1920*4:1080*4:(in_w-1920*4)/2:(in_h-1080*4)/2,setsar=1:1,zoompan=z='min(zoom+0.0015,1.5)':d=60:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=30,trim=start_pts=0:end_pts=60,setpts=PTS-STARTPTS[v1];[v0][v1]concat=n=2[out]" -map "[out]" -preset ultrafast -y -r 30 lel.mp4
    ffmpeg -r 30 -i test_videos/pan.mp4 -loop 1 -i test_videos/ken.jpg -filter_complex "[0:v]trim=start_pts=0:end_pts=60,setpts=PTS-STARTPTS,scale=w=1920:h=1080:force_original_aspect_ratio=increase,setsar=1:1[v0];[1:v]scale=w=1920*4:h=1080*4:force_original_aspect_ratio=increase,crop=1920*4:1080*4:(in_w-1920*4)/2:(in_h-1080*4)/2,setsar=1:1,zoompan=z=1.1:d=60:x='x+(zoom*ih-ih)/60':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=30,trim=start_pts=0:end_pts=60,setpts=PTS-STARTPTS[v1];[v0][v1]concat=n=2[out]" -map "[out]" -preset ultrafast -y -r 30 lel.mp4
    ffmpeg -r 30 -i test_videos/pan.mp4 -loop 1 -i test_videos/ken.jpg -filter_complex "[0:v]trim=start_pts=0:end_pts=60,setpts=PTS-STARTPTS,scale=w=1920:h=1080:force_original_aspect_ratio=increase,setsar=1:1[v0];[1:v]scale=w=1920*4:h=1080*4:force_original_aspect_ratio=increase,crop=1920*4:1080*4:(in_w-1920*4)/2:(in_h-1080*4)/2,setsar=1:1,zoompan=z=1.1:d=60:x='if(lte(x,0),zoom*ih-ih,max(x-(zoom*ih-ih)/60,0.001))':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=30,trim=start_pts=0:end_pts=60,setpts=PTS-STARTPTS[v1];[v0][v1]concat=n=2[out]" -map "[out]" -preset ultrafast -y -r 30 lel.mp4
    '''