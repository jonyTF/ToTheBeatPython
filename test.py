#ffmpeg -ss 5 -i test_videos/pan.mp4 -frames:v 1 -f mjpeg pipe:1
import subprocess
import numpy as np

# THIS TEST PROGRAM gets the rgb difference between two frames

'''
a = np.array([
    [
        [245, 237, 225], [255, 240, 230], [255, 240, 230]
    ],
    [
        [255, 240, 230], [255, 240, 230], [255, 240, 230]
    ],
    [
        [255, 240, 230], [255, 240, 230], [255, 240, 230]
    ],
])

b = np.array([
    [
        [255, 240, 230], [245, 237, 225], [245, 237, 225]
    ],
    [
        [245, 237, 225], [245, 237, 225], [245, 237, 225]
    ],
    [
        [245, 237, 225], [245, 237, 225], [245, 237, 225]
    ],
])
diff = abs(a-b)
print(diff)
w = 3
h = 3
print(diff.sum(axis=0).sum(axis=0) / (h*w))

exit()
'''


WIDTH = 3840
HEIGHT = 2160

CMP_SIZE = 10
DIV = 16

vid = 'test_videos/circle.mp4'

cmd = f'ffmpeg -hide_banner -loglevel error -ss 54 -i {vid} -frames:v 1 -vf scale={WIDTH/DIV}:{HEIGHT/DIV} -f rawvideo -pix_fmt rgb24 pipe:1'.split(' ')
process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
img1_data = np.frombuffer(process.stdout.read(), np.uint8).reshape([int(WIDTH/DIV), int(HEIGHT/DIV), 3])
#print(img_data)

cmd = f'ffmpeg -hide_banner -loglevel error -ss 37 -i {vid} -frames:v 1 -vf scale={WIDTH/DIV}:{HEIGHT/DIV} -f rawvideo -pix_fmt rgb24 pipe:1'.split(' ')
process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
img2_data = np.frombuffer(process.stdout.read(), np.uint8).reshape([int(WIDTH/DIV), int(HEIGHT/DIV), 3])

diff = abs(img1_data - img2_data)
#print(diff)

average_rgb_diff = diff.sum(axis=0).sum(axis=0) / (WIDTH/DIV * HEIGHT/DIV) / 255
print(average_rgb_diff)

small_change = 0
big_change = 0
threshold = 255/2

small_change = (diff < threshold).sum()
big_change = diff.shape[0]*diff.shape[1]*diff.shape[2] - small_change

print(f'small_change: {small_change}, big_change: {big_change}')
print(f'diff: {big_change-small_change}')

if small_change > big_change:
    print('TOO SIMILAR1')
elif abs(big_change - small_change) < 4000:
    print('TOO SIMILAR2')
else:
    print('DIFFERENT ENOUGH')