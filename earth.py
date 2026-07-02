import math
import os
import time

import numpy as np

from hex_mask import cartesian_coords


class Earth:
    """A readable, antialiased rotating globe rendered on the LED lattice."""

    CONTINENTS = (
        # North America
        ((-168, 72), (-150, 70), (-137, 60), (-128, 55), (-124, 48),
         (-125, 40), (-117, 32), (-107, 24), (-98, 19), (-90, 29),
         (-82, 25), (-80, 32), (-75, 39), (-66, 44), (-58, 52),
         (-68, 59), (-82, 63), (-96, 69), (-116, 72), (-140, 73)),
        # Alaska
        ((-179, 52), (-169, 72), (-143, 71), (-130, 59), (-145, 55),
         (-162, 57)),
        # Central America
        ((-106, 24), (-96, 18), (-89, 19), (-84, 10), (-78, 8),
         (-79, 14), (-88, 22), (-98, 27)),
        # South America
        ((-81, 12), (-72, 12), (-61, 7), (-50, 2), (-43, -8),
         (-35, -17), (-40, -25), (-49, -29), (-53, -42), (-67, -55),
         (-73, -43), (-70, -30), (-77, -18), (-80, -2)),
        # Europe and Asia
        ((-10, 36), (-9, 44), (-4, 50), (6, 54), (10, 61), (24, 71),
         (46, 70), (62, 76), (96, 77), (126, 71), (150, 61),
         (178, 52), (166, 45), (153, 47), (145, 39), (128, 35),
         (121, 23), (109, 20), (103, 8), (96, 6), (88, 22),
         (72, 25), (60, 30), (48, 29), (40, 40), (30, 42),
         (21, 36), (12, 42), (2, 43)),
        # Africa
        ((-17, 36), (-5, 37), (10, 36), (25, 32), (34, 29), (43, 12),
         (51, 10), (44, -12), (40, -23), (31, -34), (18, -35),
         (12, -27), (4, -20), (0, -5), (-10, 5), (-17, 18)),
        # Arabian peninsula
        ((34, 30), (48, 30), (57, 23), (51, 13), (43, 12), (36, 20)),
        # India and southeast Asia
        ((68, 25), (78, 30), (90, 23), (87, 9), (78, 7), (73, 17)),
        ((92, 22), (107, 23), (121, 16), (117, 5), (105, 8), (98, 14)),
        # Australia
        ((112, -11), (130, -12), (145, -10), (154, -21), (151, -38),
         (137, -35), (129, -43), (115, -35), (112, -24)),
        # Greenland
        ((-60, 82), (-35, 84), (-18, 76), (-28, 61), (-48, 59),
         (-62, 69)),
        # Major islands exaggerated for readability
        ((-10, 58), (-2, 59), (1, 51), (-6, 50)),                 # Britain
        ((45, -12), (51, -16), (49, -26), (44, -25)),            # Madagascar
        ((130, 34), (142, 46), (146, 42), (138, 32)),             # Japan
        ((95, 5), (119, 5), (128, -6), (111, -9), (99, -4)),     # Indonesia
        ((166, -34), (179, -39), (174, -47), (167, -45)),         # New Zealand
    )

    WATER_CUTOUTS = (
        ((-96, 63), (-84, 65), (-76, 58), (-82, 51), (-94, 54)),  # Hudson Bay
        ((-98, 30), (-82, 31), (-80, 23), (-90, 18), (-97, 22)),  # Gulf of Mexico
        ((-6, 37), (8, 44), (27, 41), (36, 35), (18, 31), (2, 35)),  # Mediterranean
        ((27, 47), (42, 47), (42, 41), (29, 41)),                 # Black Sea
    )

    def __init__(self, color_palette=None, alpha=1.0):
        self.brightness = alpha
        self.start_time = time.monotonic()
        self.rotation_seconds = float(os.environ.get(
            "PPL_EARTH_ROTATION_SECONDS", "120"
        ))

        coords = cartesian_coords.astype(float)
        self.y = coords[:, 0]
        self.x = coords[:, 1]
        self.center_x = (self.x.min() + self.x.max()) / 2.0
        self.center_y = (self.y.min() + self.y.max()) / 2.0
        self.radius = min(np.ptp(self.x), np.ptp(self.y)) * 0.43

        angles = np.arange(6, dtype=float) * math.pi / 3.0
        ring = np.column_stack((np.cos(angles), np.sin(angles))) * 0.34
        self.sample_offsets = np.vstack(([[0.0, 0.0]], ring))

        rng = np.random.default_rng(2026)
        self.star_progress = rng.random(18)
        self.star_y = rng.uniform(self.y.min() + 0.5, self.y.max() - 0.5, 18)
        self.star_arc_phase = rng.uniform(0.0, 2.0 * math.pi, 18)
        self.star_strength = rng.uniform(0.55, 1.0, 18)

    def set_palette(self, color_palette, alpha):
        self.brightness = alpha

    def set_brightness(self, brightness):
        self.brightness = brightness

    @staticmethod
    def _points_in_polygon(longitude, latitude, polygon):
        inside = np.zeros(longitude.shape, dtype=bool)
        x1, y1 = polygon[-1]
        for x2, y2 in polygon:
            crosses = ((y1 > latitude) != (y2 > latitude))
            edge_x = (x2 - x1) * (latitude - y1) / ((y2 - y1) + 1e-12) + x1
            inside ^= crosses & (longitude < edge_x)
            x1, y1 = x2, y2
        return inside

    def _land_mask(self, longitude, latitude):
        land = latitude < -68.0  # simplified Antarctica
        for polygon in self.CONTINENTS:
            land |= self._points_in_polygon(longitude, latitude, polygon)
        for polygon in self.WATER_CUTOUTS:
            land &= ~self._points_in_polygon(longitude, latitude, polygon)
        return land

    def _background(self, elapsed):
        state = np.tile(np.array([1.0, 2.0, 9.0]), (len(self.x), 1))
        width = np.ptp(self.x)
        progress = (
            self.star_progress - elapsed / self.rotation_seconds
        ) % 1.0
        star_x = self.x.min() + progress * width
        star_y = self.star_y + 0.30 * np.sin(
            progress * 2.0 * math.pi + self.star_arc_phase
        )

        dx = self.x[:, np.newaxis] - star_x[np.newaxis, :]
        dy = self.y[:, np.newaxis] - star_y[np.newaxis, :]
        coverage = np.exp(-(dx * dx + dy * dy) / (2.0 * 0.31 ** 2))

        # Fade at the horizontal edges so stars rotate cleanly out of sight
        # before wrapping around to the opposite side.
        edge_distance = np.minimum(progress, 1.0 - progress)
        edge_fade = np.clip(edge_distance / 0.055, 0.0, 1.0)
        twinkle = 0.72 + 0.18 * np.sin(
            elapsed / 3.5 + self.star_arc_phase
        )
        star_light = coverage * (
            self.star_strength * edge_fade * twinkle
        )[np.newaxis, :]
        brightness = np.clip(star_light.max(axis=1), 0.0, 1.0)
        star_color = np.array([145.0, 160.0, 205.0])
        state += brightness[:, np.newaxis] * star_color
        return state

    def update(self, state):
        elapsed = time.monotonic() - self.start_time
        output = self._background(elapsed)

        sample_x = self.x[:, np.newaxis] + self.sample_offsets[np.newaxis, :, 0]
        sample_y = self.y[:, np.newaxis] + self.sample_offsets[np.newaxis, :, 1]
        screen_x = (sample_x - self.center_x) / self.radius
        screen_y = (self.center_y - sample_y) / self.radius

        # Keep the rotational axis vertical so north remains straight up.
        globe_x = screen_x
        globe_y = screen_y
        radius_squared = globe_x * globe_x + globe_y * globe_y
        on_globe = radius_squared <= 1.0
        globe_z = np.sqrt(np.clip(1.0 - radius_squared, 0.0, 1.0))

        rotation = 2.0 * math.pi * (elapsed / self.rotation_seconds)
        longitude = np.degrees(np.arctan2(globe_x, globe_z) + rotation)
        longitude = (longitude + 180.0) % 360.0 - 180.0
        raw_latitude = np.degrees(np.arcsin(np.clip(globe_y, -1.0, 1.0)))
        # Orthographic projection crowds high latitudes toward the equator on
        # this tiny globe. Symmetrically expand them while keeping latitude 0
        # dead center and both poles fixed at +/-90 degrees.
        latitude = np.sign(raw_latitude) * 90.0 * (
            np.abs(raw_latitude) / 90.0
        ) ** 1.15
        land = self._land_mask(longitude, latitude) & on_globe

        ocean_color = np.array([10.0, 90.0, 210.0])
        land_color = np.array([85.0, 185.0, 75.0])
        desert_color = np.array([220.0, 175.0, 80.0])
        sample_color = np.broadcast_to(ocean_color, (*on_globe.shape, 3)).copy()
        sample_color[land] = land_color

        dry_land = land & (np.abs(latitude) < 31.0) & (
            np.sin(np.radians(longitude * 2.2 + latitude * 3.1)) > 0.2
        )
        sample_color[dry_land] = desert_color

        polar = on_globe & (np.abs(latitude) > 72.0)
        sample_color[polar] = [230.0, 245.0, 255.0]

        # Fixed upper-left light gives a readable terminator without hiding
        # continents completely on the night side.
        light = np.array([-0.42, 0.30, 0.855])
        light /= np.linalg.norm(light)
        diffuse = np.maximum(
            globe_x * light[0] + globe_y * light[1] + globe_z * light[2],
            0.0,
        )
        lighting = 0.30 + 0.70 * diffuse
        sample_color *= lighting[:, :, np.newaxis]

        atmosphere = np.clip((1.0 - globe_z) ** 3 * 75.0, 0.0, 55.0)
        sample_color[:, :, 1] += atmosphere * on_globe
        sample_color[:, :, 2] += atmosphere * 1.5 * on_globe

        # Sparse translucent clouds add motion cues without obscuring the map.
        cloud_pattern = (
            np.sin(np.radians(longitude * 3.0) + elapsed * 0.045)
            + np.sin(np.radians(latitude * 7.0 - longitude * 0.7))
        )
        clouds = on_globe & (cloud_pattern > 1.45) & (np.abs(latitude) < 65.0)
        sample_color[clouds] = sample_color[clouds] * 0.70 + 255.0 * 0.30

        # Average only covered samples. Partial coverage naturally antialiases
        # the circular limb against the star field.
        coverage = on_globe.sum(axis=1)
        globe_sum = (sample_color * on_globe[:, :, np.newaxis]).sum(axis=1)
        covered = coverage > 0
        globe_average = globe_sum[covered] / coverage[covered, np.newaxis]
        land_coverage = land.sum(axis=1)
        coastline = covered & (land_coverage > 0) & (land_coverage < coverage)
        coastline_within_covered = coastline[covered]
        globe_average[coastline_within_covered] = (
            globe_average[coastline_within_covered] * 0.72
            + np.array([185.0, 205.0, 112.0]) * 0.28
        )
        coverage_fraction = coverage[covered, np.newaxis] / len(self.sample_offsets)
        output[covered] = (
            output[covered] * (1.0 - coverage_fraction)
            + globe_average * coverage_fraction
        )

        state[:] = np.clip(output * self.brightness, 0, 255)
        return state.astype(int)
