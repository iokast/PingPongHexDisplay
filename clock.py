import numpy as np
from hex_mask import *
import random
import time

class Clock():
    def __init__(self, start_pos=[38, 42, 48,52], colon_pos=[112,66]):
        self.hhmm_ids = np.zeros((4, 5, 3), dtype=int)
        self.hhmm_ids[0, 0, 1] = start_pos[0]
        self.hhmm_ids[1, 0, 1] = start_pos[1]
        self.hhmm_ids[2, 0, 1] = start_pos[2]
        self.hhmm_ids[3, 0, 1] = start_pos[3]
        self.colon_pos = colon_pos

        for i in range(self.hhmm_ids.shape[0]):
            for j in range(5):
                self.hhmm_ids[i, j, 0] = adjacency[self.hhmm_ids[i, j, 1], 4]  # [None,None,2,6,0,None]
                self.hhmm_ids[i, j, 2] = adjacency[self.hhmm_ids[i, j, 1], 2]
                if j < 4:
                    self.hhmm_ids[i, j+1, 1] = adjacency[self.hhmm_ids[i, j, 1], 3]
                
        self.prev_minute = None

    def update_clock(self, color=None, transparent=True):
        curr_time = time.localtime()

        # update clock mask if minutes have changed
        if self.prev_minute is None or curr_time.tm_min % 10 != self.prev_minute: # check if time has changed
            hour = curr_time.tm_hour % 12
            if hour == 0: hour = 12  # show 12 o'clock instead of 00
            hhmm = [int(hour / 10), int(hour % 10),
                    int(curr_time.tm_min / 10), int(curr_time.tm_min % 10)]
            self.mask = (np.array([digits[hhmm[0]], digits[hhmm[1]], digits[hhmm[2]], digits[hhmm[3]]]) \
                * self.hhmm_ids).flatten()
            self.mask = self.mask[self.mask >= 0]
            self.mask = np.concatenate((self.mask, self.colon_pos), axis=None)  # add pixel ids for hh:mm colon

        if color is None:
            return set(self.mask)

        # update pixels with clock mask
        for pixel_id in self.mask:
            if transparent:
                self.frame[pixel_id, :3] = np.clip(self.frame[pixel_id, :3] + color, 0, 255)
            else:
                self.frame[pixel_id, :3] = np.clip(color, 0, 255)