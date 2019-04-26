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

cmd = 'ffmpeg -hide_banner -loglevel error -ss 26 -i test_videos/circle.mp4 -frames:v 1 -f rawvideo -pix_fmt rgb24 pipe:1'.split(' ')
process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
img1_data = np.frombuffer(process.stdout.read(), np.uint8).reshape([HEIGHT, WIDTH, 3])
#print(img_data)

cmd = 'ffmpeg -hide_banner -loglevel error -ss 29 -i test_videos/circle.mp4 -frames:v 1 -f rawvideo -pix_fmt rgb24 pipe:1'.split(' ')
process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
img2_data = np.frombuffer(process.stdout.read(), np.uint8).reshape([HEIGHT, WIDTH, 3])

diff = abs(img1_data - img2_data)
print(diff)

average_rgb_diff = diff.sum(axis=0).sum(axis=0) / (WIDTH * HEIGHT) / 255
print(average_rgb_diff)