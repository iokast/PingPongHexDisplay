import numpy as np
import hexy as hx
import pygame as pg
from text_for_hex import radial_to_irl_map
from simulate_helpers import *
from hex_mask import color_palette_11
from expanse import Expanse
from clock import Clock

class Selection:
    class Type:
        POINT = 0 
        RING = 1
        DISK = 2
        LINE = 3

        @staticmethod
        def to_string(selection_type):
            if selection_type == Selection.Type.DISK:
                return "disk"
            elif selection_type == Selection.Type.RING:
                return "ring"
            elif selection_type == Selection.Type.LINE:
                return "line"
            else:
                return "point"

    @staticmethod
    def get_selection(selection_type, cube_mouse, rad, clicked_hex=None):
        if selection_type == Selection.Type.DISK:
            return hx.get_disk(cube_mouse, rad.value)
        elif selection_type == Selection.Type.RING:
            return hx.get_ring(cube_mouse, rad.value)
        elif selection_type == Selection.Type.LINE:
            return hx.get_hex_line(clicked_hex, cube_mouse)
        else:
            return cube_mouse.copy()


class ClampedInteger:
    """
    A simple class for "clamping" an integer value between a range. Its value will not increase beyond `upper_limit`
    and will not decrease below `lower_limit`.
    """
    def __init__(self, initial_value, lower_limit, upper_limit):
        self.value = initial_value
        self.lower_limit = lower_limit
        self.upper_limit = upper_limit

    def increment(self):
        self.value += 1
        if self.value > self.upper_limit:
            self.value = self.upper_limit

    def decrement(self):
        self.value -= 1
        if self.value < self.lower_limit:
            self.value = self.lower_limit


class CyclicInteger:
    """
    A simple helper class for "cycling" an integer through a range of values. Its value will be set to `lower_limit`
    if it increases above `upper_limit`. Its value will be set to `upper_limit` if its value decreases below
    `lower_limit`.
    """
    def __init__(self, initial_value, lower_limit, upper_limit):
        self.value = initial_value
        self.lower_limit = lower_limit
        self.upper_limit = upper_limit

    def increment(self):
        self.value += 1
        if self.value > self.upper_limit:
            self.value = self.lower_limit

    def decrement(self):
        self.value -= 1
        if self.value < self.lower_limit:
            self.value = self.upper_limit


