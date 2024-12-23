import numpy as np
from hex_mask import *
import random

class Fireflies():
    def __init__(self, ff_count, tail_len, color_list):
        self.fflist = []
        self.ff_count = ff_count
        self.tail_len = tail_len
        color_i = 0
        for i in range(self.ff_count):
            self.fflist.append(Firefly(random.randint(0, 396), self.tail_len, color_list[color_i]))
            color_i = (color_i + 1) % len(color_list)

    def add_ff(self,):
        # use this to add fireflies after starting
        return
    def destroy_ff(self,):
        # delete a firefly, maybe not necesary
        return
    def update(self, strip):
        for ff in self.fflist:
            ff.move(strip)
        self.render(strip)

    def set_palette(self, color_palette):
        self.fflist = []
        color_i = 0
        for i in range(self.ff_count):
            self.fflist.append(Firefly(random.randint(0, 396), self.tail_len, color_palette[color_i]))
            color_i = (color_i + 1) % len(color_palette)

    def render(self, strip):
        for ff in self.fflist:
            for i, pid in enumerate(ff.pixel_ids):
                strip.set_pixel_color(pid, ff.colors[-i-1])
        strip.refresh_display()


class Firefly():
    def __init__(self, pixel_id, tail_len, color):
        self.pixel_ids = [pixel_id]
        self.tail_len = tail_len
        self.adjacency = adjacency[pixel_id]
        # self.adjacency = [x for x in adjacency[pixel_id] if x is not None] # filter Nones from adjacency list
        color = [gamma_adj[color[0]], gamma_adj[color[1]], gamma_adj[color[2]]]
        colors = np.array([[color[0]*i/tail_len, 
                            color[1]*i/tail_len, 
                            color[2]*i/tail_len] for i in range(1, tail_len+1)], dtype=int)
        color_32 = (colors[:, 1] << 16) + (colors[:, 0] << 8) + colors[:, 2]
        self.colors = color_32.tolist()
        self.last_dir = random.randint(0, 5)
        
    def move(self, strip):
        # select an adjacent pixel_id that isn't adjacent to the previous TODO: make sure can't colide with other
        if self.adjacency[self.last_dir] is None:
            p0 = [0, .1, .2, .4, .2, .1]
        else:
            p0 = [.7, .1, .05, 0, .05, .1]

        isNone = True
        while isNone:                
            prob = p0[-self.last_dir:] + p0[:-self.last_dir]
            curr_dir = np.random.choice([0, 1, 2, 3, 4, 5], 1, p=prob)[0]
            new_pixel = self.adjacency[curr_dir]
            if new_pixel is not None:
                isNone = False
                self.last_dir = curr_dir

        
        # update pixel list and adjacency list
        self.pixel_ids.insert(0, new_pixel)
        if len(self.pixel_ids) > self.tail_len:
            # remove end of tail and revert color
            # strip.set_pixel_color(self.pixel_ids.pop(), 0)
            self.pixel_ids.pop()
            
            # get pixel color. If it is equal to last color on color list, black out

        # get new adjacency list, removing previously visited and its neighbors.
        self.adjacency = adjacency[new_pixel]
        
