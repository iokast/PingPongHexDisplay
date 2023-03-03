import numpy as np
from hex_mask import *
import cv2
import random


class Rain:
    def __init__(self, size=100, blur=8, thickness=5, growth_spd=1, drop_interval=10):
        self.size = int(size)
        self.blur = int(blur)
        self.thickness = int(thickness)
        self.growth_spd = int(growth_spd)
        self.center = int(size / 2)
        self.drop_interval = int(drop_interval)

        self.drops_xyr = []

        gif_np_list = np.zeros((1, 30))
        self.rgb1 = np.full((100,100, 3), [40,20,0]) # initialize canvas with bg color

        multiplier = 100 / 23.  # TODO: Hardcoded size of 100x100 canvas. Consider making dynamic.
        gif_coords = cartesian_coords * multiplier
        
        whex = np.max(gif_coords[:,1])
        left_margin = (100 - whex)/2
        gif_coords[:,1] = gif_coords[:,1] + left_margin
        gif_coords[:,0] = gif_coords[:,0] + (multiplier / 2)
        self.gif_coords = gif_coords.astype(int)

        left_start = left_margin
        top_start = multiplier
        interval_h = 0.86605 * multiplier
        interval_v = multiplier

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

    def update(self, strip):
        rain_mask = self.draw_drops()
        background = (self.rgb1 + rain_mask).astype(int)
        background_32 = (background[:,:,1] << 16) + (background[:,:,2] << 8) + background[:,:,0]
        
        for pixel_id in range(397):
            strip.set_pixel_color(self, pixel_id, int(background_32[self.gif_coords[pixel_id, 0], self.gif_coords[pixel_id, 1]]))
            
        strip.refresh_display()