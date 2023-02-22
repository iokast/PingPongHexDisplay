import numpy as np
import gif2numpy
from hex_mask import *
import argparse
import time
import os
import sys
import select
import tty
import termios
import cv2
import random
import fireflies
from copy import deepcopy

import _rpi_ws281x as ws

LED_CHANNEL = 0
LED_COUNT = 397              # How many LEDs to light.
LED_FREQ_HZ = 800000        # Frequency of the LED signal.  Should be 800khz or 400khz.
LED_DMA_NUM = 10            # DMA channel to use, can be 0-14.
LED_GPIO = 18               # GPIO connected to the LED signal line.  Must support PWM!
LED_BRIGHTNESS = 255        # Set to 0 for darkest and 255 for brightest
LED_INVERT = 0              # Set to 1 to invert the LED signal, good if using NPN

leds = ws.new_ws2811_t()

# Initialize all channels to off
for channum in range(2):
    channel = ws.ws2811_channel_get(leds, channum)
    ws.ws2811_channel_t_count_set(channel, 0)
    ws.ws2811_channel_t_gpionum_set(channel, 0)
    ws.ws2811_channel_t_invert_set(channel, 0)
    ws.ws2811_channel_t_brightness_set(channel, 0)

channel = ws.ws2811_channel_get(leds, LED_CHANNEL)

ws.ws2811_channel_t_count_set(channel, LED_COUNT)
ws.ws2811_channel_t_gpionum_set(channel, LED_GPIO)
ws.ws2811_channel_t_invert_set(channel, LED_INVERT)
ws.ws2811_channel_t_brightness_set(channel, LED_BRIGHTNESS)

ws.ws2811_t_freq_set(leds, LED_FREQ_HZ)
ws.ws2811_t_dmanum_set(leds, LED_DMA_NUM)

resp = ws.ws2811_init(leds)
if resp != ws.WS2811_SUCCESS:
    message = ws.ws2811_get_return_t_str(resp)
    raise RuntimeError('ws2811_init failed with code {0} ({1})'.format(resp, message))

def set_pixel_color(pixel_id, color32):
    ws.ws2811_led_set(channel, pixel_id, color32)

def refresh_display():
        resp = ws.ws2811_render(leds)
        if resp != ws.WS2811_SUCCESS:
            message = ws.ws2811_get_return_t_str(resp)
            raise RuntimeError('ws2811_render failed with code {0} ({1})'.format(resp, message))

class PPDisplay():
    def __init__(self, live) -> None:
        self.live = live
        self.frame = None
        self.prev_minute = None
        self.mask = None

    def hexcolor(self, r, g, b):
        ret = (0 << 24) | (g<<16) | (r<<8) | b
        print(ret)
        return ret
        
    def update_background(self, frame):
        self.frame = frame.copy()

    def update_clock(self, color=None, transparent=True):
        curr_time = time.localtime()

        # update clock mask if minutes have changed
        if self.prev_minute is None or curr_time.tm_min % 10 != self.prev_minute: # check if time has changed
            hour = curr_time.tm_hour % 12
            if hour == 0: hour = 12  # show 12 o'clock instead of 00
            hhmm = [int(hour / 10), int(hour % 10),
                    int(curr_time.tm_min / 10), int(curr_time.tm_min % 10)]
            self.mask = (np.array([digits[hhmm[0]], digits[hhmm[1]], digits[hhmm[2]], digits[hhmm[3]]]) \
                * clock_positions).flatten()
            self.mask = self.mask[self.mask != 0]
            self.mask = np.concatenate((self.mask, [112,66]), axis=None)  # add pixel ids for hh:mm colon

        if color is None:
            return set(self.mask)

        # update pixels with clock mask
        for pixel_id in self.mask:
            if transparent:
                self.frame[pixel_id, :3] = np.clip(self.frame[pixel_id, :3] + color, 0, 255)
            else:
                self.frame[pixel_id, :3] = np.clip(color, 0, 255)
    
    def update_pixel_color(self):
        a = self.frame[:, :3].astype(int)
        a = (a[:,1] << 16) + (a[:,2] << 8) + a[:,0]
        for pixel_id in range(397):
            # color = self.frame[pixel_id, :3]
            ws.ws2811_led_set(channel, pixel_id, int(a[pixel_id]))
        
    def refresh_display(self, ms):
        resp = ws.ws2811_render(leds)
        if resp != ws.WS2811_SUCCESS:
            message = ws.ws2811_get_return_t_str(resp)
            raise RuntimeError('ws2811_render failed with code {0} ({1})'.format(resp, message))
    
    def turn_off_display(self):
        for i in range(LED_COUNT):
            ws.ws2811_led_set(channel, i, 0)
        resp = ws.ws2811_render(leds)
        if resp != ws.WS2811_SUCCESS:
            message = ws.ws2811_get_return_t_str(resp)
            raise RuntimeError('ws2811_render failed with code {0} ({1})'.format(resp, message))
        ws.ws2811_fini(leds)
        ws.delete_ws2811_t(leds)            

