import os
import time
import ctypes
import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
from pyglet.gl import Config, Context
from hex_mask import cartesian_coords, adjacency

class Shader:
    def __init__(self, color_palette, alpha):
        self.colors = color_palette
        self.brightness = alpha
        self.start_time = time.time()
        self.frame = 0

        # Smoothing controls.
        self.shader_time_scale = 0.5          # Lower = slower animation.
        self.neighbor_strength = 0.30         # Higher = more spatial smoothing.
        self.temporal_alpha = 0.35            # Lower = smoother/slower frame changes.
        self.previous_led_frame = None

        self.shader_files = sorted([
            os.path.join("shaders", f)
            for f in os.listdir("shaders")
            if f.endswith(".fs")
        ])

        self.shader_id = 0
        with open(self.shader_files[self.shader_id], "r") as f:
            self.shadertoy_code = f.read()

        self.build_pixel_map()
        self.iResolution = (float(self.canvas_size), float(self.canvas_size))

    def build_pixel_map(self):
        coords = cartesian_coords.astype(float)

        # cartesian_coords convention:
        # coords[:,0] = display row / Y
        # coords[:,1] = display column / X
        center_y = (np.max(coords[:, 0]) + np.min(coords[:, 0])) / 2.0
        center_x = (np.max(coords[:, 1]) + np.min(coords[:, 1])) / 2.0

        coords[:, 0] -= center_y
        coords[:, 1] -= center_x

        max_extent = max(
            np.max(np.abs(coords[:, 0])),
            np.max(np.abs(coords[:, 1]))
        )

        # Small padding prevents edge LEDs from clipping.
        self.canvas_size = int(max_extent * 2 + 4)

        x = coords[:, 1] + self.canvas_size / 2
        y = coords[:, 0] + self.canvas_size / 2

        self.pixel_map = np.column_stack((x.astype(int), y.astype(int)))

    def change_shader(self):
        self.shader_id = (self.shader_id + 1) % len(self.shader_files)
        print("Loading shader:", self.shader_files[self.shader_id])

        with open(self.shader_files[self.shader_id], "r") as f:
            self.shadertoy_code = f.read()

        self.shader_program = self.compile_shaders()
        self.cache_uniform_locations()
        self.previous_led_frame = None

    def set_palette(self, colors, brightness):
        if colors != self.colors:
            self.colors = colors
            self.change_shader()
        self.brightness = brightness

    def prepare_shadertoy_shader(self, code):
        lines = []
        for line in code.split("\n"):
            if "#version" not in line:
                lines.append(line)

        code = "\n".join(lines)
        code = code.replace("texture(", "texture2D(")
        code = code.replace("round(", "floor(")

        if "float jTime;" in code:
            code = code.replace("float jTime;", "float jTime = 0.0;")

        return code

    def initialize_opengl(self):
        config = Config(double_buffer=True, depth_size=16)
        self.context = Context(config)

        glClearColor(0.0, 0.0, 0.0, 1.0)

        self.shader_program = self.compile_shaders()
        self.vao = self.create_buffer(self.shader_program)
        self.cache_uniform_locations()

        self.fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)

        self.texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture)

        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGB,
            self.canvas_size,
            self.canvas_size,
            0,
            GL_RGB,
            GL_UNSIGNED_BYTE,
            None
        )

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        glFramebufferTexture2D(
            GL_FRAMEBUFFER,
            GL_COLOR_ATTACHMENT0,
            GL_TEXTURE_2D,
            self.texture,
            0
        )

        if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
            raise RuntimeError("Framebuffer incomplete")

        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def cache_uniform_locations(self):
        self.iResolution_location = glGetUniformLocation(
            self.shader_program,
            "iResolution"
        )

        self.iTime_location = glGetUniformLocation(
            self.shader_program,
            "iTime"
        )

        self.iTimeDelta_location = glGetUniformLocation(
            self.shader_program,
            "iTimeDelta"
        )

        self.iFrame_location = glGetUniformLocation(
            self.shader_program,
            "iFrame"
        )

        self.iMouse_location = glGetUniformLocation(
            self.shader_program,
            "iMouse"
        )

    def compile_shaders(self):
        vertex_shader = """
        #version 100
        attribute vec2 position;
        void main()
        {
            gl_Position = vec4(position,0.0,1.0);
        }
        """

        fragment_header = """
        #version 100
        precision mediump float;
        uniform vec2 iResolution;
        uniform float iTime;
        uniform float iTimeDelta;
        uniform int iFrame;
        uniform vec4 iMouse;
        uniform sampler2D iChannel0;
        uniform sampler2D iChannel1;
        uniform sampler2D iChannel2;
        uniform sampler2D iChannel3;
        uniform vec3 iChannelResolution[4];
        """

        fragment_shader = (
            fragment_header +
            self.prepare_shadertoy_shader(self.shadertoy_code) +
            """
            void main()
            {
                vec4 fragColor = vec4(0.0);
                mainImage(fragColor, gl_FragCoord.xy);
                gl_FragColor = fragColor;
            }
            """
        )

        try:
            vertex_shader_obj = compileShader(vertex_shader, GL_VERTEX_SHADER)
            fragment_shader_obj = compileShader(fragment_shader, GL_FRAGMENT_SHADER)
            return compileProgram(vertex_shader_obj, fragment_shader_obj)
        except Exception as e:
            print("Shader compilation failed:")
            print(fragment_shader)
            raise e

    def create_buffer(self, shader_program):
        vertices = np.array([
            -1.0, -1.0,
             1.0, -1.0,
             1.0,  1.0,
            -1.0,  1.0
        ], dtype=np.float32)

        vao = glGenVertexArrays(1)
        glBindVertexArray(vao)

        vertex_buffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vertex_buffer)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        position = glGetAttribLocation(shader_program, "position")

        glVertexAttribPointer(
            position,
            2,
            GL_FLOAT,
            False,
            8,
            ctypes.c_void_p(0)
        )

        glEnableVertexAttribArray(position)
        return vao

    def generate_frame(self):
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        glViewport(0, 0, self.canvas_size, self.canvas_size)
        glClear(GL_COLOR_BUFFER_BIT)
        glUseProgram(self.shader_program)

        elapsed = (time.time() - self.start_time) * self.shader_time_scale

        glUniform2f(self.iResolution_location, *self.iResolution)
        glUniform1f(self.iTime_location, elapsed)
        glUniform1f(self.iTimeDelta_location, 1.0 / 60.0)
        glUniform1i(self.iFrame_location, self.frame)
        glUniform4f(
            self.iMouse_location,
            0.0,
            0.0,
            0.0,
            0.0
        )

        self.frame += 1

        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLE_FAN, 0, 4)

        pixels = glReadPixels(
            0,
            0,
            self.canvas_size,
            self.canvas_size,
            GL_RGB,
            GL_UNSIGNED_BYTE
        )

        pixels = np.frombuffer(pixels, dtype=np.uint8)
        pixels = pixels.reshape(self.canvas_size, self.canvas_size, 3)
        pixels = np.flipud(pixels)

        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        return pixels

    def sample_led_pixels(self, frame):
        led_frame = np.zeros((self.pixel_map.shape[0], 3), dtype=np.float32)

        for led_id, xy in enumerate(self.pixel_map):
            x = xy[0]
            y = xy[1]
            led_frame[led_id] = frame[y, x]

        return led_frame

    def smooth_led_neighbors(self, led_frame):
        if self.neighbor_strength <= 0:
            return led_frame

        smoothed = led_frame.copy()

        for led_id in range(led_frame.shape[0]):
            neighbors = []

            for n in adjacency[led_id]:
                if n is not None:
                    neighbors.append(n)

            if len(neighbors) == 0:
                continue

            neighbor_avg = np.mean(led_frame[neighbors], axis=0)

            smoothed[led_id] = (
                (1.0 - self.neighbor_strength) * led_frame[led_id] +
                self.neighbor_strength * neighbor_avg
            )

        return smoothed

    def smooth_temporal(self, led_frame):
        if self.temporal_alpha >= 1.0:
            self.previous_led_frame = led_frame.copy()
            return led_frame

        if self.previous_led_frame is None:
            self.previous_led_frame = led_frame.copy()
            return led_frame

        smoothed = (
            self.temporal_alpha * led_frame +
            (1.0 - self.temporal_alpha) * self.previous_led_frame
        )

        self.previous_led_frame = smoothed.copy()
        return smoothed

    def update(self, state):
        frame = self.generate_frame()
        led_frame = self.sample_led_pixels(frame)
        led_frame = self.smooth_led_neighbors(led_frame)
        led_frame = self.smooth_temporal(led_frame)

        state[:] = led_frame * self.brightness
        return state