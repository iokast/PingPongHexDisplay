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

def main(live, bg, br):

    # Setup LED Strip 
    strip = LedStrip()

    # Setup animation modes
    gif = Gif()
    spin = Spin()
    fireflies = Fireflies(ff_count=11, tail_len=10, color_list=hazy_p[1:])
    rain = Rain()
    mode = [gif, spin, fireflies, rain]

    # Setup clock
    clock = Clock()
    
    # Setup initial parameters
    clock_brightness = 255
    bg_brightness = 100
    ms = 40
    num_of_loops = 30

    # Setup for keyboard input
    def isData():
        return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])
    old_settings = termios.tcgetattr(sys.stdin)
        
    # run display loop
    previous_time = time.time()
    mode_id = 0
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
                        time.sleep(.1)
                    elif c == 'q': 
                        strip.change_brightness(-20)
                        print("All Bright Down: ", strip.brightness)
                        time.sleep(.1)
                    elif c == 's': 
                        gif.gif_change(1, bg_brightness)
                        print("Next GIF: ", gif.gif_id, gif.filelist[gif.gif_id])
                        time.sleep(.1)
                        break
                    elif c == 'a': 
                        gif.gif_change(-1, bg_brightness)
                        print("Prev GIF: ", gif.gif_id, gif.filelist[gif.gif_id])
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
                        gif.brightness_change(10)   # TODO: Might want to make this applicable to all animations
                        print("BG Bright Up (%): ", gif.brightness)
                        time.sleep(.1)
                        break
                    elif c == 'k': 
                        gif.brightness_change(10)   # TODO: Might want to make this applicable to all animations
                        print("BG Bright Down (%): ", gif.brightness)
                        time.sleep(.1)
                        break
                    elif c == 'z': 
                        ms = max(ms - 10, 0)
                        print("Interval Down (ms): ", ms)
                        time.sleep(.1)
                    elif c == 'x': 
                        ms = min(ms + 10, 500)
                        print("Interval Up (ms): ", ms)
                        time.sleep(.1)
     
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
