import numpy as np
from hex_mask import clock_positions, digits, led_adjacency, clock_dial, cube_coords
import random
from datetime import datetime



class Clock:
    def __init__(self, color, alpha):
        self.alpha = alpha
        self.original_color = color
        self.set_palette(color)

        self.clock_type = 3
        self.clock_locs_dict = clock_positions[self.clock_type]
        self.number_of_digits = 3
        self.digits = digits[self.clock_type]
        self.color_type = [0, 3] # [current type, total types]

        self.current_direction = 2  # Start moving in the 4 o'clock direction

        self.tail = 1
        self.tail_multiplier = 2

        # generate cube coords for each layer/ring
        self.layers = []
        for i in range(12):
            q = [*range(i, -i, -1)] + [-i] * i + [*range(-i, i, 1)] + [i] * i
            r = q[2*i:] + q[:2*i]
            s = r[2*i:] + r[:2*i]
            self.layers.append(list(zip(r, q, s))) 
        
        # for each cube coord assign the pixel id
        for i, coords in enumerate(cube_coords):
            layer_id = max(abs(coords))
            for j in range(len(self.layers[layer_id])):
                if tuple(coords.tolist()) == self.layers[layer_id][j]:
                    self.layers[layer_id][j] = i

    def set_palette(self, color):
        self.original_color = color
        self.color = (np.asarray(color) * self.alpha).astype(int)

    def set_brightness(self, brightness):
        self.alpha = brightness
        self.color = (np.asarray(self.original_color) * self.alpha).astype(int)

    def change_type(self):
        self.clock_type = (self.clock_type + 1) % len(clock_positions)
        self.clock_locs_dict = clock_positions[self.clock_type]
        self.digits = digits[self.clock_type]

    def get_color(self, curr_color):        
        # additive
        if self.color_type[0] == 0:
            return curr_color + self.color

        # solid
        if self.color_type[0] == 1:
            return self.color
        
        # negative
        if self.color_type[0] == 2:
            return (np.array([255,255,255]) - curr_color) * self.alpha
    
    def change_color_type(self):
        self.color_type[0] = (self.color_type[0] + 1) % self.color_type[1]

    def can_move(self, direction):
        """
        Check if all clock pixels (digits and colon) can move in the given direction.
        """
        curr_loc = self.clock_locs_dict[self.number_of_digits][:self.number_of_digits]
        edge_pixels = [curr_loc[0][0], curr_loc[0][1], curr_loc[0][-2], curr_loc[0][-6],  # left digit corners
                       curr_loc[-1][1], curr_loc[-1][2], curr_loc[-1][-2], curr_loc[-1][-4]]    # right digit corners


        # Check digits
        for pixel_id in edge_pixels:
            if led_adjacency[pixel_id][direction] is None:
                return False
            
        return True
    
    def find_bounce_direction(self):
        """
        Calculate the new bounce direction by changing direction by 2 steps clockwise or counterclockwise.
        Avoids the opposite direction.
        """
        possible_directions = [2, -2, 1, -1, 3]
        
        for dir in possible_directions:
            new_dir = (self.current_direction + dir) % 6
            if self.can_move(new_dir):
                return new_dir
    
    def move_clock(self):
        """
        Move the clock in the current direction. If blocked, find a bounce direction.
        """
        if not self.can_move(self.current_direction):
            self.current_direction = self.find_bounce_direction()  # Bounce to a new direction

        # Update positions for digits
        curr_clock_loc = np.array(self.clock_locs_dict[self.number_of_digits][:self.number_of_digits])
        new_clock_loc = []
        for pixel_id in curr_clock_loc.flatten():
            try:
                new_pixel = led_adjacency[pixel_id][self.current_direction]
            except:
                new_pixel = 0
            new_clock_loc.append(new_pixel)
        self.clock_locs_dict[self.number_of_digits][:self.number_of_digits] = list(np.array(new_clock_loc).reshape(curr_clock_loc.shape))

        # Update positions for colon
        new_clock_colon = []
        for pixel_id in self.clock_colon_dict[self.number_of_digits][self.number_of_digits]:
            new_pixel = led_adjacency[pixel_id][self.current_direction]
            new_clock_colon.append(new_pixel)
        self.clock_colon_dict[self.number_of_digits][self.number_of_digits] = new_clock_colon        

    def update(self, state):
        now = datetime.now()
        current_time = str(now.strftime("%I%M"))
        
        if int(current_time[0]) == 0:
            self.number_of_digits = 3
            current_time = current_time[1:]
        else:
            self.number_of_digits = 4

        # self.move_clock()

        clock_loc = self.clock_locs_dict[self.number_of_digits][:self.number_of_digits]
        
        # draw digits
        for i in range(len(clock_loc)):
            mask = self.digits[int(current_time[i])]
            on_pix = list(np.where(mask, clock_loc[i], None))
            on_pix = [x for x in on_pix if x is not None]

            for pix_id in list(on_pix):
                state[pix_id, :] = self.get_color(state[pix_id, :])
        # draw colon
        for pix_id in self.clock_locs_dict[self.number_of_digits][self.number_of_digits]:
            state[pix_id, :] = self.get_color(state[pix_id, :])

        return state.astype(int)
    
    def update_2(self, strip=None, hex_map=None):
        
        state = np.zeros((397,3), dtype=int)

        now = datetime.now()
        current_time = str(now.strftime("%I%M%S"))
        
        hours = int(now.strftime("%I"))
        minutes = int(now.strftime("%M"))
        seconds = int(now.strftime("%S"))
        
        if int(current_time[0]) == 0:
            self.number_of_digits = 3
            current_time = current_time[1:]
        else: 
            self.number_of_digits = 4

        for pix_id in list(clock_dial):
            if strip:
                # strip.set_pixel_color(pix_id, self.color_bit)
                state[pix_id, :] = state[pix_id, :]  + self.color # - [100,100,100]
            elif hex_map:
                # hex_map[pix_id].change_color(self.color)
                state[pix_id, :] = state[pix_id, :] + self.color # - [100,100,100]

        # for pix_id in self.layers[10][seconds]: # for each ring
            # tail_len = int(self.tail + self.tail_multiplier * i)
            # for j in range(0, tail_len): # for each pixel in a segment  TODO: this produces weird colors with tail + i, why?
            #     j = j % len(self.layers[i])
            #     k = (j + int(len(self.layers[i])/2)) % len(self.layers[i])

                # # make opposing streamers at pixel j and k
                # strip.set_pixel_color(self.layers[i][k], self.color)
            
            # self.layers[i].append(self.layers[i].pop(0))

        second_hand = int(len(self.layers[10]) * ((seconds + 20) % 60)/60) 
        pix_id = self.layers[10][second_hand]    
        for pix_id in [pix_id, pix_id] + led_adjacency[pix_id]:
            if strip:
                # strip.set_pixel_color(pix_id, self.color_bit)
                state[pix_id, :] = state[pix_id, :] + self.color
            elif hex_map:
                # hex_map[pix_id].change_color(self.color)
                state[pix_id, :] = state[pix_id, :] + self.color

        minute_hand = int(len(self.layers[6]) * ((minutes + 20) % 60)/60) 
        pix_id = self.layers[6][minute_hand]    
        for pix_id in [pix_id, pix_id] + led_adjacency[pix_id]:
            if strip:
                # strip.set_pixel_color(pix_id, self.color_bit)
                state[pix_id, :] = state[pix_id, :] + self.color
            elif hex_map:
                # hex_map[pix_id].change_color(self.color)
                state[pix_id, :] = state[pix_id, :] + self.color

        hour_hand = int(len(self.layers[2]) * ((hours + 4) % 12)/12) 
        pix_id = self.layers[2][hour_hand]
        for pix_id in [pix_id, pix_id] + led_adjacency[pix_id]:
            if strip:
                # strip.set_pixel_color(pix_id, self.color_bit)
                state[pix_id, :] = state[pix_id, :] + self.color
            elif hex_map:
                # hex_map[pix_id].change_color(self.color)
                state[pix_id, :] = state[pix_id, :] + self.color


                
        return state.astype(int)
        

        