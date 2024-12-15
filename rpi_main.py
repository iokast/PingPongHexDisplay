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
import threading

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
stop_thread = False  # Control flag for the animation loop
thread_lock = threading.Lock()

def animation_loop():
    global stop_thread
    previous_time = time.time()

    while not stop_thread:
        with thread_lock:
            display.update()

        elapsed = time.time() - previous_time
        time.sleep(max(0, (display.ms_between_frames / 1000.0) - elapsed))
        previous_time = time.time()

# Flask routes
@app.route('/set_params', methods=['POST'])
def set_params():
    data = request.json
    with thread_lock:  # Ensure thread-safe updates
        if "brightness_background" in data:
            display.brightness_background = float(data["brightness_background"])
            display.expanse.alpha = display.brightness_background

        if "brightness_clock" in data:
            display.brightness_clock = float(data["brightness_clock"])
            display.clock.alpha = display.brightness_clock

        if "colors_id" in data:
            display.colors_id = int(data["colors_id"])
            display.colors = display.adjust_gamma(color_palette_11[display.colors_id])
            display.expanse.color_palette = display.colors

        if "ms_between_frames" in data:
            display.ms_between_frames = int(data["ms_between_frames"])

    return jsonify({"status": "parameters updated"})

@app.route('/turn_off', methods=['POST'])
def turn_off():
    with thread_lock:
        display.turn_off()
    return jsonify({"status": "LEDs turned off"})

if __name__ == '__main__':
    # Start the animation loop in a separate thread
    animation_thread = threading.Thread(target=animation_loop, daemon=True)
    animation_thread.start()

    try:
        app.run(host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        stop_thread = True
        animation_thread.join()
        display.turn_off()
