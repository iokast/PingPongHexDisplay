import os

abspath = os.path.abspath(__file__)
os.chdir(os.path.dirname(abspath))

import numpy as np
import pygame as pg

from clock import Clock
from day_night import DayNight
from expanse import Expanse
from hex_mask import cartesian_coords, color_palette_11, gamma_adj
from shader import Shader
from spin import Spin
from solar_dimmer import SolarDimmer


class Simulator:
    """Hardware-free desktop preview of the Raspberry Pi render pipeline."""

    HELP_LINES = (
        "B: next background",
        "C: change current palette / shader",
        "S: next shader (when Shader is active)",
        "K: next clock style",
        "V: next clock color mode",
        "Up/Down: background brightness",
        "Right/Left: clock brightness",
        "A: toggle automatic solar dimmer preview",
        "G: toggle hardware gamma preview",
        "Space: pause / wake",
        "F12: save screenshot",
        "H: toggle this help",
        "Q or Escape: quit",
    )

    def __init__(self, size=(1240, 900), hex_radius=20, target_fps=60):
        self.size = np.asarray(size, dtype=int)
        self.display_size = np.array([900, self.size[1]], dtype=float)
        self.center = self.display_size / 2
        self.hex_radius = hex_radius
        self.dot_radius = max(2, int(hex_radius * 0.82))
        self.target_fps = target_fps
        self.running = True
        self.is_on = True
        self.show_help = True
        # The Pi's LED gamma LUT looks unnaturally dark on an already
        # gamma-corrected desktop monitor. It remains available with G.
        self.apply_gamma = False
        self.auto_dimmer = True
        self.status_message = "Ready"

        self.brightness_background = 1.0
        self.brightness_clock = 0.6
        self.colors_id = 0
        self.colors = color_palette_11[self.colors_id]
        self.gamma_adj = np.asarray(gamma_adj)
        self.state = np.zeros((397, 3), dtype=np.int16)
        self.display_state = np.zeros((397, 3), dtype=np.uint8)

        self.dimmer = SolarDimmer()
        self.dimmer_brightness = 1.0
        self.dimmer_status = "animation lighting"

        self._init_pygame()
        self._build_pixel_positions()

        self.shader_animation = Shader(self.colors, self.brightness_background)
        self.background_animations = [
            DayNight(self.colors, self.brightness_background),
            self.shader_animation,
            Expanse(self.colors, self.brightness_background),
            Spin(self.colors, self.brightness_background),
        ]
        self.background_animation_id = 1
        self.clock_animation = Clock(
            [255, 255, 255],
            alpha=self.brightness_clock,
            clock_type=0,
        )

        # Keep shader behavior identical to the Pi and ready for instant
        # background switching, while importing no LED/native Pi modules.
        self.shader_animation.initialize_opengl()
        self.print_controls()

    @property
    def active_animation(self):
        return self.background_animations[self.background_animation_id]

    @property
    def active_animation_name(self):
        return type(self.active_animation).__name__

    def _init_pygame(self):
        pg.init()
        self.surface = pg.display.set_mode(self.size)
        self.frame_clock = pg.time.Clock()
        self.font = pg.font.SysFont("Consolas", 12)

    def _build_pixel_positions(self):
        # cartesian_coords is the authoritative physical LED layout. Its
        # columns are (y, x); converting to screen (x, y) already places the
        # intended point at 12 o'clock.
        positions = np.column_stack((cartesian_coords[:, 1], cartesian_coords[:, 0]))
        positions -= (positions.min(axis=0) + positions.max(axis=0)) / 2.0

        span = positions.max(axis=0) - positions.min(axis=0)
        available = self.display_size * 0.86
        scale = np.min(available / span)
        self.pixel_positions = positions * scale + self.center
        self.dot_radius = max(2, int(scale * 0.43))

    def print_controls(self):
        print("Desktop display simulator controls:")
        for line in self.HELP_LINES:
            print("  " + line)

    def set_background_brightness(self, change):
        self.brightness_background = float(np.clip(
            self.brightness_background + change, 0.0, 1.0
        ))
        for animation in self.background_animations:
            animation.set_brightness(self.brightness_background)
        self.dimmer.start_override()

    def set_clock_brightness(self, change):
        self.brightness_clock = float(np.clip(
            self.brightness_clock + change, 0.0, 1.0
        ))
        self.clock_animation.set_brightness(self.brightness_clock)
        self.dimmer.start_override()

    def change_background(self):
        self.background_animation_id = (
            self.background_animation_id + 1
        ) % len(self.background_animations)
        self.status_message = f"Switched to {self.active_animation_name}"

    def change_current_color_or_shader(self):
        animation = self.active_animation
        if isinstance(animation, Shader):
            self.change_shader_safely()
            return
        if isinstance(animation, DayNight):
            return
        self.colors_id = (self.colors_id + 1) % len(color_palette_11)
        self.colors = color_palette_11[self.colors_id]
        animation.set_palette(self.colors, self.brightness_background)
        self.status_message = f"Palette {self.colors_id} selected"

    def change_shader_safely(self):
        previous_name = self.shader_animation.current_shader_name
        try:
            self.shader_animation.change_shader()
        except Exception as exc:
            self.status_message = f"Shader error: {str(exc).splitlines()[0]}"
            print(f"Failed to change from {previous_name}:\n{exc}")
            return False
        if "iChannel" in self.shader_animation.shadertoy_code:
            self.status_message = (
                f"Loaded {self.shader_animation.current_shader_name} (channel input unavailable)"
            )
        else:
            self.status_message = f"Loaded {self.shader_animation.current_shader_name}"
        return True

    def handle_key(self, key):
        if key in (pg.K_ESCAPE, pg.K_q):
            self.running = False
        elif key == pg.K_b:
            self.change_background()
        elif key == pg.K_c:
            self.change_current_color_or_shader()
        elif key == pg.K_s and isinstance(self.active_animation, Shader):
            self.change_shader_safely()
        elif key == pg.K_k:
            self.clock_animation.change_type()
        elif key == pg.K_v:
            self.clock_animation.change_color_type()
        elif key == pg.K_UP:
            self.set_background_brightness(0.05)
        elif key == pg.K_DOWN:
            self.set_background_brightness(-0.05)
        elif key == pg.K_RIGHT:
            self.set_clock_brightness(0.05)
        elif key == pg.K_LEFT:
            self.set_clock_brightness(-0.05)
        elif key == pg.K_a:
            self.auto_dimmer = not self.auto_dimmer
        elif key == pg.K_g:
            self.apply_gamma = not self.apply_gamma
        elif key == pg.K_SPACE:
            self.is_on = not self.is_on
        elif key == pg.K_h:
            self.show_help = not self.show_help
        elif key == pg.K_F12:
            pg.image.save(self.surface, "simulator_screenshot.png")

    def handle_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            elif event.type == pg.KEYDOWN:
                self.handle_key(event.key)

    def update(self):
        if not self.is_on:
            self.display_state.fill(0)
            return

        state = self.state
        state.fill(0)
        background = self.active_animation
        state = background.update(state)
        state = self.clock_animation.update(state)

        if isinstance(background, DayNight) or not self.auto_dimmer:
            self.dimmer_brightness = 1.0
            self.dimmer_status = (
                "animation lighting" if isinstance(background, DayNight)
                else "dimmer disabled"
            )
        else:
            self.dimmer_brightness = self.dimmer.brightness()
            self.dimmer_status = self.dimmer.state()
        if self.dimmer_brightness != 1.0:
            state = (state * self.dimmer_brightness).astype(np.int16)

        state = np.clip(state, 0, 255).astype(np.int16)
        if self.apply_gamma:
            state = self.gamma_adj[state]
        self.display_state[:] = state.astype(np.uint8)

    def status_text(self):
        details = self.active_animation_name
        if isinstance(self.active_animation, Shader):
            details += f" / {self.shader_animation.current_shader_name}"
        return (
            f"{self.frame_clock.get_fps():4.1f} FPS | {details} | "
            f"BG {self.brightness_background * 100:.0f}% | "
            f"Clock {self.brightness_clock * 100:.0f}% | "
            f"Dim {self.dimmer_brightness * 100:.0f}% {self.dimmer_status} | "
            f"Gamma {'on' if self.apply_gamma else 'off'}"
        )

    def draw(self):
        self.surface.fill((5, 5, 8))
        for pixel_id, position in enumerate(self.pixel_positions):
            color = tuple(int(value) for value in self.display_state[pixel_id])
            pg.draw.circle(self.surface, color, position.astype(int), self.dot_radius)

        if self.show_help:
            panel_x = int(self.display_size[0] + 8)
            panel_width = int(self.size[0] - panel_x - 8)
            overlay = pg.Surface(
                (panel_width, 82 + len(self.HELP_LINES) * 16),
                pg.SRCALPHA,
            )
            overlay.fill((12, 12, 16, 235))
            current = self.active_animation_name
            if isinstance(self.active_animation, Shader):
                current += f": {self.shader_animation.current_shader_name}"
            overlay.blit(self.font.render("Current animation", True, (170, 190, 255)), (10, 8))
            overlay.blit(self.font.render(current, True, (255, 255, 255)), (10, 25))
            overlay.blit(self.font.render(self.status_message, True, (190, 205, 190)), (10, 44))
            overlay.blit(self.font.render("Controls", True, (170, 190, 255)), (10, 65))
            for index, line in enumerate(self.HELP_LINES):
                text = self.font.render(line, True, (215, 215, 220))
                overlay.blit(text, (10, 82 + index * 16))
            self.surface.blit(overlay, (panel_x, 12))

        pg.display.set_caption(self.status_text())
        pg.display.flip()

    def close(self):
        try:
            self.shader_animation.close()
        finally:
            pg.quit()

    def run(self):
        try:
            while self.running:
                self.handle_events()
                self.update()
                self.draw()
                self.frame_clock.tick(self.target_fps)
        finally:
            self.close()


if __name__ == "__main__":
    Simulator().run()
