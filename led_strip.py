import _rpi_ws281x as ws
import numpy as np
from numba import njit

class LedStrip:
    def __init__(self):
        LED_CHANNEL = 0
        LED_COUNT = 397              # How many LEDs to light.
        LED_FREQ_HZ = 800000        # Frequency of the LED signal.  Should be 800khz or 400khz.
        LED_DMA_NUM = 10            # DMA channel to use, can be 0-14.
        LED_GPIO = 18               # GPIO connected to the LED signal line.  Must support PWM!
        LED_BRIGHTNESS = 255        # Set to 0 for darkest and 255 for brightest
        LED_INVERT = 0              # Set to 1 to invert the LED signal, good if using NPN

        leds = ws.new_ws2811_t()

        # Initialize all channels to off
        for channum in range(2):
            channel = ws.ws2811_channel_get(leds, channum)
            ws.ws2811_channel_t_count_set(channel, 0)
            ws.ws2811_channel_t_gpionum_set(channel, 0)
            ws.ws2811_channel_t_invert_set(channel, 0)
            ws.ws2811_channel_t_brightness_set(channel, 0)

        channel = ws.ws2811_channel_get(leds, LED_CHANNEL)

        ws.ws2811_channel_t_count_set(channel, LED_COUNT)
        ws.ws2811_channel_t_gpionum_set(channel, LED_GPIO)
        ws.ws2811_channel_t_invert_set(channel, LED_INVERT)
        ws.ws2811_channel_t_brightness_set(channel, LED_BRIGHTNESS)

        ws.ws2811_t_freq_set(leds, LED_FREQ_HZ)
        ws.ws2811_t_dmanum_set(leds, LED_DMA_NUM)

        resp = ws.ws2811_init(leds)
        if resp != ws.WS2811_SUCCESS:
            message = ws.ws2811_get_return_t_str(resp)
            raise RuntimeError('ws2811_init failed with code {0} ({1})'.format(resp, message))

        self.leds = leds
        self.channel = ws.ws2811_channel_get(leds, LED_CHANNEL)
        self.brightness = LED_BRIGHTNESS
        self.led_count = LED_COUNT

    @staticmethod
    @njit
    def _set_all_pixels(channel, colors):
        """
        Update the color of all pixels efficiently using Numba.

        Args:
            channel: The channel object from _rpi_ws281x.
            colors: A 1D numpy array of np.uint32, where each element is a color.
        """
        for pixel_id in range(len(colors)):
            ws.ws2811_led_set(channel, pixel_id, colors[pixel_id])

    def set_pixel_colors(self, colors):
        """
        Updates all pixel colors at once.

        Args:
            colors: A 1D numpy array of np.uint32 values, where each element is a color.
        """
        if len(colors) != self.led_count:
            raise ValueError("Length of colors array must match the number of LEDs.")

        self._set_all_pixels(self.channel, colors)

    def refresh_display(self):
        resp = ws.ws2811_render(self.leds)
        if resp != ws.WS2811_SUCCESS:
            message = ws.ws2811_get_return_t_str(resp)
            raise RuntimeError('ws2811_render failed with code {0} ({1})'.format(resp, message))

    def change_brightness(self, incr):
        self.brightness = max(0, min(self.brightness + incr, 255))
        ws.ws2811_channel_t_brightness_set(self.channel, self.brightness)
        resp = ws.ws2811_init(self.leds)
        if resp != ws.WS2811_SUCCESS:
            message = ws.ws2811_get_return_t_str(resp)
            raise RuntimeError('ws2811_init failed with code {0} ({1})'.format(resp, message))

    def turn_off(self):
        for i in range(self.led_count):
            ws.ws2811_led_set(self.channel, i, 0)
        resp = ws.ws2811_render(self.leds)
        if resp != ws.WS2811_SUCCESS:
            message = ws.ws2811_get_return_t_str(resp)
            raise RuntimeError('ws2811_render failed with code {0} ({1})'.format(resp, message))
        ws.ws2811_fini(self.leds)
        ws.delete_ws2811_t(self.leds)