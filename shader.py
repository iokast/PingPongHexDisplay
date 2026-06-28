# shader.py

import os
import time
import ctypes
import numpy as np

from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
from pyglet.gl import Config, Context

from hex_mask import cartesian_coords
from scipy.ndimage import gaussian_filter


class Shader:

    def __init__(self, color_palette, alpha):

        self.colors = color_palette
        self.brightness = alpha

        self.start_time = time.time()
        self.frame = 0

        self.blur_sigma = 1.0

        self.shader_files = sorted([
            os.path.join("shaders", f)
            for f in os.listdir("shaders")
            if f.endswith(".fs")
        ])

        self.shader_id = 0

        with open(self.shader_files[0], "r") as f:
            self.shadertoy_code = f.read()

        self.build_pixel_map()

        self.iResolution = (
            float(self.canvas_size),
            float(self.canvas_size)
        )


    def build_pixel_map(self):

        coords = cartesian_coords.astype(float)

        # cartesian_coords convention:
        #
        # coords[:,0] = row / Y
        # coords[:,1] = column / X

        center_y = (
            np.max(coords[:, 0]) +
            np.min(coords[:, 0])
        ) / 2.0

        center_x = (
            np.max(coords[:, 1]) +
            np.min(coords[:, 1])
        ) / 2.0

        coords[:,0] -= center_y
        coords[:,1] -= center_x


        max_extent = max(
            np.max(np.abs(coords[:,0])),
            np.max(np.abs(coords[:,1]))
        )

        padding = 4

        self.canvas_size = int(
            max_extent * 2 + padding
        )


        # Convert to framebuffer coordinates
        #
        # Here we intentionally DO NOT invert Y.
        # glReadPixels() inversion is handled later
        # by np.flipud()

        x = (
            coords[:,1] +
            self.canvas_size / 2
        )

        y = (
            coords[:,0] +
            self.canvas_size / 2
        )


        self.pixel_map = np.column_stack(
            (
                x.astype(int),
                y.astype(int)
            )
        )


    def change_shader(self):

        self.shader_id = (
            self.shader_id + 1
        ) % len(self.shader_files)

        print(
            "Loading shader:",
            self.shader_files[self.shader_id]
        )

        with open(
            self.shader_files[self.shader_id],
            "r"
        ) as f:
            self.shadertoy_code = f.read()

        self.shader_program = self.compile_shaders()


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

        code = code.replace(
            "texture(",
            "texture2D("
        )

        code = code.replace(
            "round(",
            "floor("
        )

        return code


    def initialize_opengl(self):

        config = Config(
            double_buffer=True,
            depth_size=16
        )

        self.context = Context(config)

        glClearColor(
            0,
            0,
            0,
            1
        )

        self.shader_program = self.compile_shaders()

        self.vao = self.create_buffer(
            self.shader_program
        )

        self.iResolution_location = glGetUniformLocation(
            self.shader_program,
            "iResolution"
        )

        self.iTime_location = glGetUniformLocation(
            self.shader_program,
            "iTime"
        )

        self.iFrame_location = glGetUniformLocation(
            self.shader_program,
            "iFrame"
        )

        self.fbo = glGenFramebuffers(1)

        glBindFramebuffer(
            GL_FRAMEBUFFER,
            self.fbo
        )

        self.texture = glGenTextures(1)

        glBindTexture(
            GL_TEXTURE_2D,
            self.texture
        )

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

        glTexParameteri(
            GL_TEXTURE_2D,
            GL_TEXTURE_MIN_FILTER,
            GL_LINEAR
        )

        glTexParameteri(
            GL_TEXTURE_2D,
            GL_TEXTURE_MAG_FILTER,
            GL_LINEAR
        )

        glFramebufferTexture2D(
            GL_FRAMEBUFFER,
            GL_COLOR_ATTACHMENT0,
            GL_TEXTURE_2D,
            self.texture,
            0
        )

        if glCheckFramebufferStatus(
            GL_FRAMEBUFFER
        ) != GL_FRAMEBUFFER_COMPLETE:

            raise RuntimeError(
                "Framebuffer incomplete"
            )

        glBindFramebuffer(
            GL_FRAMEBUFFER,
            0
        )


    def compile_shaders(self):

        vertex_shader = """

        #version 100

        attribute vec2 position;

        void main()
        {
            gl_Position =
                vec4(position,0.0,1.0);
        }

        """

        fragment_header = """

        #version 100

        precision mediump float;

        uniform vec2 iResolution;
        uniform float iTime;
        uniform int iFrame;

        """

        fragment_shader = (
            fragment_header +
            self.prepare_shadertoy_shader(
                self.shadertoy_code
            ) +
            """

            void main()
            {
                vec4 fragColor =
                    vec4(0.0);

                mainImage(
                    fragColor,
                    gl_FragCoord.xy
                );

                gl_FragColor =
                    fragColor;
            }

            """
        )

        return compileProgram(

            compileShader(
                vertex_shader,
                GL_VERTEX_SHADER
            ),

            compileShader(
                fragment_shader,
                GL_FRAGMENT_SHADER
            )
        )


    def create_buffer(self, shader_program):

        vertices = np.array(
            [
                -1,-1,
                 1,-1,
                 1, 1,
                -1, 1
            ],
            dtype=np.float32
        )

        vao = glGenVertexArrays(1)

        glBindVertexArray(
            vao
        )

        buffer = glGenBuffers(1)

        glBindBuffer(
            GL_ARRAY_BUFFER,
            buffer
        )

        glBufferData(
            GL_ARRAY_BUFFER,
            vertices.nbytes,
            vertices,
            GL_STATIC_DRAW
        )

        position = glGetAttribLocation(
            shader_program,
            "position"
        )

        glVertexAttribPointer(
            position,
            2,
            GL_FLOAT,
            False,
            8,
            ctypes.c_void_p(0)
        )

        glEnableVertexAttribArray(
            position
        )

        return vao


    def generate_frame(self):

        glBindFramebuffer(
            GL_FRAMEBUFFER,
            self.fbo
        )

        glViewport(
            0,
            0,
            self.canvas_size,
            self.canvas_size
        )

        glClear(
            GL_COLOR_BUFFER_BIT
        )

        glUseProgram(
            self.shader_program
        )

        elapsed = (
            time.time()
            -
            self.start_time
        )

        glUniform2f(
            self.iResolution_location,
            *self.iResolution
        )

        glUniform1f(
            self.iTime_location,
            elapsed
        )

        glUniform1i(
            self.iFrame_location,
            self.frame
        )

        self.frame += 1

        glBindVertexArray(
            self.vao
        )

        glDrawArrays(
            GL_TRIANGLE_FAN,
            0,
            4
        )

        pixels = glReadPixels(
            0,
            0,
            self.canvas_size,
            self.canvas_size,
            GL_RGB,
            GL_UNSIGNED_BYTE
        )

        pixels = np.frombuffer(
            pixels,
            dtype=np.uint8
        )

        pixels = pixels.reshape(
            self.canvas_size,
            self.canvas_size,
            3
        )

        pixels = np.flipud(
            pixels
        )

        glBindFramebuffer(
            GL_FRAMEBUFFER,
            0
        )

        return gaussian_filter(
            pixels,
            sigma=(
                self.blur_sigma,
                self.blur_sigma,
                0
            )
        )


    def update(self, state):

        frame = self.generate_frame()

        for led_id, (x, y) in enumerate(
            self.pixel_map
        ):

            state[led_id] = frame[y, x]

        return (
            state *
            self.brightness
        )