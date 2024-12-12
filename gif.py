import numpy as np
import gif2numpy
from hex_mask import *
import time
import os

class Gif():
    def __init__(self) -> None:
        self.frame = None
        self.prev_minute = None
        self.mask = None

        self.filelist = []
        for file in os.listdir('gifs'):
            if file.endswith(".gif"):
                self.filelist.append(file[:-4])
        
        self.gif_np_list = self.load_gifs(self.filelist)
        self.gif_id = 0
        self.current_gif_np = np.copy(self.gif_np_list[self.gif_id])

        self.frame_id = 0
        self.brightness = 100
        

    def load_gifs(self, filelist):
        filelist = sorted(filelist)
        print("GIFs loading: ", filelist)
        
        gif_np_list = []
        for bg in filelist:
            if os.path.isfile('gifs/np/' + bg + '.npy' ):
                with open('gifs/np/' + bg + '.npy', 'rb') as f:
                    gif_np_list.append(np.load(f))
            else:
                np_frames, _, _ = gif2numpy.convert('gifs/' + bg + '.gif')
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
        
        return gif_np_list


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
    

    def update_pixel_color(self, strip):
        a = self.frame[:, :3].astype(int)
        a = (a[:,1] << 16) + (a[:,2] << 8) + a[:,0]
        for pixel_id in range(397):
            strip.set_pixel_color(pixel_id, int(a[pixel_id]))

    def gif_change(self, incr):
        self.gif_id = (self.gif_id + incr) % len(self.gif_np_list)
        self.frame_id = 0
        self.brightness_change(0)

    def brightness_change(self, incr):
        self.brightness = max(10, min(self.brightness + incr, 100))
        self.current_gif_np = np.copy(self.gif_np_list[self.gif_id]) * (self.brightness / 100)

    def update(self, strip):
        self.update_background(self.current_gif_np[self.frame_id])
        self.update_pixel_color(strip)            
        strip.refresh_display()
        self.frame_id = (self.frame_id + 1) % self.current_gif_np.shape[0]
     

