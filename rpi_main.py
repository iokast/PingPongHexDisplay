# set working directory
import os
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# libraries
from hex_mask import color_palette_11, gamma_adj
from flask import Flask, request, jsonify
from led_strip import LedStrip
from expanse import Expanse
from clock import Clock
import numpy as np
import time

# Flask app
app = Flask(__name__)

class Display():
    def __init__(self, colors_id, brightness_background=0.1, brightness_clock=0.3):
        # Setup LED Strip
        self.strip = LedStrip()

        # Setup initial parameters
        self.brightness_background = brightness_background
        self.brightness_clock = brightness_clock
        self.colors_id = colors_id
        self.colors = self.adjust_gamma(color_palette_11[colors_id])
        self.ms_between_frames = 30

        # Setup animations
        self.expanse = Expanse(color_palette=self.colors, alpha=self.brightness_background)
        self.clock = Clock([255, 255, 255], alpha=self.brightness_clock)

    def adjust_gamma(self, color_palette):
        return [[gamma_adj[value] for value in row] for row in color_palette]
    
    def set_brightness(self, background=None, clock=None):
        if background:
            self.brightness_background = background
            self.expanse.set_brightness(self.brightness_background)
        elif clock: 
            self.brightness_clock = clock
            self.clock.set_brightness(self.brightness_clock)

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

# Initialize display
display = Display(colors_id=0)

@app.route('/set_params', methods=['POST'])
def set_params():
    # Parse JSON data
    data = request.json
    print(data)
    if "brightness_background" in data:
        display.set_brightness(background=float(data["brightness_background"])/100)

    if "brightness_clock" in data:
        display.set_brightness(clock=float(data["brightness_clock"])/100)

    if "fps" in data:
        display.ms_between_frames = int(1000/float(data["fps"]))

    return jsonify({"status": "parameters updated"})

@app.route('/change_colors', methods=['POST'])
def change_colors():
    display.colors_id = (display.colors_id + 1) % len(color_palette_11)
    display.colors = display.adjust_gamma(color_palette_11[display.colors_id])
    display.expanse.set_palette(display.colors)
    return jsonify({"status": "colors updated"})

@app.route('/turn_off', methods=['POST'])
def turn_off():
    display.turn_off()
    return jsonify({"status": "LEDs turned off"})

@app.route('/run', methods=['POST'])
def run():
    num_loops_to_update_fps = 30
    t0 = time.time()
    previous_time = time.time()
    frame_count = 0

    while True:
        try:
            display.update()

            elapsed = time.time() - previous_time
            time.sleep(max(0, (display.ms_between_frames / 1000.0) - elapsed))
            previous_time = time.time()

            frame_count += 1
            if frame_count == num_loops_to_update_fps:
                print("FPS = ", round(frame_count / (time.time() - t0), 2), end='\r')
                t0 = time.time()
                frame_count = 0
        except KeyboardInterrupt:
            display.turn_off()
            break

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
