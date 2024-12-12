import numpy as np
from hex_mask import *
from copy import deepcopy
import random

class Expanse:
    def __init__(self, color_palette):
        self.color_palette
        self.set_palette(color_palette)

        self.color_bins = {}
        for i in range(len(self.color_palette)):
            if i == 0:
                self.color_bins[i] = set(range(397))
            else:
                self.color_bins[i] = set()
        
    def set_palette(self, color_palette):
        for c in color_palette:
            self.color_palette.append((int(c[1]) << 16) + (int(c[0]) << 8) + int(c[2]))

    def update(self, strip):
        num_bins = len(self.color_bins)
        for i, bin in enumerate(self.color_bins.values()):
            # check if there are sufficient pixels in current bin and none in the next, if so move a random pixel to the next bin
            seed_count = 1
            if len(bin) > 0 and len(self.color_bins[(i+1) % num_bins]) < 10:
                for j in range(seed_count):
                    seed_pixel = random.sample(bin, 1)[0]
                    # check that it is only touchin
                    #  current bins colors
                    isolated = True
                    for adj_id in led_adjacency[seed_pixel]:
                        if adj_id not in bin: #.union(self.color_bins[(i-1) % num_bins], self.color_bins[(i-2) % num_bins]):
                            isolated = False
                    if isolated:
                        self.color_bins[(i+1) % num_bins].add(seed_pixel)
                        self.color_bins[i].remove(seed_pixel)
                        self.hex_map[seed_pixel].change_color(self.color_palette[i])

                        # # mark seed pixel for debugging
                        # hexagon = self.hex_map[seed_pixel]
                        # text = self.font.render('S', False, (0, 0, 0))
                        # text.set_alpha(160)
                        # text_pos = hexagon.get_position() + self.center
                        # text_pos -= (text.get_width() / 2, text.get_height() / 2)
                        # self.main_surf.blit(text, text_pos)
                        # pg.display.update()
                        # self.clock.tick(2)
            
            move_to_next_bin = set()
            
            # iterate through pixels in bin
            for pix_id in bin:
                adjacent_count = 0
                not_frontline = True
                for adj_id in led_adjacency[pix_id]:
                    if adj_id in self.color_bins[(i+1) % num_bins].union(self.color_bins[(i+2) % num_bins], self.color_bins[(i+3) % num_bins]):
                        adjacent_count += 1
                    if adj_id in self.color_bins[(i-2) % num_bins]:
                        not_frontline = False
                if not_frontline and random.random() < (adjacent_count / 10): # Make proportional to max possible adjacent
                    move_to_next_bin.add(pix_id)
                    self.hex_map[pix_id].change_color(self.color_palette[i])
            
            # move selected pixels from current bin to next bin
            self.color_bins[i] -= move_to_next_bin
            self.color_bins[(i+1) % num_bins].update(move_to_next_bin)
        
        
        
        for i in range(1, len(self.layers)): # for each ring
            tail_len = int(self.tail + self.tail_multiplier * i)
            for j in range(0, tail_len): # for each pixel in a segment  TODO: this produces weird colors with tail + i, why?
                j = j % len(self.layers[i])
                k = (j + int(len(self.layers[i])/2)) % len(self.layers[i])

                # make opposing streamers at pixel j and k
                strip.set_pixel_color(self.layers[i][j], self.layer_colors_all[i][j])
                strip.set_pixel_color(self.layers[i][k], self.layer_colors_all[i][j])
            
            self.layers[i].append(self.layers[i].pop(0))

        strip.refresh_display()
        