class Rain:
    def __init__(self, size=100, blur=8, thickness=5, growth_spd=1, drop_interval=10):
        self.size = int(size)
        self.blur = int(blur)
        self.thickness = int(thickness)
        self.growth_spd = int(growth_spd)
        self.center = int(size / 2)
        self.drop_interval = int(drop_interval)

        self.drops_xyr = []

    def draw_drops(self):
        # clear mask
        rain_mask = np.zeros((self.size, self.size, 3), np.uint8)

        # add new drops
        if random.randint(0, self.drop_interval) == 0: 
            self.add_drop()
        
        # draw existing drops
        i = 0
        while i < len(self.drops_xyr):
            x, y, r, [b, g, red] = self.drops_xyr[i]
            rain_mask = cv2.circle(rain_mask, (x, y), r, [b, g, red], thickness=self.thickness)
            self.drops_xyr[i][2] += self.growth_spd

            if self.drops_xyr[i][2] > self.size:
                self.drops_xyr.pop(i)
            else:
                i += 1

        # blur mask
        rain_mask = cv2.blur(rain_mask, (self.blur, self.blur))
        
        return rain_mask

    def add_drop(self):
        x, y = (random.randint(20, 80), random.randint(20, 80))
        color_rand = random.randint(0, 2)
        if color_rand == 0:
            color = [random.randint(130, 200),
                    random.randint(130, 200),
                    random.randint(0, 20)]
        elif color_rand == 1:
            color = [random.randint(130, 200),
                    random.randint(0, 60),
                    random.randint(0, 20)]
        else:
            color = [random.randint(130, 200),
                    random.randint(0, 20),
                    random.randint(10, 50)]                 
        self.drops_xyr.append([x, y, 1, color])

class Clock():
    def __init__(self, left_start, top_start, interval_h, interval_v):
        self.x0 = left_start
        self.y0 = top_start
        self.dx = interval_h
        self.dy = interval_v
        self.prev_min = None
        self.mask = np.zeros((5,17))
        self.startxy = [self.x0, self.y0]

    def draw(self, background, color, transparent=True):
        curr_time = time.localtime()

        # update clock mask if minutes have changed
        if self.prev_min is None or curr_time.tm_min % 10 != self.prev_min: # check if time has changed
            hour = curr_time.tm_hour % 12
            if hour == 0: hour = 12  # show 12 o'clock instead of 00
            hhmm = [int(hour / 10), int(hour % 10),
                    int(curr_time.tm_min / 10), int(curr_time.tm_min % 10)]
            space = np.array([[0],[0],[0],[0],[0]])
            colon = np.array([[0],[1],[0],[1],[0]])
            self.mask = np.hstack((digits[hhmm[0]], space, digits[hhmm[1]], space, colon, space, digits[hhmm[2]], space, digits[hhmm[3]]))
            
        # update pixels with clock mask
        for j, y in enumerate(np.arange(self.y0, self.mask.shape[0]*self.dy, self.dy)):
            for i, x in enumerate(np.arange(self.x0, self.mask.shape[1]*self.dx, self.dx)):
                if self.mask[j,i] == 1:
                    xt = int(x)
                    if (i % 2) == 1: 
                        yt = int(y - (self.dy / 2))
                    else:
                        yt = int(y)

                    if transparent:
                        background[yt, xt, :] = np.clip(background[yt, xt, :] + color, 0, 255)
                    else:
                        background[yt, xt, :] = np.clip(color, 0, 255)

        return background

