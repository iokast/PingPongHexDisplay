# set working directory
import os
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# libraries
from hex_mask import color_palette_11, gamma_adj
import time
from led_strip_cy import LedStrip
from expanse import Expanse
from clock import Clock
import numpy as np

class Display():
    def __init__(self, colors_id):
        # Setup LED Strip 
        self.strip = LedStrip()

        # Setup initial parameters
        self.alpha_background = .1
        self.alpha_clock = .3
        self.num_of_loops = 30
        self.colors = self.adjust_gamma(color_palette_11[colors_id])

        # setup animations
        self.expanse = Expanse(color_palette=self.colors, alpha=self.alpha_background)
        self.clock = Clock([255,255,255], alpha=self.alpha_clock)

    # adjust gamma in colors
    def adjust_gamma(self, color_palette):
        return [[gamma_adj[value] for value in row] for row in color_palette]

    def update(self):
        state = self.expanse.update(self.strip)
        state = state + self.clock.update(self.strip)
        
        state = np.clip(state, 0, 255)

        state_24bit = ((state[:, 1] << 16) | (state[:, 0] << 8) | state[:, 2]).tolist()

        self.strip.set_pixel_colors(state_24bit)

        self.strip.refresh_display()

    def turn_off(self):
        self.strip.turn_off()


if __name__ == '__main__':
    colors_id = 0
    num_loops = 30
    
    display = Display(colors_id)
    
    try:
        while True:
            t0 = time.time()
            for _ in range(num_loops):
                display.update()
            print("FPS = ", round(num_loops / (time.time() - t0), 2), end='\r')

    except KeyboardInterrupt:
        display.turn_off()