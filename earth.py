import math
import os
import time
from datetime import datetime, timezone

import numpy as np

from hex_mask import cartesian_coords


class Earth:
    """A readable, antialiased rotating globe rendered on the LED lattice."""

    CLOSEUP_LATITUDE = 20.0

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
        ((-17, 37), (-10, 36), (-6, 35), (-2, 36), (4, 37),
         (10, 37), (15, 33), (22, 32), (29, 31), (33, 28),
         (35, 23), (39, 16), (43, 12), (51, 11), (49, 7),
         (45, 2), (42, -1), (41, -10), (40, -16), (36, -22),
         (33, -27), (28, -34), (23, -35), (18, -34), (15, -29),
         (12, -24), (9, -18), (6, -12), (2, -6), (0, 5),
         (-5, 5), (-8, 7), (-13, 8), (-16, 13), (-17, 21),
         (-13, 28), (-10, 31)),
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

    # Broad geographic regions, simplified for readability on 397 LEDs.
    DESERT_REGIONS = (
        ((-17, 15), (-12, 29), (5, 36), (28, 33), (36, 22),
         (25, 14), (5, 12)),                                      # Sahara
        ((35, 17), (43, 30), (56, 27), (58, 18), (50, 12)),       # Arabian
        ((55, 35), (68, 47), (83, 47), (91, 38), (78, 30)),       # Central Asia
        ((87, 38), (102, 47), (113, 45), (108, 36), (94, 35)),    # Gobi
        ((114, -20), (127, -14), (145, -20), (145, -34),
         (128, -35), (116, -29)),                                 # Australia
        ((-118, 31), (-104, 31), (-103, 40), (-114, 43)),         # SW North America
        ((-76, -15), (-68, -17), (-69, -28), (-73, -30)),         # Atacama
        ((11, -16), (22, -17), (25, -29), (15, -30)),             # Kalahari
        ((11, -18), (17, -20), (16, -29), (12, -29)),             # Namib
    )

    MOUNTAIN_REGIONS = (
        ((-81, 8), (-75, 12), (-68, -18), (-67, -55),
         (-73, -43), (-76, -15)),                                 # Andes
        ((-130, 55), (-121, 50), (-108, 31), (-103, 28),
         (-110, 44), (-119, 58)),                                 # Rockies
        ((-10, 31), (0, 36), (10, 35), (1, 29)),                  # Atlas
        ((5, 44), (17, 48), (16, 45), (7, 42)),                   # Alps
        ((35, 39), (50, 43), (58, 35), (45, 32)),                 # Caucasus/Zagros
        ((67, 37), (78, 37), (96, 29), (103, 27), (91, 35),
         (76, 42)),                                                # Himalaya/Tibet
        ((137, 34), (145, 45), (142, 31)),                         # Japan
        ((145, -17), (153, -27), (149, -38), (143, -32)),         # Eastern Australia
        ((166, -34), (179, -39), (174, -47), (168, -44)),         # New Zealand Alps
    )

    LIGHTING_MODES = ("day & night", "day only", "night only")

    # Major population centers, intentionally consolidated and slightly
    # exaggerated so they remain visible on the low-resolution globe.
    CITY_CENTERS = (
        (-74.0, 40.7), (-77.0, 38.9), (-87.6, 41.9), (-118.2, 34.1),
        (-99.1, 19.4), (-46.6, -23.6), (-58.4, -34.6), (-0.1, 51.5),
        (2.4, 48.9), (13.4, 52.5), (30.5, 50.5), (37.6, 55.8),
        (31.2, 30.0), (3.4, 6.5), (28.0, -26.2), (55.3, 25.2),
        (72.9, 19.1), (77.2, 28.6), (90.4, 23.8), (100.5, 13.8),
        (103.8, 1.3), (106.8, -6.2), (116.4, 39.9), (121.5, 31.2),
        (139.7, 35.7), (127.0, 37.6), (151.2, -33.9), (144.9, -37.8),
    )

    SECONDARY_CITY_CENTERS = (
        (-123.1, 49.3), (-122.3, 47.6), (-112.1, 33.4), (-104.9, 39.7),
        (-97.7, 30.3), (-95.4, 29.8), (-90.1, 29.9), (-84.4, 33.8),
        (-80.2, 25.8), (-79.4, 43.7), (-73.6, 45.5), (-70.7, -33.5),
        (-77.0, -12.0), (-74.1, 4.7), (-43.2, -22.9), (-38.5, -12.9),
        (-3.7, 40.4), (12.5, 41.9), (18.1, 59.3), (24.9, 60.2),
        (21.0, 52.2), (14.4, 50.1), (19.0, 47.5), (23.7, 38.0),
        (29.0, 41.0), (44.4, 33.3), (46.7, 24.7), (32.6, 15.5),
        (-7.6, 33.6), (-4.0, 5.3), (7.5, 9.1), (15.3, -4.3),
        (32.6, 0.3), (36.8, -1.3), (38.8, 9.0), (39.3, -6.8),
        (28.0, -26.2), (18.4, -33.9), (73.0, 33.7), (74.4, 31.5),
        (67.0, 24.9), (80.3, 13.1), (77.6, 13.0), (88.4, 22.6),
        (96.2, 16.9), (105.8, 21.0), (106.7, 10.8), (101.7, 3.1),
        (114.2, 22.3), (113.3, 23.1), (104.1, 30.7), (106.6, 29.6),
        (114.3, 30.6), (120.2, 30.3), (117.2, 39.1), (126.5, 43.8),
        (121.5, 25.0), (135.5, 34.7), (136.9, 35.2), (130.4, 33.6),
        (141.4, 43.1), (153.0, -27.5), (115.9, -31.9), (174.8, -36.9),
    )

    # Populated belts supply the distributed light visible in satellite
    # imagery. Strengths remain below metro centers, and a deterministic
    # texture prevents these broad regions from looking like solid paint.
    POPULATION_REGIONS = (
        (0.48, ((-96, 29), (-82, 25), (-67, 43), (-72, 48),
                (-90, 47), (-98, 38))),                           # Eastern US
        (0.30, ((-124, 32), (-117, 32), (-118, 49), (-124, 49))), # US west coast
        (0.24, ((-106, 20), (-96, 18), (-86, 21), (-98, 31))),    # Mexico
        (0.22, ((-80, -5), (-70, 8), (-60, 7), (-72, -15))),      # Northern Andes
        (0.32, ((-52, -31), (-39, -23), (-42, -10), (-51, -15),
                (-57, -25))),                                     # SE Brazil
        (0.52, ((-10, 36), (4, 43), (25, 44), (31, 54),
                (20, 61), (3, 59), (-6, 51))),                    # Europe
        (0.25, ((24, 30), (31, 31), (33, 23), (31, 15),
                (29, 22))),                                       # Nile valley
        (0.18, ((-9, 5), (12, 3), (15, 12), (3, 14))),            # West Africa
        (0.22, ((27, -34), (33, -24), (31, -18), (24, -25))),     # Southern Africa
        (0.55, ((67, 7), (78, 6), (91, 22), (87, 30),
                (75, 31), (68, 23))),                              # Indian subcontinent
        (0.28, ((91, 20), (107, 8), (108, 23), (99, 28))),        # Mainland SE Asia
        (0.58, ((106, 20), (119, 22), (123, 31), (120, 41),
                (111, 35))),                                       # Eastern China
        (0.42, ((126, 34), (130, 34), (130, 40), (125, 40))),     # Korea
        (0.44, ((130, 31), (142, 34), (146, 45), (138, 45))),     # Japan
        (0.38, ((95, -8), (114, -9), (116, -5), (105, 1))),       # Java/Sumatra
        (0.24, ((145, -39), (154, -27), (151, -21), (143, -32))), # Eastern Australia
    )

    def __init__(self, color_palette=None, alpha=1.0):
        self.brightness = alpha
        self.start_time = time.monotonic()
        self._last_update_time = self.start_time
        self._animation_elapsed = 0.0
        self.rotation_rate = 3.0
        self._sun_cache_minute = None
        self._sun_cache_position = None
        self.rotation_seconds = float(os.environ.get(
            "PPL_EARTH_ROTATION_SECONDS", "120"
        ))
        self.lighting_mode_id = 0

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
        self._build_geography_lookup()

    def set_palette(self, color_palette, alpha):
        self.brightness = alpha

    def set_brightness(self, brightness):
        self.brightness = brightness

    @property
    def lighting_mode(self):
        return self.LIGHTING_MODES[self.lighting_mode_id]

    def change_lighting_mode(self):
        self.lighting_mode_id = (
            self.lighting_mode_id + 1
        ) % len(self.LIGHTING_MODES)
        return self.lighting_mode

    def set_rotation_rate(self, rate):
        self.rotation_rate = max(0.0, float(rate))
        return self.rotation_rate

    @staticmethod
    def _sun_position(now=None):
        """Approximate the real-time subsolar longitude and latitude."""
        if now is None:
            now = datetime.now(timezone.utc)
        day = now.timetuple().tm_yday
        utc_hour = now.hour + now.minute / 60.0 + now.second / 3600.0
        year_angle = 2.0 * math.pi / 365.0 * (
            day - 1 + (utc_hour - 12.0) / 24.0
        )
        equation_of_time = 229.18 * (
            0.000075 + 0.001868 * math.cos(year_angle)
            - 0.032077 * math.sin(year_angle)
            - 0.014615 * math.cos(2.0 * year_angle)
            - 0.040849 * math.sin(2.0 * year_angle)
        )
        declination = (
            0.006918 - 0.399912 * math.cos(year_angle)
            + 0.070257 * math.sin(year_angle)
            - 0.006758 * math.cos(2.0 * year_angle)
            + 0.000907 * math.sin(2.0 * year_angle)
            - 0.002697 * math.cos(3.0 * year_angle)
            + 0.00148 * math.sin(3.0 * year_angle)
        )
        longitude = 180.0 - 15.0 * utc_hour - equation_of_time / 4.0
        longitude = (longitude + 180.0) % 360.0 - 180.0
        return longitude, math.degrees(declination)

    def _current_sun_position(self):
        now = datetime.now(timezone.utc)
        minute = (now.year, now.timetuple().tm_yday, now.hour, now.minute)
        if minute != self._sun_cache_minute:
            self._sun_cache_minute = minute
            self._sun_cache_position = self._sun_position(now)
        return self._sun_cache_position

    def _city_lights_geometric(self, longitude, latitude):
        lights = np.zeros(longitude.shape, dtype=float)
        city_groups = (
            (self.CITY_CENTERS, 4.5, 1.0),
            (self.SECONDARY_CITY_CENTERS, 3.2, 0.62),
        )
        for cities, radius, strength in city_groups:
            for city_longitude, city_latitude in cities:
                longitude_delta = (
                    longitude - city_longitude + 180.0
                ) % 360.0 - 180.0
                distance = np.sqrt(
                    (longitude_delta * math.cos(math.radians(city_latitude))) ** 2
                    + (latitude - city_latitude) ** 2
                )
                glow = strength * np.clip(1.0 - distance / radius, 0.0, 1.0)
                np.maximum(lights, glow, out=lights)
        return lights

    def _population_lights_geometric(self, longitude, latitude):
        density = np.zeros(longitude.shape, dtype=float)
        for strength, polygon in self.POPULATION_REGIONS:
            region = self._points_in_polygon(longitude, latitude, polygon)
            density[region] = np.maximum(density[region], strength)

        # Stable geographic variation suggests towns, roads, and dark rural
        # gaps without causing temporal sparkle as the globe rotates.
        texture = (
            0.52
            + 0.28 * (0.5 + 0.5 * np.sin(np.radians(longitude * 17.0 + latitude * 9.0)))
            + 0.20 * (0.5 + 0.5 * np.sin(np.radians(longitude * 31.0 - latitude * 13.0)))
        )
        return density * texture

    def _build_geography_lookup(self):
        """Rasterize static geography once instead of testing it every frame."""
        longitude_axis = np.arange(-180.0, 180.0, 1.0)
        latitude_axis = np.arange(-90.0, 91.0, 1.0)
        longitude, latitude = np.meshgrid(longitude_axis, latitude_axis)
        self._land_lookup = self._land_mask_geometric(longitude, latitude)
        city_lights = self._city_lights_geometric(longitude, latitude)
        population_lights = self._population_lights_geometric(
            longitude, latitude
        )
        self._city_lookup = np.maximum(city_lights, population_lights)
        self._city_lookup *= self._land_lookup
        self._desert_lookup = self._region_mask(
            longitude, latitude, self.DESERT_REGIONS
        ) & self._land_lookup
        self._mountain_lookup = self._region_mask(
            longitude, latitude, self.MOUNTAIN_REGIONS
        ) & self._land_lookup

    def _region_mask(self, longitude, latitude, regions):
        mask = np.zeros(longitude.shape, dtype=bool)
        for polygon in regions:
            mask |= self._points_in_polygon(longitude, latitude, polygon)
        return mask

    @staticmethod
    def _lookup_indices(longitude, latitude):
        longitude_index = np.rint(longitude + 180.0).astype(np.int16) % 360
        latitude_index = np.clip(
            np.rint(latitude + 90.0).astype(np.int16), 0, 180
        )
        return longitude_index, latitude_index

    def _city_lights(self, longitude, latitude):
        longitude_index, latitude_index = self._lookup_indices(
            longitude, latitude
        )
        return self._city_lookup[latitude_index, longitude_index]

    def _terrain_masks(self, longitude, latitude):
        longitude_index, latitude_index = self._lookup_indices(
            longitude, latitude
        )
        return (
            self._desert_lookup[latitude_index, longitude_index],
            self._mountain_lookup[latitude_index, longitude_index],
        )

    @staticmethod
    def _smoothstep(value):
        value = np.clip(value, 0.0, 1.0)
        return value * value * (3.0 - 2.0 * value)

    def _camera(self, elapsed):
        """Return camera latitude, globe scale, and vertical framing offset."""
        transition_rotations = 0.40
        wide_rotations = 1.0
        cycle_rotations = 2.0 + 2.0 * wide_rotations + 4.0 * transition_rotations
        phase = (elapsed / self.rotation_seconds) % cycle_rotations
        close_scale = 1.62
        # At this zoom, an offset of roughly half the original globe radius
        # keeps the near polar limb inside the hexagonal display while pushing
        # most of the opposite hemisphere beyond the far edge.
        close_offset = 0.62

        if phase < 1.0:
            return self.CLOSEUP_LATITUDE, close_scale, close_offset

        if phase < 1.0 + transition_rotations:
            progress = self._smoothstep((phase - 1.0) / transition_rotations)
            latitude = self.CLOSEUP_LATITUDE * (1.0 - progress)
            scale = close_scale + (1.0 - close_scale) * progress
            offset = close_offset * (1.0 - progress)
            return latitude, scale, offset

        south_zoom_start = 1.0 + transition_rotations + wide_rotations
        if phase < south_zoom_start:
            return 0.0, 1.0, 0.0

        if phase < south_zoom_start + transition_rotations:
            progress = self._smoothstep(
                (phase - south_zoom_start) / transition_rotations
            )
            return (
                -self.CLOSEUP_LATITUDE * progress,
                1.0 + (close_scale - 1.0) * progress,
                -close_offset * progress,
            )

        south_hold_end = south_zoom_start + transition_rotations + 1.0
        if phase < south_hold_end:
            return -self.CLOSEUP_LATITUDE, close_scale, -close_offset

        south_zoom_out_end = south_hold_end + transition_rotations
        if phase < south_zoom_out_end:
            progress = self._smoothstep(
                (phase - south_hold_end) / transition_rotations
            )
            return (
                -self.CLOSEUP_LATITUDE * (1.0 - progress),
                close_scale + (1.0 - close_scale) * progress,
                -close_offset * (1.0 - progress),
            )

        north_zoom_start = south_zoom_out_end + wide_rotations
        if phase < north_zoom_start:
            return 0.0, 1.0, 0.0

        progress = self._smoothstep(
            (phase - north_zoom_start) / transition_rotations
        )
        return (
            self.CLOSEUP_LATITUDE * progress,
            1.0 + (close_scale - 1.0) * progress,
            close_offset * progress,
        )

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

    def _land_mask_geometric(self, longitude, latitude):
        land = latitude < -68.0  # simplified Antarctica
        for polygon in self.CONTINENTS:
            land |= self._points_in_polygon(longitude, latitude, polygon)
        for polygon in self.WATER_CUTOUTS:
            land &= ~self._points_in_polygon(longitude, latitude, polygon)
        return land

    def _land_mask(self, longitude, latitude):
        longitude_index, latitude_index = self._lookup_indices(
            longitude, latitude
        )
        return self._land_lookup[latitude_index, longitude_index]

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
        now = time.monotonic()
        delta = max(0.0, now - self._last_update_time)
        self._last_update_time = now
        self._animation_elapsed += delta * self.rotation_rate
        elapsed = self._animation_elapsed
        output = self._background(elapsed)

        camera_latitude, camera_scale, camera_offset = self._camera(elapsed)
        camera_radius = self.radius * camera_scale
        framed_center_y = self.center_y + self.radius * camera_offset

        sample_x = self.x[:, np.newaxis] + self.sample_offsets[np.newaxis, :, 0]
        sample_y = self.y[:, np.newaxis] + self.sample_offsets[np.newaxis, :, 1]
        screen_x = (sample_x - self.center_x) / camera_radius
        screen_y = (framed_center_y - sample_y) / camera_radius

        # Keep the rotational axis vertical so north remains straight up.
        view_x = screen_x
        view_y = screen_y
        radius_squared = view_x * view_x + view_y * view_y
        on_globe = radius_squared <= 1.0
        view_z = np.sqrt(np.clip(1.0 - radius_squared, 0.0, 1.0))

        # Tilt the globe under the camera. At +30 degrees the center of the
        # display is 30 N; at -30 degrees it is 30 S.
        camera_angle = math.radians(camera_latitude)
        camera_sin = math.sin(camera_angle)
        camera_cos = math.cos(camera_angle)
        globe_x = view_x
        globe_y = view_y * camera_cos + view_z * camera_sin
        globe_z = view_z * camera_cos - view_y * camera_sin

        rotation = 2.0 * math.pi * (elapsed / self.rotation_seconds)
        longitude = np.degrees(np.arctan2(globe_x, globe_z) + rotation)
        longitude = (longitude + 180.0) % 360.0 - 180.0
        latitude = np.degrees(np.arcsin(np.clip(globe_y, -1.0, 1.0)))
        land = self._land_mask(longitude, latitude) & on_globe

        ocean_color = np.array([10.0, 90.0, 210.0])
        land_color = np.array([85.0, 185.0, 75.0])
        desert_color = np.array([220.0, 175.0, 80.0])
        mountain_color = np.array([120.0, 105.0, 78.0])
        sample_color = np.broadcast_to(ocean_color, (*on_globe.shape, 3)).copy()
        sample_color[land] = land_color

        desert, mountain = self._terrain_masks(longitude, latitude)
        desert &= land & on_globe
        mountain &= land & on_globe
        sample_color[desert] = desert_color
        sample_color[mountain] = mountain_color

        # A restrained snow highlight distinguishes the highest northern
        # ranges without turning every mountain into a polar ice cap.
        snowy_mountain = mountain & (latitude > 34.0)
        sample_color[snowy_mountain] = [190.0, 195.0, 185.0]

        polar = on_globe & (np.abs(latitude) > 72.0)
        sample_color[polar] = [230.0, 245.0, 255.0]

        # Sparse translucent clouds add motion cues without obscuring the map.
        cloud_pattern = (
            np.sin(np.radians(longitude * 3.0) + elapsed * 0.045)
            + np.sin(np.radians(latitude * 7.0 - longitude * 0.7))
        )
        clouds = on_globe & (cloud_pattern > 1.45) & (np.abs(latitude) < 65.0)
        sample_color[clouds] = sample_color[clouds] * 0.70 + 255.0 * 0.30
        unlit_surface_color = sample_color.copy()

        sun_longitude, sun_latitude = self._current_sun_position()
        latitude_radians = np.radians(latitude)
        sun_latitude_radians = math.radians(sun_latitude)
        solar_cosine = (
            np.sin(latitude_radians) * math.sin(sun_latitude_radians)
            + np.cos(latitude_radians) * math.cos(sun_latitude_radians)
            * np.cos(np.radians(longitude - sun_longitude))
        )

        if self.lighting_mode == "day only":
            # Studio-style light keeps the entire globe legible.
            light = np.array([-0.42, 0.30, 0.855])
            light /= np.linalg.norm(light)
            diffuse = np.maximum(
                view_x * light[0] + view_y * light[1] + view_z * light[2],
                0.0,
            )
            lighting = 0.38 + 0.62 * diffuse
            night_side = np.zeros(on_globe.shape, dtype=bool)
        elif self.lighting_mode == "night only":
            lighting = np.full(on_globe.shape, 0.11)
            night_side = on_globe
            daylight = np.zeros(on_globe.shape, dtype=float)
        else:
            # Spread twilight across the terminator instead of switching from
            # ambient to direct sunlight at exactly zero solar elevation.
            twilight = np.clip((solar_cosine + 0.12) / 0.30, 0.0, 1.0)
            daylight = twilight * twilight * (3.0 - 2.0 * twilight)
            lighting = 0.11 + 0.89 * daylight
            night_side = on_globe & (solar_cosine < -0.04)

        sample_color *= lighting[:, :, np.newaxis]

        # The hardware gamma LUT maps values below about 25 to zero. Preserve
        # a gradual land-only floor, rather than switching it on sharply at
        # the terminator. The ocean remains substantially darker.
        if self.lighting_mode == "night only":
            land_floor = np.full(on_globe.shape, 0.30)
            dark_land = land & on_globe
        elif self.lighting_mode == "day & night":
            # Land moves monotonically from a readable 30% night level to
            # full daylight using the same smooth twilight curve.
            land_floor = 0.30 + 0.70 * daylight
            dark_land = land & on_globe
        else:
            land_floor = np.zeros(on_globe.shape)
            dark_land = np.zeros(on_globe.shape, dtype=bool)
        sample_color[dark_land] = np.maximum(
            sample_color[dark_land],
            unlit_surface_color[dark_land]
            * land_floor[dark_land, np.newaxis],
        )

        atmosphere = np.clip((1.0 - view_z) ** 3 * 75.0, 0.0, 55.0)
        if self.lighting_mode == "night only":
            atmosphere *= 0.18
        elif self.lighting_mode == "day & night":
            atmosphere *= 0.18 + 0.82 * daylight
        sample_color[:, :, 1] += atmosphere * on_globe
        sample_color[:, :, 2] += atmosphere * 1.5 * on_globe

        city_lights = self._city_lights(longitude, latitude)
        illuminated_cities = (city_lights > 0.0) & land & night_side
        city_strength = np.clip(
            city_lights[illuminated_cities, np.newaxis] * 1.35,
            0.0,
            1.0,
        )
        sample_color[illuminated_cities] = (
            sample_color[illuminated_cities] * (1.0 - city_strength)
            + np.array([255.0, 215.0, 105.0]) * city_strength
        )

        # Average only covered samples. Partial coverage naturally antialiases
        # the circular limb against the star field.
        coverage = on_globe.sum(axis=1)
        globe_sum = (sample_color * on_globe[:, :, np.newaxis]).sum(axis=1)
        covered = coverage > 0
        globe_average = globe_sum[covered] / coverage[covered, np.newaxis]
        coverage_fraction = coverage[covered, np.newaxis] / len(self.sample_offsets)
        output[covered] = (
            output[covered] * (1.0 - coverage_fraction)
            + globe_average * coverage_fraction
        )

        state[:] = np.clip(output * self.brightness, 0, 255)
        return state.astype(int)