class Roll:
    def __init__(self):
        self.bg_color = np.array([0,0,0]).astype(int)
        self.dot_color = np.array([255,255,255]).astype(int)
        self.tail = 1
        self.tail_multiplier = 2
        layer_colors_base = deepcopy(hazy_p)

        for i in range(len(layer_colors_base)):
            for j in range(3):
                layer_colors_base[i][j] = g[layer_colors_base[i][j]]

        self.layer_colors_base = np.array(layer_colors_base).astype(int)

        self.layer_colors_all =  [[] for _ in range(12)]
        
        # generate cube coords for each layer/ring
        self.layers = []
        for i in range(12):
            q = [*range(i, -i, -1)] + [-i] * i + [*range(-i, i, 1)] + [i] * i
            r = q[2*i:] + q[:2*i]
            s = r[2*i:] + r[:2*i]
            self.layers.append(list(zip(r, q, s))) # qsr order affects rotation start and direction
        
        # for each cube coord assign the pixel id
        for i, coords in enumerate(cube_coords):
            layer_id = max(abs(coords))
            for j in range(len(self.layers[layer_id])):
                if tuple(coords.tolist()) == self.layers[layer_id][j]:
                    self.layers[layer_id][j] = i
                    
    def update(self):
        for i in range(1, len(self.layers)): # for each ring
            tail_len = int(self.tail + self.tail_multiplier * i)
            for j in range(0, tail_len): # for each pixel in a segment  TODO: this produces weird colors with tail + i, why?
                # c = self.dot_color
                j = j % len(self.layers[i])
                k = (j + int(len(self.layers[i])/2)) % len(self.layers[i])
                
                if len(self.layer_colors_all[i]) < tail_len:
                    c = (self.bg_color + (self.layer_colors_base[i, :] * j - self.bg_color) / tail_len).astype(int) # TODO: loop length replacing tail fixes the todo a few lines above
                    self.layer_colors_all[i].append((int(c[1]) << 16) + (int(c[0]) << 8) + int(c[2]))

                ws.ws2811_led_set(channel, self.layers[i][j], self.layer_colors_all[i][j])
                ws.ws2811_led_set(channel, self.layers[i][k], self.layer_colors_all[i][j])
            
            self.layers[i].append(self.layers[i].pop(0))

        self.refresh_display()
        
    def refresh_display(self):
        resp = ws.ws2811_render(leds)
        if resp != ws.WS2811_SUCCESS:
            message = ws.ws2811_get_return_t_str(resp)
            raise RuntimeError('ws2811_render failed with code {0} ({1})'.format(resp, message))


