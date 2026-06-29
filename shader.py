import os
import time
import ctypes
import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
from pyglet.gl import Config, Context
from hex_mask import cartesian_coords, adjacency, cube_coords

class Shader:
    def __init__(self, color_palette, alpha):
        self.colors = color_palette
        self.brightness = alpha
        self.start_time = time.time()
        self.frame = 0

        # Smoothing controls.
        self.shader_time_scale = 1.0          # Lower = slower animation.
        self.neighbor_strength = 0.0         # Higher = more spatial smoothing.
        self.temporal_alpha = 0.35            # Lower = smoother/slower frame changes.
        self.previous_led_frame = None

        # Render only the samples needed by the LEDs instead of drawing an
        # entire square image. Set this to False if a shader relies on
        # screen-space derivatives or neighboring fragments.
        self.render_leds_only = os.environ.get("PPL_FULL_FRAME_SHADER") != "1"

        # Seven samples cover each LED's hexagonal footprint. The center has
        # weight 2 and each surrounding sample has weight 1, making the total
        # weight 8 so averaging can use a cheap integer divide.
        self.supersample = (
            self.render_leds_only and
            os.environ.get("PPL_SUPERSAMPLE", "1") != "0"
        )
        self.sample_radius = float(os.environ.get("PPL_SAMPLE_RADIUS", "0.45"))
        self.shader_zoom = float(os.environ.get("PPL_SHADER_ZOOM", "1.2"))
        self.sample_offsets = self.build_sample_offsets()
        self.heavy_shaders = {
            "cineshader_laval.fs",
            "flame.fs",
            "protean_clouds.fs",
        }

        self.shader_files = sorted([
            os.path.join("shaders", f)
            for f in os.listdir("shaders")
            if f.endswith(".fs")
        ])

        self.shader_id = 0
        with open(self.shader_files[self.shader_id], "r") as f:
            self.shadertoy_code = f.read()

        self.build_pixel_map()
        self.build_neighbor_map()
        self.iResolution = (float(self.canvas_size), float(self.canvas_size))

    def build_sample_offsets(self):
        if not self.supersample:
            return np.zeros((1, 2), dtype=np.float32)

        # Put the center and a symmetric three-point ring first so heavy
        # shaders can draw only those four rows without rebuilding buffers.
        angles = np.array([0, 2, 4, 1, 3, 5], dtype=np.float32) * (np.pi / 3.0)
        ring = np.column_stack((np.cos(angles), np.sin(angles)))
        ring *= self.sample_radius
        return np.vstack((np.zeros((1, 2), dtype=np.float32), ring)).astype(np.float32)

    @property
    def output_width(self):
        if self.render_leds_only:
            return len(self.pixel_map)
        return self.canvas_size

    @property
    def output_height(self):
        if self.render_leds_only:
            return len(self.sample_offsets)
        return self.canvas_size

    @property
    def active_sample_count(self):
        if not self.supersample:
            return 1
        shader_name = os.path.basename(self.shader_files[self.shader_id])
        if shader_name in self.heavy_shaders:
            requested = int(os.environ.get("PPL_HEAVY_SAMPLES", "4"))
            return requested if requested in (4, 7) else 4
        return len(self.sample_offsets)

    def build_neighbor_map(self):
        self.neighbor_ids = []
        for led_id in range(len(adjacency)):
            neighbors = [n for n in adjacency[led_id] if n is not None]
            self.neighbor_ids.append(np.array(neighbors, dtype=np.int32))

    def build_pixel_map(self):
        coords = cartesian_coords.astype(float)

        # Use the true center LED: cube coordinate [0,0,0].
        center_led = np.where(np.all(cube_coords == [0, 0, 0], axis=1))[0][0]
        center_y = coords[center_led, 0]
        center_x = coords[center_led, 1]

        coords[:, 0] -= center_y
        coords[:, 1] -= center_x

        max_extent = max(
            np.max(np.abs(coords[:, 0])),
            np.max(np.abs(coords[:, 1]))
        )

        self.canvas_size = int(np.ceil(max_extent * 2 + 7))
        if self.canvas_size % 2 == 0:
            self.canvas_size += 1

        center_pixel = self.canvas_size // 2

        # Optional fine tuning, in framebuffer pixels.
        # If image appears shifted up/right, try negative values.
        self.display_offset_x = 0.0
        self.display_offset_y = 0.0

        x = coords[:, 1] + center_pixel + self.display_offset_x
        y = coords[:, 0] + center_pixel + self.display_offset_y

        self.pixel_map = np.column_stack((
            np.rint(x).astype(int),
            np.rint(y).astype(int)
        ))

        self.pixel_map[:, 0] = np.clip(self.pixel_map[:, 0], 0, self.canvas_size - 1)
        self.pixel_map[:, 1] = np.clip(self.pixel_map[:, 1], 0, self.canvas_size - 1)

    def change_shader(self):
        self.shader_id = (self.shader_id + 1) % len(self.shader_files)
        print("Loading shader:", self.shader_files[self.shader_id])

        with open(self.shader_files[self.shader_id], "r") as f:
            self.shadertoy_code = f.read()

        old_program = self.shader_program
        old_vao = self.vao
        self.shader_program = self.compile_shaders()
        self.vao = self.create_buffer(self.shader_program)
        self.cache_uniform_locations()
        self.previous_led_frame = None
        glDeleteVertexArrays(1, [old_vao])
        glDeleteProgram(old_program)

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

        if self.render_leds_only:
            code = code.replace("gl_FragCoord.xy", "shaderFragCoord")

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

        output_width = self.output_width
        output_height = self.output_height
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGB,
            output_width,
            output_height,
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
        if self.render_leds_only:
            vertex_shader = """
            #version 100
            attribute vec2 outputPosition;
            attribute vec2 sampleCoord;
            varying vec2 shaderFragCoord;
            void main()
            {
                gl_Position = vec4(outputPosition, 0.0, 1.0);
                gl_PointSize = 1.0;
                shaderFragCoord = sampleCoord;
            }
            """
        else:
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

        if self.render_leds_only:
            fragment_header += "varying vec2 shaderFragCoord;\n"

        fragment_coordinate = "shaderFragCoord" if self.render_leds_only else "gl_FragCoord.xy"

        fragment_shader = (
            fragment_header +
            self.prepare_shadertoy_shader(self.shadertoy_code) +
            """
            void main()
            {
                vec4 fragColor = vec4(0.0);
                mainImage(fragColor, """ + fragment_coordinate + """);
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
        if self.render_leds_only:
            # The previous full-frame render was flipped vertically before
            # sampling. Convert each LED location back to OpenGL coordinates.
            sample_centers = np.column_stack((
                self.pixel_map[:, 0].astype(np.float32) + 0.5,
                self.canvas_size - self.pixel_map[:, 1].astype(np.float32) - 0.5,
            ))
            canvas_center = np.array(
                [self.canvas_size / 2.0, self.canvas_size / 2.0],
                dtype=np.float32,
            )
            sample_centers = canvas_center + (
                sample_centers - canvas_center
            ) * self.shader_zoom
            # Sample-major ordering matches glReadPixels' row-major layout.
            sample_coords = (
                sample_centers[np.newaxis, :, :] +
                self.sample_offsets[:, np.newaxis, :]
            ).reshape(-1, 2)
            output_x = ((np.arange(self.output_width, dtype=np.float32) + 0.5) /
                        self.output_width) * 2.0 - 1.0
            output_y = ((np.arange(self.output_height, dtype=np.float32) + 0.5) /
                        self.output_height) * 2.0 - 1.0
            output_positions = np.stack(np.meshgrid(output_x, output_y), axis=-1).reshape(-1, 2)
            vertices = np.column_stack((output_positions, sample_coords)).astype(np.float32)

            vao = glGenVertexArrays(1)
            glBindVertexArray(vao)
            vertex_buffer = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, vertex_buffer)
            glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

            stride = vertices.strides[0]
            output_position_location = glGetAttribLocation(shader_program, "outputPosition")
            sample_coord_location = glGetAttribLocation(shader_program, "sampleCoord")
            glVertexAttribPointer(output_position_location, 2, GL_FLOAT, False, stride, ctypes.c_void_p(0))
            glVertexAttribPointer(sample_coord_location, 2, GL_FLOAT, False, stride, ctypes.c_void_p(8))
            glEnableVertexAttribArray(output_position_location)
            glEnableVertexAttribArray(sample_coord_location)
            return vao

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
        output_width = self.output_width
        output_height = self.output_height
        glViewport(0, 0, output_width, output_height)
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
        if self.render_leds_only:
            glDrawArrays(GL_POINTS, 0, self.output_width * self.active_sample_count)
        else:
            glDrawArrays(GL_TRIANGLE_FAN, 0, 4)

        glPixelStorei(GL_PACK_ALIGNMENT, 1)
        pixels = glReadPixels(
            0,
            0,
            output_width,
            output_height,
            GL_RGB,
            GL_UNSIGNED_BYTE
        )

        pixels = np.frombuffer(pixels, dtype=np.uint8)
        pixels = pixels.reshape(output_height, output_width, 3)

        if not self.render_leds_only:
            pixels = np.flipud(pixels)

        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        return pixels

    def sample_led_pixels(self, frame):
        if self.render_leds_only:
            samples = frame.transpose(1, 0, 2)
            sample_count = self.active_sample_count
            if sample_count == 1:
                return samples[:, 0].astype(np.float32)

            # uint16 safely holds the maximum weighted total (8 * 255).
            samples = samples.astype(np.uint16)
            if sample_count == 4:
                return (samples[:, :4].sum(axis=1, dtype=np.uint16) >> 2).astype(np.float32)

            filtered = samples[:, 0] * 2
            filtered += samples[:, 1:].sum(axis=1, dtype=np.uint16)
            return (filtered >> 3).astype(np.float32)

        return frame[self.pixel_map[:, 1], self.pixel_map[:, 0]].astype(np.float32)

    def smooth_led_neighbors(self, led_frame):
        if self.neighbor_strength <= 0:
            return led_frame

        smoothed = led_frame.copy()
        s = self.neighbor_strength

        for led_id, neighbors in enumerate(self.neighbor_ids):
            if neighbors.size == 0:
                continue

            neighbor_avg = led_frame[neighbors].mean(axis=0)
            smoothed[led_id] = (1.0 - s) * led_frame[led_id] + s * neighbor_avg

        return smoothed

    def smooth_temporal(self, led_frame):
        if self.temporal_alpha >= 1.0:
            self.previous_led_frame = led_frame.copy()
            return led_frame

        if self.previous_led_frame is None:
            self.previous_led_frame = led_frame.copy()
            return led_frame

        self.previous_led_frame *= 1.0 - self.temporal_alpha
        self.previous_led_frame += self.temporal_alpha * led_frame
        return self.previous_led_frame

    def update(self, state):
        frame = self.generate_frame()
        led_frame = self.sample_led_pixels(frame)
        led_frame = self.smooth_led_neighbors(led_frame)
        led_frame = self.smooth_temporal(led_frame)

        state[:] = led_frame * self.brightness
        return state
