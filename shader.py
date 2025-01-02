import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import time
from pyglet.gl import Config, Context
from hex_mask import cartesian_coords
from scipy.ndimage import gaussian_filter
import os

class Shader:
    def __init__(self, color_palette, alpha):        
        self.shader_files = []
        for file in os.listdir("shaders"):
            if file.endswith(".fs"):
                self.shader_files.append(os.path.join("shaders", file))
        
        self.shader_id = 1

        with open(self.shader_files[self.shader_id], 'r') as file:
            self.shadertoy_code = file.read()

        self.brightness = alpha
        self.colors = color_palette
        self.canvas_size = 50
        self.iResolution = (self.canvas_size, self.canvas_size)
        self.start_time = time.time()
        multiplier = (self.canvas_size) / 23.0

        gif_coords = cartesian_coords * multiplier
        whex = np.max(gif_coords[:, 1])
        left_margin = (self.canvas_size - whex) / 2
        gif_coords[:, 1] += left_margin
        gif_coords[:, 0] += (multiplier / 2)
        self.gif_coords = gif_coords.astype(int)

        # Initialize Pyglet OpenGL context
        # config = Config(double_buffer=True, depth_size=16)
        # self.context = Context(config)
        #self.initialize_opengl()

    def change_shader(self):
        self.shader_id = (self.shader_id + 1) % len(self.shader_files)

        with open(self.shader_files[self.shader_id], 'r') as file:
            self.shadertoy_code = file.read()

        self.shader_program = self.compile_shaders()

    def set_palette(self, colors, brightness):
        if colors != self.colors:
            self.colors = colors
            self.change_shader()
        self.brightness = brightness
    
    def initialize_opengl(self):
        config = Config(double_buffer=True, depth_size=16)
        self.context = Context(config)

        # Set up OpenGL environment
        glClearColor(0.0, 0.0, 0.0, 1.0)

        # Compile shaders and create buffer
        self.shader_program = self.compile_shaders()
        self.vao = self.create_buffer(self.shader_program)

        # Set up FBO
        self.fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)

        # Create texture for rendering
        self.texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, self.canvas_size, self.canvas_size, 0, GL_RGB, GL_UNSIGNED_BYTE, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        # Attach texture to FBO
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.texture, 0)

        # Check FBO status
        if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
            raise RuntimeError("Framebuffer not complete")

        glBindFramebuffer(GL_FRAMEBUFFER, 0)

        self.iResolution = (self.canvas_size, self.canvas_size)

    def compile_shaders(self):
        vertex_shader = """
        #version 100
        attribute vec2 position;
        void main() {
            gl_Position = vec4(position, 0.0, 1.0);
        }
        """

        fragment_shader = """
        #version 100
        precision mediump float;

        uniform vec2 iResolution;
        uniform float iTime;
        const vec4 iMouse = vec4(0.0,0.0,0.0,0.0);""" + \
        self.shadertoy_code + \
        """
        void main() {
            vec4 fragColor = vec4(0.0);
            mainImage(fragColor, gl_FragCoord.xy);
            gl_FragColor = fragColor;
        }
        """
        
        vertex_shader_obj = compileShader(vertex_shader, GL_VERTEX_SHADER)
        fragment_shader_obj = compileShader(fragment_shader, GL_FRAGMENT_SHADER)
        print(glGetShaderInfoLog(vertex_shader_obj))  # Debug output for vertex shader
        print(glGetShaderInfoLog(fragment_shader_obj)) 
        return compileProgram(vertex_shader_obj, fragment_shader_obj)

    def create_buffer(self, shader_program):
        vertices = np.array([-1.0, -1.0, 1.0, -1.0, 1.0, 1.0, -1.0, 1.0], dtype=np.float32)
        vao = glGenVertexArrays(1)
        glBindVertexArray(vao)
        vertex_buffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vertex_buffer)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        position = glGetAttribLocation(shader_program, "position")
        glVertexAttribPointer(position, 2, GL_FLOAT, False, 2 * 4, ctypes.c_void_p(0))
        glEnableVertexAttribArray(position)
        return vao

    def check_gl_error(self):
        err = glGetError()
        if err != GL_NO_ERROR:
            print(f"OpenGL Error: {err}")

    def generate_frame(self):
        # Bind the FBO for offscreen rendering
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)

        # Ensure the viewport matches the framebuffer size
        glViewport(0, 0, self.canvas_size, self.canvas_size)

        # Clear and render
        glClear(GL_COLOR_BUFFER_BIT)
        glUseProgram(self.shader_program)

        # Set uniforms
        iTime = time.time() - self.start_time
        glUniform2f(glGetUniformLocation(self.shader_program, "iResolution"), *self.iResolution)
        glUniform1f(glGetUniformLocation(self.shader_program, "iTime"), iTime)

        # Render the fullscreen quad
        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLE_FAN, 0, 4)

        # Read pixels from the FBO
        pixels = glReadPixels(0, 0, self.canvas_size, self.canvas_size, GL_RGB, GL_UNSIGNED_BYTE)
        pixels = np.frombuffer(pixels, dtype=np.uint8).reshape(self.canvas_size, self.canvas_size, 3)
        pixels = np.flipud(pixels)

        # Unbind FBO to return to default framebuffer
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

        return pixels

    def update(self, state):
        frame = self.generate_frame()
        frame = gaussian_filter(frame, sigma=(.5, .5, 0))
        for pix_id in range(self.gif_coords.shape[0]):
            state[pix_id, :] = frame[self.gif_coords[pix_id, 0], self.gif_coords[pix_id, 1], :]
        return state * self.brightness


# if __name__ == "__main__":
#     frame_count = 0
#     sh = Shader()
#     frame = np.zeros((397, 3), dtype=int)
#     frame = sh.update(frame)
#     frame_count += 1
#     # print(f"frame: {frame_count}", end="\r")
#     print(frame)


if __name__ == "__main__":
    frame_count = 0
    sh = Shader(None, .5)
    sh.initialize_opengl()
    frame = np.zeros((397, 3), dtype=int)

    import cv2
    while True:
        frame = sh.generate_frame()
        frame = gaussian_filter(frame, sigma=(.5,.5,0))

        # Display the frame using OpenCV
        cv2.imshow('Shader Output', cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()