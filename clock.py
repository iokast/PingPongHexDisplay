import numpy as np
from hex_mask import clock_positions, clock_positions_slant, digits, digits_slant
import random
from datetime import datetime



class Clock:
    def __init__(self, color, alpha):
        self.alpha = alpha
        self.original_color = color
        self.set_palette(color)
        self.clock_loc_4 = np.array(clock_positions[4][:4])
        self.clock_colon_4 = np.array(clock_positions[4][4])
        self.clock_loc_3 = np.array(clock_positions[3][:3])
        self.clock_colon_3 = np.array(clock_positions[3][3])
        self.digits = digits

        self.color_bins = {}
        for i in range(len(self.color)):
            if i == 0:
                self.color_bins[i] = set(range(397))
            else:
                self.color_bins[i] = set()
        
        self.spread_likelihood = 8
        
    def set_palette(self, color):
        self.original_color = color
        self.color = (np.asarray(color) * self.alpha).astype(int)
        # self.color_bit = (int(self.color[1]) << 16) + (int(self.color[0]) << 8) + int(self.color[2])
        # self.off  = [0,0,0]
        # self.off_bit = (int(self.off[1]) << 16) + (int(self.off[0]) << 8) + int(self.off[2])

    def set_brightness(self, brightness):
        self.alpha = brightness
        self.color = (np.asarray(self.original_color) * self.alpha).astype(int)

    def update(self, strip=None, hex_map=None):
        
        state = np.zeros((397,3), dtype=int)

        now = datetime.now()
        current_time = str(now.strftime("%I%M"))
        
        if int(current_time[0]) == 0:
            clock_loc = self.clock_loc_3
            clock_colon = self.clock_colon_3
            current_time = current_time[1:]
        else:
            clock_loc = self.clock_loc_4
            clock_colon = self.clock_colon_4

        for i in range(len(clock_loc)):
            mask = self.digits[int(current_time[i])]
            on_pix = list(np.where(mask, clock_loc[i], None))
            on_pix = [x for x in on_pix if x is not None]

            for pix_id in list(on_pix):
                if strip:
                    # strip.set_pixel_color(pix_id, self.color_bit)
                    state[pix_id, :] = state[pix_id, :] + self.color
                elif hex_map:
                    # hex_map[pix_id].change_color(self.color)
                    state[pix_id, :] = state[pix_id, :] + self.color
        for pix_id in clock_colon:
            if strip:
                # strip.set_pixel_color(pix_id, self.color_bit)
                state[pix_id, :] = state[pix_id, :] + self.color
            elif hex_map:
                # hex_map[pix_id].change_color(self.color)
                state[pix_id, :] = state[pix_id, :] + self.color

                
        return state.astype(int)

        # if strip:
        #     strip.refresh_display()
        

        