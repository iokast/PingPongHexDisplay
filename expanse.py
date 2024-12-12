import numpy as np
from hex_mask import led_adjacency
import random

class Expanse:
    def __init__(self, color_palette, alpha):
        self.alpha = alpha
        self.set_palette(color_palette)
        self.state = np.zeros((397,3), dtype=int)

        self.color_bins = {}
        for i in range(len(self.color_palette)):
            if i == 0:
                self.color_bins[i] = set(range(397))
            else:
                self.color_bins[i] = set()
        
        self.spread_likelihood = 8
        
    def set_palette(self, color_palette):
        # cp_arr = np.asarray(color_palette)
        # cp_arr = np.column_stack((cp_arr, np.full(cp_arr.shape[0])))
        self.color_palette = (np.asarray(color_palette) * self.alpha).astype(int)
        # self.color_palette_bit = []
        # for c in color_palette:
        #     self.color_palette_bit.append((int(c[3]) << 24) (int(c[1]) << 16) + (int(c[0]) << 8) + int(c[2]))

    def update(self, strip=None, hex_map=None):
        num_bins = len(self.color_bins)
        led_adj_dict = {idx: set(adj) for idx, adj in enumerate(led_adjacency) if adj}  # Convert list of lists to dict of sets

        # Precompute bin lengths
        bin_lengths = {i: len(bin) for i, bin in self.color_bins.items()}

        # Precompute unions for adjacent bins
        bin_unions = {
            i: self.color_bins[(i + 1) % num_bins].union(
                self.color_bins[(i + 2) % num_bins], self.color_bins[(i + 3) % num_bins]
            )
            for i in range(num_bins)
        }

        for i, bin in self.color_bins.items():
            seed_count = 10

            # Handle seed pixel movement to the next bin
            if bin_lengths[i] > 0 and bin_lengths[(i + 1) % num_bins] < 20:
                seed_pixels = random.sample(bin, min(seed_count, bin_lengths[i]))
                isolated_pixels = {
                    p for p in seed_pixels
                    if all(adj_id in bin for adj_id in led_adj_dict.get(p, []))
                }
                for seed_pixel in isolated_pixels:
                    self.color_bins[(i + 1) % num_bins].add(seed_pixel)
                    bin.remove(seed_pixel)
                    if strip:
                        # strip.set_pixel_color(seed_pixel, self.color_palette_bit[i])
                        self.state[seed_pixel] = self.color_palette_bit[i]
                    elif hex_map:
                        # hex_map[seed_pixel].change_color(self.color_palette[i])
                        self.state[seed_pixel, :] = self.color_palette[i]
                    

            # Prepare to move pixels to the next bin
            move_to_next_bin = set()

            for pix_id in bin:
                adjacent_count = sum(
                    adj_id in bin_unions[i] for adj_id in led_adj_dict.get(pix_id, [])
                )
                not_frontline = all(
                    adj_id not in self.color_bins[(i - 2) % num_bins]
                    for adj_id in led_adj_dict.get(pix_id, [])
                )

                if not_frontline and random.random() > ((adjacent_count) / self.spread_likelihood):
                    move_to_next_bin.add(pix_id)
                    if strip:
                        # strip.set_pixel_color(pix_id, self.color_palette_bit[i])
                        self.state[pix_id, :] = self.color_palette[i]
                    elif hex_map:
                        # hex_map[pix_id].change_color(self.color_palette[i])
                        self.state[pix_id, :] = self.color_palette[i]

            # Move pixels to the next bin
            bin.difference_update(move_to_next_bin)
            self.color_bins[(i + 1) % num_bins].update(move_to_next_bin)

        return self.state.astype(int)

        # self.spread_likelihood = ((self.spread_likelihood + 1) % self.spread_likelihood) + 6

        # if strip:
        #     strip.refresh_display()
        

        