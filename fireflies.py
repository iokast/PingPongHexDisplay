import numpy as np
from hex_mask import *
import random
import pplight_rain as ppl

class Fireflies():
    def __init__(self, ff_count, tail_len, color_list):
        self.fflist = []
        color_i = 0
        for i in range(ff_count):
            self.fflist.append(Firefly(random.randint(0, 396), tail_len, color_list[color_i]))
            color_i = (color_i + 1) % len(color_list)

    def add_ff(self,):
        # use this to add fireflies after starting
        return
    def destroy_ff(self,):
        # delete a firefly, maybe not necesary
        return
    def update(self):
        for ff in self.fflist:
            ff.move()
        self.render()

    def render(self):
        for ff in self.fflist:
            for i, pid in enumerate(ff.pixel_ids):
                ppl.set_pixel_color(pid, ff.colors[i])
        ppl.refresh_display()


class Firefly():
    def __init__(self, pixel_id, tail_len, color):
        self.pixel_ids = [pixel_id]
        self.tail_len = tail_len
        self.adjacency = adjacency[pixel_id]
        # self.adjacency = [x for x in adjacency[pixel_id] if x is not None] # filter Nones from adjacency list
        
        colors = np.array([[g[int(color[0]*i/tail_len)], 
                            g[int(color[1]*i/tail_len)], 
                            g[int(color[2]*i/tail_len)]] for i in range(tail_len, -1, -1)], dtype=int)
        color_32 = (colors[:, 1] << 16) + (colors[:, 0] << 8) + colors[:, 2]
        self.colors = color_32.tolist()
        
    def move(self):
        # select an adjacent pixel_id that isn't adjacent to the previous TODO: make sure can't colide with other
        isNone = True
        print(self.adjacency)
        while isNone:
            adj_i = random.randint(0, 5)
            new_pixel = self.adjacency[adj_i]
            if new_pixel is not None:
                isNone = False
        
        # update pixel list and adjacency list
        self.pixel_ids.insert(0, new_pixel)
        if len(self.pixel_ids) > self.tail_len:
            # remove end of tail and revert color
            ppl.set_pixel_color(self.pixel_ids.pop(), 0)
            
            # get pixel color. If it is equal to last color on color list, black out

        # get new adjacency list, removing previously visited and its neighbors.
        last = (adj_i + 3) % 6
        self.adjacency = adjacency[new_pixel]
##        self.adjacency[last] = None
##        self.adjacency[(last - 1) % 6] = None
##        self.adjacency[(last + 1) % 6] = None
        
