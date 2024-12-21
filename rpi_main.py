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
from spin import Spin
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
        self.background_animations = [Expanse(color_palette=self.colors, alpha=self.brightness_background),
                                      Spin(color_palette=self.colors, alpha=self.brightness_background)]
        self.background_animation_id = 0
        # self.background_animation_current = self.background_animations[self.background_animation_id]
        
        self.clock_animations = [Clock([255, 255, 255], alpha=self.brightness_clock)]
        self.clock_animation_id = 0
        # self.clock_animation_current = self.clock_animations[self.clock_animation_id]

    def adjust_gamma(self, color_palette):
        return [[gamma_adj[value] for value in row] for row in color_palette]

    def set_color_and_brightness(self):
        for animation in self.background_animations:
            animation.set_palette(self.colors, self.brightness_background)

        self.clock_animations[self.clock_animation_id].set_brightness(self.brightness_clock)

    def change_clock_type(self):
        self.clock_animations[self.clock_animation_id].change_type()

    def change_background_type(self):
        self.background_animation_id = (self.background_animation_id + 1) % len(self.background_animations)

    def change_clock_color_type(self):
        self.clock_animations[self.clock_animation_id].change_color_type()

    def update(self):
        state = np.zeros((397,3), dtype=int)
        state = self.background_animations[self.background_animation_id].update(state)
        state = self.clock_animations[self.clock_animation_id].update(state)
        state = np.clip(state, 0, 255)

        state_24bit = ((state[:, 1] << 16) | (state[:, 0] << 8) | state[:, 2]).tolist()

        for pix_id, color in enumerate(state_24bit):
            self.strip.set_pixel_color(pix_id, color)

        self.strip.refresh_display()

    def turn_off(self):
        self.strip.turn_off()

# Global variables
display = None
stop_thread = True  # Control flag for the animation loop
thread = None

def animation_loop():
    global stop_thread, display
    frame_count = 0
    num_loops_to_update_fps = 30
    t0 = time.time()
    previous_time = time.time()

    while not stop_thread:
        if display is not None:
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
            except:
                display.turn_off()

@app.route('/set_params', methods=['POST'])
def set_params():
    global display
    # Parse JSON data
    data = request.json
    if display is not None:
        if "brightness_background" in data:
            display.brightness_background = float(data["brightness_background"]) / 100
        if "brightness_clock" in data:
            display.brightness_clock = float(data["brightness_clock"]) / 100
        display.set_color_and_brightness()

        if "fps" in data:
            display.ms_between_frames = int(1000 / float(data["fps"]))

    return jsonify({"status": "parameters updated"})

@app.route('/change_colors', methods=['POST'])
def change_colors():
    global display
    if display is not None:
        display.colors_id = (display.colors_id + 1) % len(color_palette_11)
        display.colors = display.adjust_gamma(color_palette_11[display.colors_id])
        display.set_color_and_brightness()
    return jsonify({"status": "colors updated"})

@app.route('/change_clock_type', methods=['POST'])
def change_clock_type():
    global display
    if display is not None:
        display.change_clock_type()
    return jsonify({"status": "clock type updated"})

@app.route('/change_background_type', methods=['POST'])
def change_background_type():
    global display
    if display is not None:
        display.change_background_type()
    return jsonify({"status": "background type updated"})

@app.route('/change_clock_color_type', methods=['POST'])
def change_clock_color_type():
    global display
    if display is not None:
        display.change_clock_color_type()
    return jsonify({"status": "clock color type updated"})

@app.route('/turn_on_off', methods=['POST'])
def turn_on_off():
    global stop_thread, thread, display
    if stop_thread == False:
        stop_thread = True
        if thread and thread.is_alive():
            thread.join()  # Wait for the thread to finish safely
        if display is not None:
            display.turn_off()
        return jsonify({"status": "LEDs turned off"})
    if stop_thread == True:
        if display is None:
            display = Display(colors_id=0)  # Reinitialize the Display object safely
        stop_thread = False
        thread = threading.Thread(target=animation_loop, daemon=True)
        thread.start()  # Start the animation loop
        return jsonify({"status": "LEDs turned on and animation started"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
