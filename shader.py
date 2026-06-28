# shader.py
#
# Optimized shader renderer for the PingPongHexDisplay
#
# Major changes from original:
#
# 1. The old version:
#
#       Shader framebuffer (50x50)
#               |
#               v
#       hex_mask lookup
#               |
#               v
#       397 LEDs
#
#    rendered many pixels that were never used.
#
#
# 2. New version:
#
#       Shader framebuffer
#               |
#               v
#       only extract physical LED coordinates
#               |
#               v
#       397 LEDs
#
#
# The shader still renders a 2D image because Shadertoy shaders
# require spatial information. However, the conversion step is now
# precomputed and efficient.
#


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


        # --------------------------------------------------------
        # Animation parameters
        # --------------------------------------------------------

        self.brightness = alpha

        self.colors = color_palette

        self.start_time = time.time()

        self.frame = 0


        # --------------------------------------------------------
        # Shader files
        # --------------------------------------------------------

        self.shader_files = []

        for file in os.listdir("shaders"):

            if file.endswith(".fs"):

                self.shader_files.append(
                    os.path.join("shaders", file)
                )


        self.shader_files.sort()


        self.shader_id = 0


        with open(
            self.shader_files[self.shader_id],
            "r"
        ) as f:

            self.shadertoy_code = f.read()



        # --------------------------------------------------------
        # Build optimized LED coordinate map
        #
        # cartesian_coords contains the physical hex layout.
        #
        # Example:
        #
        # LED 0 -> (x,y)
        # LED 1 -> (x,y)
        #
        # We convert this into framebuffer coordinates once.
        #
        # This replaces the old gif_coords lookup.
        # --------------------------------------------------------

        self.build_pixel_map()



        # --------------------------------------------------------
        # Rendering size
        #
        # Instead of always rendering 50x50:
        #
        # self.canvas_size = 50
        #
        # we calculate the smallest square that contains
        # the actual hex display.
        #
        # --------------------------------------------------------

        self.canvas_size = self.framebuffer_size



        self.iResolution = (
            self.canvas_size,
            self.canvas_size
        )



        self.blur_sigma = 1.0



    def build_pixel_map(self):

        #
        # cartesian_coords comes from hex_mask.py
        #
        # IMPORTANT:
        #
        # The original project treats:
        #
        #   cartesian_coords[:,0] = image row (Y)
        #   cartesian_coords[:,1] = image column (X)
        #
        # Keep this orientation!
        #

        coords = cartesian_coords.astype(float)


        #
        # Find center of the physical hex
        #

        center_y = (
            np.max(coords[:,0]) +
            np.min(coords[:,0])
        ) / 2.0


        center_x = (
            np.max(coords[:,1]) +
            np.min(coords[:,1])
        ) / 2.0



        #
        # Move hex center to (0,0)
        #

        coords[:,0] -= center_y
        coords[:,1] -= center_x



        #
        # Find the size needed to fit the hex
        #

        max_extent = max(
            np.max(np.abs(coords[:,0])),
            np.max(np.abs(coords[:,1]))
        )



        #
        # Add small padding so edge LEDs
        # are not clipped
        #

        padding = 2


        self.framebuffer_size = int(
            max_extent * 2 + padding
        )



        #
        # Convert centered coordinates into
        # OpenGL texture coordinates
        #
        # OpenGL origin is bottom-left.
        #
        # Pixel array origin is top-left.
        #

        x = (
            coords[:,1]
            +
            self.framebuffer_size / 2
        )


        y = (
            self.framebuffer_size / 2
            -
            coords[:,0]
        )



        #
        # Store lookup table:
        #
        # LED index -> framebuffer pixel
        #

        self.pixel_map = np.column_stack(
            (
                x.astype(int),
                y.astype(int)
            )
        )




    def set_palette(self, colors, brightness):


        if colors != self.colors:

            self.colors = colors

            self.change_shader()


        self.brightness = brightness



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



    def prepare_shadertoy_shader(self, code):


        lines = code.split("\n")


        filtered = []


        for line in lines:

            if "#version" not in line:

                filtered.append(line)


        code = "\n".join(filtered)



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


        self.shader_program = (
            self.compile_shaders()
        )



        self.vao = (
            self.create_buffer(
                self.shader_program
            )
        )



        #
        # Offscreen framebuffer
        #

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

        uniform float iTimeDelta;

        uniform int iFrame;


        """



        fragment_shader = (

            fragment_header +

            self.prepare_shadertoy_shader(
                self.shadertoy_code
            )

            +

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



        now = time.time()


        elapsed = (
            now -
            self.start_time
        )



        glUniform2f(
            glGetUniformLocation(
                self.shader_program,
                "iResolution"
            ),
            *self.iResolution
        )



        glUniform1f(
            glGetUniformLocation(
                self.shader_program,
                "iTime"
            ),
            elapsed
        )



        glUniform1i(
            glGetUniformLocation(
                self.shader_program,
                "iFrame"
            ),
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



        return pixels



    def update(self,state):


        frame = self.generate_frame()



        #
        # Only copy real LED pixels.
        #
        # No 50x50 mask lookup.
        #

        for led_id,xy in enumerate(
            self.pixel_map
        ):


            x,y = xy


            state[led_id,:] = (
                frame[y,x,:]
            )



        return (
            state *
            self.brightness
        )