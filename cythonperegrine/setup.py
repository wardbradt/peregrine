from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize


extensions = [
    Extension("*", ["*.pyx"])
]

setup(
    ext_modules=cythonize(extensions)
)