def main(live, bg, br):

    def isData():
        return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])
    old_settings = termios.tcgetattr(sys.stdin)
        
    if bg == "all":
        filelist = []
        for file in os.listdir('gifs'):
            if file.endswith(".gif"):
                filelist.append(file[:-4])
    else:
        filelist = [bg]
    
    filelist = sorted(filelist)
    print("GIFs loading: ", filelist)
    
    gif_np_list = []
    for bg in filelist:
    # convert gif to array
        if bg == "rain":
            gif_np_list = np.zeros((1, 30))
            rain = Rain()
            rgb1 = np.full((100,100, 3), [40,20,0]) # [100, 50, 0])
            # rgb2 = np.full((100,100, 3), [220, 220, 0])

            multiplier = 100 / 23.
            gif_coords = cartesian_coords * multiplier
            
            whex = np.max(gif_coords[:,1])
            left_margin = (100 - whex)/2
            gif_coords[:,1] = gif_coords[:,1] + left_margin
            gif_coords[:,0] = gif_coords[:,0] + (multiplier / 2)
            gif_coords = gif_coords.astype(int)

            left_start = left_margin
            top_start = multiplier
            interval_h = 0.86605 * multiplier
            interval_v = multiplier
        elif bg == 'roll' or bg == 'fireflies':
            gif_np_list = np.zeros((1, 30))
        elif os.path.isfile('gifs/np/' + bg + '.npy' ):
            with open('gifs/np/' + bg + '.npy', 'rb') as f:
                gif_np_list.append(np.load(f))
        else:
            np_frames, extensions, image_specifications = gif2numpy.convert('gifs/' + bg + '.gif')
            w, h, _ = np_frames[0].shape
            multiplier = min(w, h) / 23.
            gif_coords = cartesian_coords * multiplier
            
            whex = np.max(gif_coords[:,1])
            left_margin = (w - whex)/2
            gif_coords[:,1] = gif_coords[:,1] + left_margin
            gif_coords[:,0] = gif_coords[:,0] + (multiplier / 2)
            gif_coords = gif_coords.astype(int)



            np_frames_reduced = np.zeros((len(np_frames), 397, 3), dtype=int)
            for i, frame in enumerate(np_frames):
                for j in range(397):
                    for k in range(3):
                        np_frames_reduced[i, j, k] = g[frame[gif_coords[j,0], gif_coords[j,1], k]]

            with open('gifs/np/' + bg + '.npy', 'wb') as f:
                np.save(f, np_frames_reduced)

            gif_np_list.append(np_frames_reduced)

    # run display loop
    gif_id = 0
    LED_BRIGHTNESS = 255 
    disp = PPDisplay(live)
    # clock = Clock(left_start, top_start, interval_h, interval_v)
    roll = Roll()
    ffs = fireflies.Fireflies(ff_count=11, tail_len=10, color_list=hazy_p[1:])
    clock_brightness = 255
    bg_brightness = 100
    ms = 40
    current_gif_np = np.copy(gif_np_list[gif_id])
    previous_time = time.time()
    try:
        while True:
            fcnt = 0
            t0 = time.time()
            
            tty.setcbreak(sys.stdin.fileno())
            for frame in current_gif_np:  # frame starts as background
                if isData():
                    c = sys.stdin.read(1)
                    if c== 'w': 
                        LED_BRIGHTNESS = min(LED_BRIGHTNESS + 20,255)
                        print("All Bright Up: ", LED_BRIGHTNESS)
                        ws.ws2811_channel_t_brightness_set(channel, LED_BRIGHTNESS)
                        time.sleep(.1)
                        resp = ws.ws2811_init(leds)
                        if resp != ws.WS2811_SUCCESS:
                            message = ws.ws2811_get_return_t_str(resp)
                            raise RuntimeError('ws2811_init failed with code {0} ({1})'.format(resp, message))
                    elif c == 'q': 
                        LED_BRIGHTNESS = max(LED_BRIGHTNESS - 20,0)
                        print("All Bright Down: ", LED_BRIGHTNESS)
                        ws.ws2811_channel_t_brightness_set(channel, LED_BRIGHTNESS)
                        time.sleep(.1)
                        resp = ws.ws2811_init(leds)
                        if resp != ws.WS2811_SUCCESS:
                            message = ws.ws2811_get_return_t_str(resp)
                            raise RuntimeError('ws2811_init failed with code {0} ({1})'.format(resp, message))
                    elif c == 's': 
                        gif_id = (gif_id + 1) % len(gif_np_list)
                        current_gif_np = np.copy(gif_np_list[gif_id]) * (bg_brightness / 100)
                        print("Next GIF: ", gif_id, filelist[gif_id])
                        time.sleep(.1)
                        break
                    elif c == 'a': 
                        gif_id = (gif_id - 1) % len(gif_np_list)
                        current_gif_np = np.copy(gif_np_list[gif_id]) * (bg_brightness / 100)
                        print("Prev GIF: ", gif_id, filelist[gif_id])
                        time.sleep(.1)
                        break
                    elif c == 'p': 
                        clock_brightness = min(clock_brightness + 20, 255)
                        print("Clock Bright Up: ", clock_brightness)
                        time.sleep(.1)
                    elif c == 'o': 
                        clock_brightness = max(clock_brightness - 20, 0)
                        print("Clock Bright Down: ", clock_brightness)
                        time.sleep(.1)
                    elif c == 'l': 
                        bg_brightness = min(bg_brightness + 10, 100)
                        current_gif_np = np.copy(gif_np_list[gif_id]) * (bg_brightness / 100)
                        print("BG Bright Up (%): ", bg_brightness)
                        time.sleep(.1)
                        break
                    elif c == 'k': 
                        bg_brightness = max(bg_brightness - 10, 10)
                        current_gif_np = np.copy(gif_np_list[gif_id]) * (bg_brightness / 100)
                        print("BG Bright Down (%): {}".format(bg_brightness))
                        time.sleep(.1)
                        break
                    elif c == 'z': 
                        ms = max(ms - 10, 0)
                        print("Interval Down (ms): ", ms)
                        time.sleep(.1)
                        break
                    elif c == 'x': 
                        ms = min(ms + 10, 500)
                        print("Interval Up (ms): ", ms)
                        time.sleep(.1)
                        break
     
                if bg == 'rain':
                    rain_mask = rain.draw_drops()
                    background = (rgb1 + rain_mask).astype(int)
                    # background = clock.draw(background, np.array([clock_brightness]*3))
                    background_32 = (background[:,:,1] << 16) + (background[:,:,2] << 8) + background[:,:,0]
                    
                    # clock_pixels = disp.update_clock(np.array([clock_brightness]*3))

                    for pixel_id in range(397):
                        # print(background.shape, background_32.shape, gif_coords[pixel_id, :])
                        ws.ws2811_led_set(channel, pixel_id, int(background_32[gif_coords[pixel_id, 0], gif_coords[pixel_id, 1]]))
                        
                    resp = ws.ws2811_render(leds)
                    if resp != ws.WS2811_SUCCESS:
                        message = ws.ws2811_get_return_t_str(resp)
                        raise RuntimeError('ws2811_render failed with code {0} ({1})'.format(resp, message))
                elif bg == 'roll':
                    roll.update()
                elif bg == 'fireflies':
                    ffs.update()
                else:         
                    disp.update_background(frame)
                    disp.update_clock(np.array([clock_brightness]*3))
                    disp.update_pixel_color()            
                    disp.refresh_display(ms)
                
                fcnt += 1
                elapsed = time.time() - previous_time
                time.sleep(max(0, (ms / 1000.0) - elapsed))
                previous_time = time.time()
            
            print("FPS = ", round(fcnt / (time.time() - t0), 2), end='\r')

    except KeyboardInterrupt:
        disp.turn_off_display()
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-ledon', action='store_true')
    parser.add_argument('-ledoff', dest='ledon', action='store_false')
    parser.set_defaults(feature=False)
    parser.add_argument('-bg', type=str, required=False, default='vortex100')
    parser.add_argument('-br', type=int, required=False, default=255)
    args = parser.parse_args()

    live = bool(args.ledon)

    main(live, args.bg, args.br)
