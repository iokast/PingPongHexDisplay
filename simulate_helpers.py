import numpy as np
import pygame as pg

import hexy as hx
import time
from text_for_hex import digits
import random

DIR = {'SE' : np.array((1, -1)).T,
       'SW' : np.array((0, -1)).T,
       'W' : np.array((-1, 0)).T,
       'NW' : np.array((-1, 1)).T,
       'NE' : np.array((0, 1)).T,
       'E' : np.array((1, 0)).T}

# DIR = {'SE' : np.array((1, 0, -1)),
#         'SW' : np.array((0, 1, -1)),
#         'W' : np.array((-1, 1, 0)),
#         'NW' : np.array((-1, 0, 1)),
#         'NE' : np.array((0, -1, 1)),
#         'E' : np.array((1, -1, 0))}

def make_hex_surface(color, radius, border_color=(100, 100, 100), border=True, hollow=False):
    """
    Draws a hexagon with gray borders on a pygame surface.
    :param color: The fill color of the hexagon.
    :param radius: The radius (from center to any corner) of the hexagon.
    :param border_color: Color of the border.
    :param border: Draws border if True.
    :param hollow: Does not fill hex with color if True.
    :return: A pygame surface with a hexagon drawn on it
    """
    angles_in_radians = np.deg2rad([60 * i + 30 for i in range(6)])
    x = radius * np.cos(angles_in_radians)
    y = radius * np.sin(angles_in_radians)
    points = np.round(np.vstack([x, y]).T)

    sorted_x = sorted(points[:, 0])
    sorted_y = sorted(points[:, 1])
    minx = sorted_x[0]
    maxx = sorted_x[-1]
    miny = sorted_y[0]
    maxy = sorted_y[-1]

    sorted_idxs = np.lexsort((points[:, 0], points[:, 1]))

    surf_size = np.array((maxx - minx, maxy - miny)) * 2 + 1
    center = surf_size / 2
    surface = pg.Surface(surf_size)
    surface.set_colorkey((0, 0, 0))
    if np.array_equal(color, np.array([0,0,0])):
        color = np.array([1,1,1])

    # Set alpha if color has 4th coordinate.
    if len(color) >= 4:
        surface.set_alpha(color[-1])

    # fill if not hollow.
    if not hollow:
        # pg.draw.polygon(surface, color, points + center, 0)
        pg.draw.circle(surface, color, center, (maxx - minx) /2)


    points[sorted_idxs[-1:-4:-1]] += [0, 1]
    # # if border is true or hollow is true draw border.
    # if border or hollow:
    #     pg.draw.lines(surface, border_color, True, points + center, 1)

    return surface


class ExampleHex(hx.HexTile):
    def __init__(self, axial_coordinates, color, radius):
        self.axial_coordinates = np.array([axial_coordinates])
        self.cube_coordinates = hx.axial_to_cube(self.axial_coordinates)
        self.position = hx.axial_to_pixel(self.axial_coordinates, radius)
        self.color = color
        self.radius = radius
        self.image = make_hex_surface(color, radius)
        self.value = None
        self.rgb1 = [0, 50, 100]
        self.rgb2 = [0, 220, 220]

        # print(self.position)

    def set_value(self, value):
        self.value = value

    def get_draw_position(self):
        """
        Get the location to draw this hex so that the center of the hex is at `self.position`.
        :return: The location to draw this hex so that the center of the hex is at `self.position`.
        """
        draw_position = self.position[0] - [self.image.get_width() / 2, self.image.get_height() / 2]
        return draw_position

    def get_position(self):
        """
        Retrieves the location of the center of the hex.
        :return: The location of the center of the hex.
        """
        return self.position[0]

    def change_color(self, color):
        new_color = np.array(color)
        self.color = new_color.astype(int)
        self.image = make_hex_surface(self.color, self.radius)

    def change_color_fixed(self, color):
        self.color = np.clip(self.color + color, 0, 255)
        self.image = make_hex_surface(self.color, self.radius)

def get_banner_loc(hexmap, radius, from_top=1):
    banner_coords = np.zeros((5, 2 * radius + 1, 2), dtype=int)
    banner_coords[:, :, 0] = range(-radius, radius+1)
    banner_coords[:, radius:, 1] = np.array([range(from_top - radius, from_top - radius + 5),]*(radius+1)).transpose()
    rows = []
    for i in range(5):
        max = banner_coords[i, radius, 1]
        rows.append(range(radius + max, max, -1))
    banner_coords[:, :radius, 1] = np.array(rows)

    return banner_coords

class TimeDisp:
    def __init__(self):
        self.update_time_mat()

    def is_new_time(self):
        curr_tm = time.localtime()
        if curr_tm.tm_min != self.m2:
            return True

        return False

    def update_time_mat(self):
        curr_time = time.localtime()
        self.h1 = int(curr_time.tm_hour / 10)
        self.h2 = int(curr_time.tm_hour % 10)
        self.m1 = int(curr_time.tm_min / 10)
        self.m2 = int(curr_time.tm_min % 10)

        space = np.zeros((5, 1))
        colon = np.array([[0], [0], [1], [0], [1]])
        self.time_mat = np.hstack((digits[self.h1], space,
                                   digits[self.h2], space, colon, space,
                                   digits[self.m1], space,
                                   digits[self.m2])).astype(int)

        return self.time_mat

class HourGlass():
    def __init__(self, hex_map, max_coord):
        self.hex_map = hex_map
        self.max_coord = max_coord
        self.last_sec = time.localtime().tm_sec
        self.stationary = set()
        self.moving = []
        self.purge = []
        self.color = np.array([200, 100, 100])

    def update_colors(self):
        i = 0
        while i < len(self.moving):
            old_coords = np.array(self.moving[i])
            new_coords = np.array(self.move(old_coords))
            if np.array_equal(new_coords, old_coords):
                self.stationary.add(tuple(new_coords))
                self.moving.pop(i)
            else:
                self.moving[i] = new_coords
                self.hex_map[new_coords][0].change_color_fixed(self.color)
                self.hex_map[old_coords][0].change_color_fixed((self.color/2).astype(int))
                i += 1

        for coords in self.stationary:
            self.hex_map[np.array(coords)][0].change_color_fixed(self.color)

        i = 0
        while i < len(self.purge):
            old_coords = np.array(self.purge[i])
            new_coords = np.array(self.move(old_coords))
            if np.array_equal(new_coords, old_coords):
                self.purge.pop(i)
            else:
                self.purge[i] = new_coords
                self.hex_map[new_coords][0].change_color_fixed(self.color)
                i += 1


        curr_time = time.localtime()
        if curr_time.tm_sec != self.last_sec:
            if curr_time.tm_sec == 0:
                self.purge = self.moving + list(self.stationary)
                self.moving = []
                self.stationary = set()
            self.last_sec = curr_time.tm_sec
            self.moving.append(np.array([0, -self.max_coord]))

    def move(self, coords):
        d = coords + DIR['NE']
        d_valid = str(int(d[0])) + ',' + str(int(d[1])) in self.hex_map.keys() and tuple(d) not in self.stationary

        if d_valid:
            return d

        l = coords + DIR['NW']
        l_valid = str(int(l[0])) + ',' + str(int(l[1])) in self.hex_map.keys() and tuple(l) not in self.stationary

        r = coords + DIR['E']
        r_valid = str(int(r[0])) + ',' + str(int(r[1])) in self.hex_map.keys() and tuple(r) not in self.stationary

        possible = []
        if l_valid:
            possible.append(l)
        if r_valid:
            possible.append(r)
        if possible:
            return random.choice(possible)
        else:
            return coords