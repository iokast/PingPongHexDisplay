import numpy as np
import gif2numpy
from hex_mask import *
import argparse
import time
import os
import sys
import select
import tty
import termios
import cv2
import random
import fireflies
from copy import deepcopy

class Spin:
    def __init__(self):
        self.bg_color = np.array([0,0,0]).astype(int)
        self.dot_color = np.array([255,255,255]).astype(int)
        self.tail = 1
        self.tail_multiplier = 2
        layer_colors_base = deepcopy(hazy_p)

        for i in range(len(layer_colors_base)):
            for j in range(3):
                layer_colors_base[i][j] = g[layer_colors_base[i][j]]

        self.layer_colors_base = np.array(layer_colors_base).astype(int)

        self.layer_colors_all =  [[] for _ in range(12)]
        
        # generate cube coords for each layer/ring
        self.layers = []
        for i in range(12):
            q = [*range(i, -i, -1)] + [-i] * i + [*range(-i, i, 1)] + [i] * i
            r = q[2*i:] + q[:2*i]
            s = r[2*i:] + r[:2*i]
            self.layers.append(list(zip(r, q, s))) # qsr order affects rotation start and direction
        
        # for each cube coord assign the pixel id
        for i, coords in enumerate(cube_coords):
            layer_id = max(abs(coords))
            for j in range(len(self.layers[layer_id])):
                if tuple(coords.tolist()) == self.layers[layer_id][j]:
                    self.layers[layer_id][j] = i
                    
    def update(self, strip):
        for i in range(1, len(self.layers)): # for each ring
            tail_len = int(self.tail + self.tail_multiplier * i)
            for j in range(0, tail_len): # for each pixel in a segment  TODO: this produces weird colors with tail + i, why?
                # c = self.dot_color
                j = j % len(self.layers[i])
                k = (j + int(len(self.layers[i])/2)) % len(self.layers[i])
                
                if len(self.layer_colors_all[i]) < tail_len:
                    c = (self.bg_color + (self.layer_colors_base[i, :] * j - self.bg_color) / tail_len).astype(int) # TODO: loop length replacing tail fixes the todo a few lines above
                    self.layer_colors_all[i].append((int(c[1]) << 16) + (int(c[0]) << 8) + int(c[2]))

                strip.set_pixel_color(self.layers[i][j], self.layer_colors_all[i][j])
                strip.set_pixel_color(self.layers[i][k], self.layer_colors_all[i][j])
            
            self.layers[i].append(self.layers[i].pop(0))

        strip.refresh_display()
        