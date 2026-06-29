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
from threading import Thread
from shader import Shader
from queue import Queue
from solar_dimmer import SolarDimmer

# Flask app
app = Flask(__name__)

class Display():
    def __init__(self, colors_id, brightness_background=0.4, brightness_clock=0.4):
        # Setup LED Strip
        self.strip = LedStrip()

        # Setup initial parameters
        self.brightness_background = brightness_background
        self.brightness_clock = brightness_clock
        self.colors_id = colors_id
        self.colors = color_palette_11[colors_id]
        # Zero disables sleeping and is useful for measuring maximum throughput.
        target_fps = float(os.environ.get("PPL_FPS", "60"))
        self.frame_interval = 0.0 if target_fps <= 0 else 1.0 / target_fps
        self.is_on = True
        self.gamma_adj = np.array(gamma_adj)
        self.state = np.zeros((397, 3), dtype=np.int16)
        self.dimmer = SolarDimmer()
        self.dimmer_brightness = 1.0

        # Setup animations
        self.background_animations = [Shader(color_palette=self.colors, alpha=self.brightness_background),
                                      Expanse(color_palette=self.colors, alpha=self.brightness_background),
                                      Spin(color_palette=self.colors, alpha=self.brightness_background)]
        self.background_animation_id = 0
        
        self.clock_animations = [Clock([255, 255, 255], alpha=self.brightness_clock)]
        self.clock_animation_id = 0

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
        frame_start = time.perf_counter()
        state = self.state
        state.fill(0)
        state = self.background_animations[self.background_animation_id].update(state)
        background_done = time.perf_counter()
        state = self.clock_animations[self.clock_animation_id].update(state)
        self.dimmer_brightness = self.dimmer.brightness()
        if self.dimmer_brightness != 1.0:
            state = (state * self.dimmer_brightness).astype(np.int16)
        state = np.clip(state, 0, 255)
        state = self.gamma_adj[state]

        state_24bit = ((state[:, 1].astype(np.uint32) << 16) |
                       (state[:, 0].astype(np.uint32) << 8) |
                       state[:, 2].astype(np.uint32))
        compose_done = time.perf_counter()
        self.strip.set_pixel_colors(state_24bit)
        pixels_done = time.perf_counter()
        self.strip.refresh_display()
        render_done = time.perf_counter()

        self.last_timings = (
            background_done - frame_start,
            compose_done - background_done,
            pixels_done - compose_done,
            render_done - pixels_done,
        )

    def turn_off(self):
        self.strip.turn_off()
        display.is_on = not display.is_on

# Global variables
display = Display(colors_id=0)
command_queue = Queue()

@app.route('/set_params', methods=['POST'])
def set_params():
    global display
    data = request.json
    if display is not None:
        if "brightness_background" in data:
            display.brightness_background = float(data["brightness_background"]) / 100
        if "brightness_clock" in data:
            display.brightness_clock = float(data["brightness_clock"]) / 100
        if "brightness_background" in data or "brightness_clock" in data:
            display.dimmer.start_override()
            display.dimmer_brightness = 1.0
        display.set_color_and_brightness()

        if "fps" in data:
            fps = float(data["fps"])
            display.frame_interval = 0.0 if fps <= 0 else 1.0 / fps

    return jsonify({
        "status": "parameters updated",
        "automatic_dimmer": not display.dimmer.override_active(),
        "dimmer_brightness": display.dimmer_brightness,
    })

@app.route('/change_colors', methods=['POST'])
def change_colors():
    global command_queue, display
    if display is not None:
        display.colors_id = (display.colors_id + 1) % len(color_palette_11)
        display.colors = color_palette_11[display.colors_id]
        command_queue.put("change_colors")
    return jsonify({"status": "colors updated"})

@app.route('/change_clock_type', methods=['POST'])
def change_clock_type():
    global command_queue
    command_queue.put("change_clock_type") 
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
    global command_queue
    command_queue.put("turn_off") 
    return jsonify({"status": "LEDs turned on/off"})

def process_commands():
    global command_queue, display
    while not command_queue.empty():
        command = command_queue.get()
        if command == "change_colors":
            display.colors_id = (display.colors_id + 1) % len(color_palette_11)
            display.colors = color_palette_11[display.colors_id]
            display.set_color_and_brightness()
        elif command == "change_background_type":
            display.change_background_type()
        elif command == "change_clock_type":
            display.change_clock_type()
        elif command == "turn_off":
            display.turn_off()

def animation_loop():
    global display
    display.background_animations[0].initialize_opengl()
    frame_count = 0
    num_loops_to_update_fps = 60
    report_start = time.perf_counter()
    timing_totals = np.zeros(5, dtype=float)

    try:
        while True:
            frame_start = time.perf_counter()
            process_commands()
            if display.is_on: display.update()

            work_elapsed = time.perf_counter() - frame_start
            sleep_time = max(0.0, display.frame_interval - work_elapsed)
            if sleep_time:
                time.sleep(sleep_time)

            if display.is_on:
                timing_totals[:4] += display.last_timings
            timing_totals[4] += sleep_time

            frame_count += 1
            if frame_count == num_loops_to_update_fps:
                report_elapsed = time.perf_counter() - report_start
                averages_ms = timing_totals * (1000.0 / frame_count)
                print(
                    f"FPS {frame_count / report_elapsed:5.1f} | "
                    f"shader {averages_ms[0]:5.1f} ms | "
                    f"compose {averages_ms[1]:4.1f} ms | "
                    f"pixels {averages_ms[2]:4.1f} ms | "
                    f"render {averages_ms[3]:4.1f} ms | "
                    f"sleep {averages_ms[4]:4.1f} ms | "
                    f"dim {display.dimmer_brightness * 100:3.0f}%"
                    f"{' manual' if display.dimmer.override_active() else ' auto'}",
                    end='\r',
                )
                report_start = time.perf_counter()
                timing_totals.fill(0)
                frame_count = 0
    except KeyboardInterrupt:
        display.turn_off()

if __name__ == '__main__':
    # Start Flask in a separate thread
    flask_thread = Thread(target=lambda: app.run(host='0.0.0.0', port=5000), daemon=True)
    flask_thread.start()

    # Run the main OpenGL animation loop
    animation_loop()
