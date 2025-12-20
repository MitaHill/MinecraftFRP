from setuptools import setup, Extension
from Cython.Build import cythonize
import os

# 目标文件
source_file = "src/config/SecretConfig.py"

if os.path.exists(source_file):
    extensions = [
        Extension("src.config.SecretConfig", [source_file])
    ]
    setup(
        ext_modules=cythonize(extensions, compiler_directives={'language_level': "3"}),
        script_args=["build_ext", "--inplace"]
    )
    print(f"Successfully compiled {source_file}")
else:
    print(f"Error: {source_file} not found")
