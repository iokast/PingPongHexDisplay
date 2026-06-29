import math
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


class SolarDimmer:
    """Day/night brightness multiplier based on local sunrise and sunset."""

    def __init__(
        self,
        latitude=38.9072,
        longitude=-77.0369,
        timezone_name="America/New_York",
        day_brightness=1.0,
        night_brightness=0.5,
        transition_hours=2.0,
        override_seconds=3600,
    ):
        self.latitude = latitude
        self.longitude = longitude
        self.timezone = ZoneInfo(timezone_name)
        self.day_brightness = day_brightness
        self.night_brightness = night_brightness
        self.transition_half_width = timedelta(hours=transition_hours / 2.0)
        self.override_seconds = override_seconds
        self.override_until = 0.0
        self._cached_date = None
        self._cached_events = None

    def start_override(self):
        self.override_until = time.monotonic() + self.override_seconds

    def override_active(self, monotonic_now=None):
        if monotonic_now is None:
            monotonic_now = time.monotonic()
        return monotonic_now < self.override_until

    @staticmethod
    def _normalize_degrees(value):
        return value % 360.0

    def _solar_event_utc_hour(self, local_date, sunrise):
        """NOAA sunrise equation, returning the event hour in UTC."""
        day_number = local_date.timetuple().tm_yday
        longitude_hour = self.longitude / 15.0
        approximate_time = day_number + (
            (6.0 if sunrise else 18.0) - longitude_hour
        ) / 24.0

        mean_anomaly = 0.9856 * approximate_time - 3.289
        true_longitude = self._normalize_degrees(
            mean_anomaly
            + 1.916 * math.sin(math.radians(mean_anomaly))
            + 0.020 * math.sin(math.radians(2.0 * mean_anomaly))
            + 282.634
        )

        right_ascension = self._normalize_degrees(math.degrees(math.atan(
            0.91764 * math.tan(math.radians(true_longitude))
        )))
        longitude_quadrant = math.floor(true_longitude / 90.0) * 90.0
        ascension_quadrant = math.floor(right_ascension / 90.0) * 90.0
        right_ascension = (right_ascension + longitude_quadrant - ascension_quadrant) / 15.0

        sin_declination = 0.39782 * math.sin(math.radians(true_longitude))
        cos_declination = math.cos(math.asin(sin_declination))
        zenith = 90.833
        cos_hour_angle = (
            math.cos(math.radians(zenith))
            - sin_declination * math.sin(math.radians(self.latitude))
        ) / (cos_declination * math.cos(math.radians(self.latitude)))
        cos_hour_angle = max(-1.0, min(1.0, cos_hour_angle))

        hour_angle = math.degrees(math.acos(cos_hour_angle))
        if sunrise:
            hour_angle = 360.0 - hour_angle
        hour_angle /= 15.0

        local_mean_time = (
            hour_angle
            + right_ascension
            - 0.06571 * approximate_time
            - 6.622
        )
        return (local_mean_time - longitude_hour) % 24.0

    def _event_datetime(self, local_date, sunrise):
        utc_hour = self._solar_event_utc_hour(local_date, sunrise)
        # Sunset in Washington can fall on the following UTC date. Select the
        # UTC candidate that converts back to the requested local calendar day.
        for day_offset in (-1, 0, 1):
            candidate = datetime.combine(
                local_date + timedelta(days=day_offset),
                datetime.min.time(),
                tzinfo=timezone.utc,
            ) + timedelta(hours=utc_hour)
            local_candidate = candidate.astimezone(self.timezone)
            if local_candidate.date() == local_date:
                return local_candidate
        raise RuntimeError("Could not resolve solar event to the local date")

    def events_for_date(self, local_date):
        if local_date != self._cached_date:
            self._cached_events = (
                self._event_datetime(local_date, sunrise=True),
                self._event_datetime(local_date, sunrise=False),
            )
            self._cached_date = local_date
        return self._cached_events

    @staticmethod
    def _lerp(start, end, fraction):
        return start + (end - start) * fraction

    def automatic_brightness(self, now=None):
        if now is None:
            now = datetime.now(self.timezone)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=self.timezone)
        else:
            now = now.astimezone(self.timezone)

        sunrise, sunset = self.events_for_date(now.date())
        sunrise_start = sunrise - self.transition_half_width
        sunrise_end = sunrise + self.transition_half_width
        sunset_start = sunset - self.transition_half_width
        sunset_end = sunset + self.transition_half_width

        if now < sunrise_start or now >= sunset_end:
            return self.night_brightness
        if now < sunrise_end:
            fraction = (now - sunrise_start) / (sunrise_end - sunrise_start)
            return self._lerp(self.night_brightness, self.day_brightness, fraction)
        if now < sunset_start:
            return self.day_brightness

        fraction = (now - sunset_start) / (sunset_end - sunset_start)
        return self._lerp(self.day_brightness, self.night_brightness, fraction)

    def brightness(self, now=None, monotonic_now=None):
        if self.override_active(monotonic_now):
            return 1.0
        return self.automatic_brightness(now)
