import math
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import numpy as np

from hex_mask import cartesian_coords
from solar_dimmer import SolarDimmer


class DayNight:
    """Pixel-art day/night landscape drawn directly on the hex LED lattice."""

    NIGHT_TOP = np.array([3, 5, 20], dtype=float)
    NIGHT_BOTTOM = np.array([18, 14, 42], dtype=float)
    DAWN_TOP = np.array([52, 55, 112], dtype=float)
    DAWN_BOTTOM = np.array([255, 105, 62], dtype=float)
    DAY_TOP = np.array([25, 112, 210], dtype=float)
    DAY_BOTTOM = np.array([125, 205, 245], dtype=float)
    DUSK_TOP = np.array([48, 35, 105], dtype=float)
    DUSK_BOTTOM = np.array([245, 72, 52], dtype=float)

    def __init__(self, color_palette=None, alpha=1.0):
        self.brightness = alpha
        self.solar = SolarDimmer()
        self.test_mode = (
            "--test-day-night" in sys.argv
            or os.environ.get("PPL_DAY_NIGHT_TEST") == "1"
        )
        self.time_scale = 500.0 if self.test_mode else 1.0
        self.start_datetime = datetime.now(self.solar.timezone)
        self.start_monotonic = time.monotonic()

        coords = cartesian_coords.astype(float)
        self.y = coords[:, 0]
        self.x = coords[:, 1]
        self.x_min = self.x.min()
        self.x_max = self.x.max()
        self.y_min = self.y.min()
        self.y_max = self.y.max()
        self.x_norm = (self.x - self.x_min) / (self.x_max - self.x_min)
        self.y_norm = (self.y - self.y_min) / (self.y_max - self.y_min)

    def current_time(self):
        if not self.test_mode:
            return datetime.now(self.solar.timezone)
        elapsed = time.monotonic() - self.start_monotonic
        return self.start_datetime + timedelta(seconds=elapsed * self.time_scale)

    def set_palette(self, color_palette, alpha):
        # This animation owns its naturalistic palette, but participates in
        # the same brightness controls as the other background animations.
        self.brightness = alpha

    @staticmethod
    def _smoothstep(value):
        value = max(0.0, min(1.0, value))
        return value * value * (3.0 - 2.0 * value)

    @classmethod
    def _blend(cls, start, end, fraction):
        fraction = cls._smoothstep(fraction)
        return start + (end - start) * fraction

    def _sky_palette(self, now, sunrise, sunset):
        hour = timedelta(hours=1)
        keyframes = [
            (sunrise - hour, self.NIGHT_TOP, self.NIGHT_BOTTOM),
            (sunrise, self.DAWN_TOP, self.DAWN_BOTTOM),
            (sunrise + hour, self.DAY_TOP, self.DAY_BOTTOM),
            (sunset - hour, self.DAY_TOP, self.DAY_BOTTOM),
            (sunset, self.DUSK_TOP, self.DUSK_BOTTOM),
            (sunset + hour, self.NIGHT_TOP, self.NIGHT_BOTTOM),
        ]

        if now <= keyframes[0][0] or now >= keyframes[-1][0]:
            return self.NIGHT_TOP, self.NIGHT_BOTTOM

        for left, right in zip(keyframes, keyframes[1:]):
            if left[0] <= now <= right[0]:
                fraction = (now - left[0]) / (right[0] - left[0])
                return (
                    self._blend(left[1], right[1], fraction),
                    self._blend(left[2], right[2], fraction),
                )
        return self.NIGHT_TOP, self.NIGHT_BOTTOM

    def _draw_sky(self, state, top, bottom):
        vertical = np.clip(self.y_norm / 0.85, 0.0, 1.0)[:, np.newaxis]
        state[:] = top + (bottom - top) * vertical

    @staticmethod
    def _smooth_array(values):
        values = np.clip(values, 0.0, 1.0)
        return values * values * (3.0 - 2.0 * values)

    def _blend_pixels(self, state, color, coverage):
        coverage = np.clip(coverage, 0.0, 1.0)[:, np.newaxis]
        state[:] = state * (1.0 - coverage) + np.asarray(color) * coverage

    def _disc_coverage(self, center_x, center_y, radius, edge_width=0.8):
        distance = np.sqrt((self.x - center_x) ** 2 + (self.y - center_y) ** 2)
        return (radius + edge_width / 2.0 - distance) / edge_width

    def _draw_disc(self, state, center_x, center_y, radius, color, edge_width=0.8):
        coverage = self._smooth_array(
            self._disc_coverage(center_x, center_y, radius, edge_width)
        )
        self._blend_pixels(state, color, coverage)

    def _draw_sun(self, state, now, sunrise, sunset):
        if not sunrise <= now <= sunset:
            return
        progress = (now - sunrise) / (sunset - sunrise)
        center_x = self.x_min + (0.08 + 0.84 * progress) * (self.x_max - self.x_min)
        horizon_y = self.y_min + 0.67 * (self.y_max - self.y_min)
        arc_height = 0.61 * (self.y_max - self.y_min)
        center_y = horizon_y - arc_height * math.sin(math.pi * progress)

        # Same apparent radius as a full moon. The softer outer color keeps
        # edge coverage visible without making the center look washed out.
        self._draw_disc(state, center_x, center_y, 2.05, [255, 165, 38])
        self._draw_disc(state, center_x, center_y, 1.45, [255, 232, 118], 0.65)

    @staticmethod
    def _lunar_phase(now):
        # A well-known reference new moon; sufficient for a pixel-art phase.
        reference = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)
        synodic_days = 29.53058867
        age_days = (now.astimezone(timezone.utc) - reference).total_seconds() / 86400.0
        return (age_days % synodic_days) / synodic_days

    def _night_interval(self, now):
        today_sunrise, today_sunset = self.solar.events_for_date(now.date())
        if now >= today_sunset:
            next_sunrise, _ = self.solar.events_for_date(now.date() + timedelta(days=1))
            return today_sunset, next_sunrise
        if now < today_sunrise:
            _, previous_sunset = self.solar.events_for_date(now.date() - timedelta(days=1))
            return previous_sunset, today_sunrise
        return None

    def _draw_moon(self, state, now):
        interval = self._night_interval(now)
        if interval is None:
            return
        moonrise, moonset = interval
        progress = (now - moonrise) / (moonset - moonrise)
        center_x = self.x_min + (0.08 + 0.84 * progress) * (self.x_max - self.x_min)
        horizon_y = self.y_min + 0.62 * (self.y_max - self.y_min)
        arc_height = 0.55 * (self.y_max - self.y_min)
        center_y = horizon_y - arc_height * math.sin(math.pi * progress)

        dx = self.x - center_x
        dy = self.y - center_y
        radius = 2.05
        disc_coverage = self._smooth_array(
            self._disc_coverage(center_x, center_y, radius)
        )
        self._blend_pixels(state, [19, 24, 43], disc_coverage)

        phase = self._lunar_phase(now)
        illuminated = 0.5 * (1.0 - math.cos(2.0 * math.pi * phase))
        normalized_x = dx / radius
        if phase < 0.5:  # waxing: light grows from the right
            boundary = 1.0 - 2.0 * illuminated
            phase_coverage = (normalized_x - boundary) / 0.28 + 0.5
        else:  # waning: light remains on the left
            boundary = -1.0 + 2.0 * illuminated
            phase_coverage = (boundary - normalized_x) / 0.28 + 0.5
        lit_coverage = disc_coverage * self._smooth_array(phase_coverage)
        self._blend_pixels(state, [205, 218, 214], lit_coverage)

    def _draw_trees(self, state, now):
        seconds = now.timestamp()
        sway = seconds / 14.0

        # A single unbroken treetop horizon. Everything below this edge is
        # canopy, giving the perspective of hovering above a forest.
        canopy_edge = (
            0.62
            + 0.025 * np.sin(self.x_norm * math.pi * 7.0 + sway)
            + 0.014 * np.sin(self.x_norm * math.pi * 15.0 - sway * 0.7)
        )
        canopy = self.y_norm >= canopy_edge
        depth = np.clip(
            (self.y_norm - canopy_edge) / np.maximum(1.0 - canopy_edge, 0.01),
            0.0,
            1.0,
        )

        distant = np.array([31, 91, 49], dtype=float)
        foreground = np.array([5, 31, 21], dtype=float)
        canopy_color = distant + (foreground - distant) * depth[:, np.newaxis]

        leaf_pattern = (
            np.sin(self.x * 2.5 + self.y * 1.6 + sway * 0.35)
            + np.sin(self.x * 4.1 - self.y * 2.2 - sway * 0.22)
        )
        highlight = np.clip((leaf_pattern + 0.3) * 7.0, 0.0, 13.0)
        canopy_color[:, 1] += highlight
        canopy_color[:, 2] += highlight * 0.35
        state[canopy] = canopy_color[canopy]

        # Rounded crowns break up the skyline while remaining connected to the
        # solid canopy beneath them.
        for index, base_x in enumerate((0.10, 0.29, 0.50, 0.72, 0.91)):
            crown_x = base_x + 0.012 * math.sin(sway + index * 1.4)
            crown_y = 0.605 + 0.018 * math.sin(index * 2.3)
            crown = (
                ((self.x_norm - crown_x) / 0.12) ** 2
                + ((self.y_norm - crown_y) / 0.075) ** 2
                <= 1.0
            )
            state[crown] = [25, 82, 44]

    def update(self, state):
        now = self.current_time()
        sunrise, sunset = self.solar.events_for_date(now.date())
        top, bottom = self._sky_palette(now, sunrise, sunset)

        self._draw_sky(state, top, bottom)
        self._draw_sun(state, now, sunrise, sunset)
        self._draw_moon(state, now)
        self._draw_trees(state, now)

        if self.brightness != 1.0:
            state[:] = state * self.brightness
        return state.astype(int)
