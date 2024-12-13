from setuptools import setup
from Cython.Build import cythonize
import numpy

setup(
    ext_modules=cythonize("led_strip_cy.pyx"),
    include_dirs=[numpy.get_include()]
)