class ExampleHexMap:
    def __init__(self, size=(800, 800), hex_radius=20, caption="ExampleHexMap"):
        self.orient = True  # True => flat top hexes
        self.color_palette = list((np.asarray(color_palette_11[0])).astype(int))

        self.alpha_bg = .5
        self.alpha_cl = .4

        self.expanse = Expanse(self.color_palette, self.alpha_bg)
        self.clock_animation = Clock([255, 255, 255], self.alpha_cl)
        self.time_disp = TimeDisp()
        self.time_mat = self.time_disp.update_time_mat()

        self.caption = caption
        self.size = np.array(size)
        self.width, self.height = self.size
        self.center = self.size / 2

        self.hex_radius = hex_radius

        self.hex_map = hx.HexMap()
        self.max_coord = 11 # This is the hex radius

        self.rad = ClampedInteger(3, 1, 5)

        # self.selected_hex_image = make_hex_surface(
        #         (128, 128, 128, 160),
        #         self.hex_radius,
        #         (255, 255, 255),
        #         hollow=True)

        hx.set_orientation(self.orient)

        self.selection_type = CyclicInteger(3, 0, 3)
        self.clicked_hex = np.array([0, 0, 0])

        # Get all possible coordinates within `self.max_coord` as radius.
        spiral_coordinates = hx.get_spiral(np.array((0, 0, 0)), 1, self.max_coord)

        # Convert `spiral_coordinates` to axial coordinates
        hexes = {}
        axial_coordinates = hx.cube_to_axial(spiral_coordinates)

        for i, axial in enumerate(axial_coordinates):
            hex_color = self.color_palette[0]
            hexes[radial_to_irl_map[i]] = ExampleHex(axial, hex_color, hex_radius)

        self.hex_map = hexes

        for i, hexagon in enumerate(list(self.hex_map.values())):
            hexagon.ring = int(np.max(abs(hexagon.cube_coordinates)))

        # self.banner_coords = get_banner_loc(self.hex_map, self.max_coord)
        # self.hourglass = HourGlass(self.hex_map, self.max_coord)

        # pygame specific variables
        self.main_surf = None
        self.font = None
        self.clock = None
        self.init_pg()

        # specific to expanse animation
        self.frontline_ids = set()
        self.candidate_ids = set()

        self.color_bins = {}
        for i in range(len(self.color_palette)):
            if i == 0:
                self.color_bins[i] = set(range(397))
            else:
                self.color_bins[i] = set()

    def update_sim(self):
        state = np.zeros((397,3), dtype=int)
        state = self.expanse.update(state)
        state = self.clock_animation.update(state)
        state = np.clip(state, 0, 255)
        
        for pix_id, color in enumerate(state):
            self.hex_map[pix_id].change_color(color)

    def init_pg(self):
        pg.init()
        self.main_surf = pg.display.set_mode(self.size)
        self.main_surf.fill('black')
        pg.display.set_caption(self.caption)

        pg.font.init()
        self.font = pg.font.SysFont("Arial", 14, True)
        self.clock = pg.time.Clock()

    def handle_events(self):
        running = True
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    running = False

        return running

    def main_loop(self):
        running = self.handle_events()

        return running
    
    def draw(self):
        # show all hexes
        hexagons = list(self.hex_map.values())
        hex_positions = np.array([hexagon.get_draw_position() for hexagon in hexagons])
        sorted_indexes = np.argsort(hex_positions[:, 1])

        # draws colored hex
        for index in sorted_indexes:
            self.main_surf.blit(hexagons[index].image, hex_positions[index] + self.center)


        # # draw numbers on the hexes
        # # print("num hex ", len(list(self.hex_map.values())))
        # for i, hexagon in self.hex_map.items():
        #     text = self.font.render(str(i), False, (0, 0, 0))
        #     text.set_alpha(160)
        #     text_pos = hexagon.get_position() + self.center
        #     text_pos -= (text.get_width() / 2, text.get_height() / 2)
        #     self.main_surf.blit(text, text_pos)

        # Update screen at 10 frames per second
        pg.display.update()
        self.clock.tick(10)

    def draw_hex(self, hexagon):
        self.main_surf.blit(self.selected_hex_image, hexagon.get_draw_position() + self.center)

    def quit_app(self):
        pg.quit()
        raise SystemExit

def diplay_leds(hex_map_obj):
    from rpi_ws281x import PixelStrip, Color
    # LED strip configuration:
    LED_COUNT = 397        # Number of LED pixels.
    LED_PIN = 18          # GPIO pin connected to the pixels (18 uses PWM!).
    # LED_PIN = 10        # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
    LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
    LED_DMA = 10          # DMA channel to use for generating signal (try 10)
    LED_BRIGHTNESS = 100  # Set to 0 for darkest and 255 for brightest
    LED_INVERT = False    # True to invert the signal (when using NPN transistor level shift)
    LED_CHANNEL = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()

    color = Color(255,0,0)
    wait_ms = 50 
    for i, hexagon in enumerate(list(hex_map_obj.hex_map.values())):
        if hexagon.value:
            strip.setPixelColor(hexagon.value, color)
            strip.show()
            time.sleep(wait_ms / 1000.0)


if __name__ == '__main__':    
    example_hex_map = ExampleHexMap()

    if True:
        # print("num hex ", len(list(example_hex_map.hex_map.values())))
        while example_hex_map.main_loop():
            example_hex_map.update_sim()
            example_hex_map.draw()
    else:
        display_leds(example_hex_map)


    example_hex_map.quit_app()
