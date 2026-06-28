# set working directory
import os
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import time
from pyglet.gl import Config, Context
from hex_mask import cartesian_coords
from scipy.ndimage import gaussian_filter


class Shader:

    def __init__(self, color_palette, alpha):

        self.blur_sigma = 1.0

        self.shader_files = []

        for file in os.listdir("shaders"):
            if file.endswith(".fs"):
                self.shader_files.append(
                    os.path.join("shaders", file)
                )

        self.shader_files = sorted(self.shader_files)

        self.shader_id = 0

        with open(self.shader_files[self.shader_id], "r") as file:
            self.shadertoy_code = file.read()


        self.brightness = alpha
        self.colors = color_palette

        self.canvas_size = 50

        self.iResolution = (
            self.canvas_size,
            self.canvas_size
        )

        self.start_time = time.time()

        multiplier = self.canvas_size / 23.0

        gif_coords = cartesian_coords * multiplier

        whex = np.max(gif_coords[:,1])

        left_margin = (
            self.canvas_size - whex
        ) / 2

        gif_coords[:,1] += left_margin
        gif_coords[:,0] += multiplier / 2

        self.gif_coords = gif_coords.astype(int)


        # CHANGED:
        # Keep track of frame number for Shadertoy iFrame
        self.frame = 0



    def change_shader(self):

        self.shader_id = (
            self.shader_id + 1
        ) % len(self.shader_files)


        print(
            "Loading shader...",
            self.shader_files[self.shader_id]
        )


        with open(self.shader_files[self.shader_id], "r") as file:
            self.shadertoy_code = file.read()


        self.shader_program = self.compile_shaders()



    def set_palette(self, colors, brightness):

        if colors != self.colors:

            self.colors = colors
            self.change_shader()

        self.brightness = brightness



    #
    # NEW:
    # Converts Shadertoy GLSL into GLSL ES 1.00
    #
    def prepare_shadertoy_shader(self, code):


        # Remove version declarations copied from Shadertoy
        # because we already supply #version 100
        lines = code.split("\n")

        filtered = []

        for line in lines:

            if "#version" not in line:
                filtered.append(line)


        code = "\n".join(filtered)



        # Shadertoy uses texture()
        # GLES 1.0 uses texture2D()
        code = code.replace(
            "texture(",
            "texture2D("
        )


        # GLES 1.0 has no round()
        # replace common usage:
        #
        # round(x)
        #
        # with:
        #
        # floor(x+0.5)
        #
        code = code.replace(
            "round(",
            "floor("
        )


        # Some Shadertoys use this
        # without initialization
        if "float jTime;" in code:

            code = code.replace(
                "float jTime;",
                "float jTime = 0.0;"
            )



        return code




    def initialize_opengl(self):

        config = Config(
            double_buffer=True,
            depth_size=16
        )

        self.context = Context(config)


        glClearColor(
            0.0,
            0.0,
            0.0,
            1.0
        )


        self.shader_program = self.compile_shaders()


        self.vao = self.create_buffer(
            self.shader_program
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



        #
        # CHANGED:
        # Added Shadertoy compatibility uniforms
        #
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



        try:

            vertex_shader_obj = compileShader(
                vertex_shader,
                GL_VERTEX_SHADER
            )


            fragment_shader_obj = compileShader(
                fragment_shader,
                GL_FRAGMENT_SHADER
            )


            return compileProgram(
                vertex_shader_obj,
                fragment_shader_obj
            )


        except Exception as e:

            print(
                "Shader compilation failed:"
            )

            print(
                fragment_shader
            )

            raise e




    def create_buffer(self, shader_program):


        vertices = np.array(
            [
                -1.0,-1.0,
                 1.0,-1.0,
                 1.0, 1.0,
                -1.0, 1.0
            ],
            dtype=np.float32
        )


        vao = glGenVertexArrays(1)

        glBindVertexArray(vao)


        vertex_buffer = glGenBuffers(1)

        glBindBuffer(
            GL_ARRAY_BUFFER,
            vertex_buffer
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

        iTime = (
            now - self.start_time
        )


        #
        # Shadertoy uniforms
        #

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
            iTime
        )


        glUniform1f(
            glGetUniformLocation(
                self.shader_program,
                "iTimeDelta"
            ),
            1.0 / 60.0
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


        pixels = gaussian_filter(
            pixels,
            sigma=(
                self.blur_sigma,
                self.blur_sigma,
                0
            )
        )


        return pixels




    def update(self,state):

        frame = self.generate_frame()

        for pix_id in range(
            self.gif_coords.shape[0]
        ):

            state[pix_id,:] = frame[
                self.gif_coords[pix_id,0],
                self.gif_coords[pix_id,1],
                :
            ]


        return state * self.brightness
