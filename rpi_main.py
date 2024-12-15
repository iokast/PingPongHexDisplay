# set working directory
import os
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# libraries
from hex_mask import color_palette_11, gamma_adj
import time
from led_strip import LedStrip
from expanse import Expanse
from clock import Clock
import numpy as np

class Display():
    def __init__(self, colors_id):
        # Setup LED Strip 
        self.strip = LedStrip()

        # Setup initial parameters
        self.brightness_background = .1
        self.brightness_clock = .3
        self.colors_id = colors_id
        self.colors = self.adjust_gamma(color_palette_11[colors_id])

        # setup animations
        self.expanse = Expanse(color_palette=self.colors, alpha=self.brightness_background)
        self.clock = Clock([255,255,255], alpha=self.brightness_clock)

    # adjust gamma in colors
    def adjust_gamma(self, color_palette):
        return [[gamma_adj[value] for value in row] for row in color_palette]

    def update(self):
        state = self.expanse.update(self.strip)
        state = state + self.clock.update(self.strip)
        
        state = np.clip(state, 0, 255)

        state_24bit = ((state[:, 1] << 16) | (state[:, 0] << 8) | state[:, 2]).tolist()

        for pix_id, color in enumerate(state_24bit):
            self.strip.set_pixel_color(pix_id, color)

        self.strip.refresh_display()

    def turn_off(self):
        self.strip.turn_off()


if __name__ == '__main__':
    colors_id = 0
    num_loops_to_update_fps = 30
    ms_between_frames = 30
    
    display = Display(colors_id)
    
    try:
        t0 = time.time()
        previous_time = time.time()
        frame_count = 0
        while True:
            display.update()

            elapsed = time.time() - previous_time
            time.sleep(max(0, (ms_between_frames / 1000.0) - elapsed))
            previous_time = time.time()

            frame_count += 1
            if frame_count == num_loops_to_update_fps:
                print("FPS = ", round(frame_count / (time.time() - t0), 2), end='\r')
                t0 = time.time()
                frame_count = 0

    except KeyboardInterrupt:
        display.turn_off()