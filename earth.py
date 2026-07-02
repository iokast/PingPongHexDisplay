import math
import os
import time
from datetime import datetime, timezone

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

    def __init__(self, color_palette=None, alpha=1.0):
        self.brightness = alpha
        self.start_time = time.monotonic()
        self._last_update_time = self.start_time
        self._animation_elapsed = 0.0
        self.rotation_rate = 1.0
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

    def _city_lights(self, longitude, latitude):
        lights = np.zeros(longitude.shape, dtype=bool)
        for city_longitude, city_latitude in self.CITY_CENTERS:
            longitude_delta = (
                longitude - city_longitude + 180.0
            ) % 360.0 - 180.0
            distance_squared = (
                (longitude_delta * math.cos(math.radians(city_latitude))) ** 2
                + (latitude - city_latitude) ** 2
            )
            lights |= distance_squared < 4.5 ** 2
        return lights

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
            return 30.0, close_scale, close_offset

        if phase < 1.0 + transition_rotations:
            progress = self._smoothstep((phase - 1.0) / transition_rotations)
            latitude = 30.0 * (1.0 - progress)
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
                -30.0 * progress,
                1.0 + (close_scale - 1.0) * progress,
                -close_offset * progress,
            )

        south_hold_end = south_zoom_start + transition_rotations + 1.0
        if phase < south_hold_end:
            return -30.0, close_scale, -close_offset

        south_zoom_out_end = south_hold_end + transition_rotations
        if phase < south_zoom_out_end:
            progress = self._smoothstep(
                (phase - south_hold_end) / transition_rotations
            )
            return (
                -30.0 * (1.0 - progress),
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
            30.0 * progress,
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
        sample_color = np.broadcast_to(ocean_color, (*on_globe.shape, 3)).copy()
        sample_color[land] = land_color

        dry_land = land & (np.abs(latitude) < 31.0) & (
            np.sin(np.radians(longitude * 2.2 + latitude * 3.1)) > 0.2
        )
        sample_color[dry_land] = desert_color

        polar = on_globe & (np.abs(latitude) > 72.0)
        sample_color[polar] = [230.0, 245.0, 255.0]

        # Sparse translucent clouds add motion cues without obscuring the map.
        cloud_pattern = (
            np.sin(np.radians(longitude * 3.0) + elapsed * 0.045)
            + np.sin(np.radians(latitude * 7.0 - longitude * 0.7))
        )
        clouds = on_globe & (cloud_pattern > 1.45) & (np.abs(latitude) < 65.0)
        sample_color[clouds] = sample_color[clouds] * 0.70 + 255.0 * 0.30

        sun_longitude, sun_latitude = self._sun_position()
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
            lighting = np.full(on_globe.shape, 0.075)
            night_side = on_globe
        else:
            # A small ambient floor preserves the globe silhouette while the
            # real-time solar cosine supplies the moving terminator.
            lighting = 0.065 + 0.935 * np.clip(solar_cosine, 0.0, 1.0)
            night_side = on_globe & (solar_cosine < -0.04)

        sample_color *= lighting[:, :, np.newaxis]

        atmosphere = np.clip((1.0 - view_z) ** 3 * 75.0, 0.0, 55.0)
        if self.lighting_mode == "night only":
            atmosphere *= 0.18
        elif self.lighting_mode == "day & night":
            atmosphere *= 0.18 + 0.82 * np.clip(solar_cosine, 0.0, 1.0)
        sample_color[:, :, 1] += atmosphere * on_globe
        sample_color[:, :, 2] += atmosphere * 1.5 * on_globe

        city_lights = self._city_lights(longitude, latitude)
        illuminated_cities = city_lights & land & night_side
        sample_color[illuminated_cities] = [255.0, 174.0, 45.0]

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
