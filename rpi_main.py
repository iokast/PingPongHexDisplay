import os
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

from hex_mask import *
import argparse
import time
import sys
import select
import tty
import termios
from fireflies import Fireflies
from rain import Rain
from clock import Clock
from led_strip import LedStrip
from gif import Gif
from spin import Spin
from expanse import Expanse

def main(live, bg, br):

    # Setup LED Strip 
    strip = LedStrip()
    strip.brightness = 100

    # Setup initial parameters
    clock_brightness = 255
    bg_brightness = 100
    ms = 40
    num_of_loops = 30
    cols_id = 0
    help_message =  "q/w: Overall Brightness (down/up)\n" \
                    "a/s: Gif (previous/next)\n" \
                    "z/x: Time Delay (down/up)\n" \
                    "t/y: Animation Mode (previous/next)\n" \
                    "o/p: Clock Brightness (down/up)\n" \
                    "k/l: Background Brightness (down/up)\n" \
                    "n/m: Color Palette (previous/next)"

    # Setup animation modes
    gif = Gif()
    spin = Spin(color_palette=color_palette_11[cols_id])
    expanse = Expanse(color_palette=color_palette_11[cols_id])
    fireflies = Fireflies(ff_count=11, tail_len=6, color_list=color_palette_11[cols_id])
    rain = Rain()
    mode = [gif, spin, fireflies, rain, expanse]
    mode_names = ['expanse', 'gif', 'spin', 'fireflies', 'rain']

    # Setup clock
    clock = Clock()
    


    # Setup for keyboard input
    def isData():
        return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])
    old_settings = termios.tcgetattr(sys.stdin)
        
    # run display loop
    previous_time = time.time()
    mode_id = 0
    input_delay = .1
    try:
        while True:
            t0 = time.time()
            tty.setcbreak(sys.stdin.fileno())   # for keyboard input
            

            for _ in range(num_of_loops):
                if isData():
                    c = sys.stdin.read(1)
                    if c== 'w': 
                        strip.change_brightness(20)
                        print("All Bright Up: ", strip.brightness)
                        time.sleep(input_delay)
                    elif c == 'q': 
                        strip.change_brightness(-20)
                        print("All Bright Down: ", strip.brightness)
                        time.sleep(input_delay)
                    elif c == 's': 
                        gif.gif_change(1)
                        print("Next GIF: ", gif.gif_id, gif.filelist[gif.gif_id])
                        time.sleep(input_delay)
                        break
                    elif c == 'a': 
                        gif.gif_change(-1)
                        print("Prev GIF: ", gif.gif_id, gif.filelist[gif.gif_id])
                        time.sleep(input_delay)
                        break
                    elif c == 'p': 
                        clock_brightness = min(clock_brightness + 20, 255)
                        print("Clock Bright Up: ", clock_brightness)
                        time.sleep(input_delay)
                    elif c == 'o': 
                        clock_brightness = max(clock_brightness - 20, 0)
                        print("Clock Bright Down: ", clock_brightness)
                        time.sleep(input_delay)
                    elif c == 'l': 
                        gif.brightness_change(10)   # TODO: Might want to make this applicable to all animations
                        print("BG Bright Up (%): ", gif.brightness)
                        time.sleep(input_delay)
                        break
                    elif c == 'k': 
                        gif.brightness_change(10)   # TODO: Might want to make this applicable to all animations
                        print("BG Bright Down (%): ", gif.brightness)
                        time.sleep(input_delay)
                        break
                    elif c == 'z': 
                        ms = max(ms - 10, 0)
                        print("Interval Down (ms): ", ms)
                        time.sleep(input_delay)
                    elif c == 'x': 
                        ms = min(ms + 10, 500)
                        print("Interval Up (ms): ", ms)
                        time.sleep(input_delay)
                    elif c == 't': 
                        mode_id = (mode_id - 1) % len(mode)
                        print("Prev Mode: ", mode_id, mode_names[mode_id])
                        time.sleep(input_delay)
                        break
                    elif c == 'y': 
                        mode_id = (mode_id + 1) % len(mode)
                        print("Next Mode: ", mode_id, mode_names[mode_id])
                        time.sleep(input_delay)
                        break
                    elif c == 'n': 
                        cols_id = (cols_id - 1) % len(color_palette_11)
                        try:
                            mode[mode_id].set_palette(color_palette_11[cols_id])
                            print("Next Color Palette: ", cols_id)
                        except:
                            print("No set_palette function")
                        break
                    elif c == 'm': 
                        cols_id = (cols_id + 1) % len(color_palette_11)
                        try:
                            mode[mode_id].set_palette(color_palette_11[cols_id])
                            print("Next Color Palette: ", cols_id)
                        except:
                            print("No set_palette function")
                        time.sleep(input_delay)
                        break
                    elif c == 'h':
                        print(help_message) 
     
                mode[mode_id].update(strip)
                
                elapsed = time.time() - previous_time
                time.sleep(max(0, (ms / 1000.0) - elapsed))
                previous_time = time.time()
            
            print("FPS = ", round(num_of_loops / (time.time() - t0), 2), end='\r')

    except KeyboardInterrupt:
        strip.turn_off()
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)   # turn off keyboard input


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