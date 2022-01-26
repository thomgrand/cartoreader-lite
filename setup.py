from setuptools import setup
from distutils.core import setup
import os


with open(os.path.join(os.path.dirname(__file__), 'README.md'), 'r') as readme:
     long_description = readme.read()

setup(name="cartoreader-lite",
    version="1.0.0",    
    description="Cartoreader-lite provides a simplified and easy low-level access to CARTO3 studies.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/thomgrand/cartoreader-lite",
    packages=["cartoreader_lite", "cartoreader_lite.high_level", "cartoreader_lite.low_level"],
    install_requires=["numpy", "pyvista>=0.33", "vtk", "pandas", "scipy", 
                         "trimesh", "rtree"], #Geometric postprocessing
    classifiers=[
        "Programming Language :: Python :: 3"
    ],
    python_requires='>=3.8',
     author="Thomas Grandits",
     author_email="tomdev@gmx.net",
     license="AGPL", 
     extras_require = {
          "tests": ["pytest", "pytest-cov"],
          "docs": ["sphinx", "pydata_sphinx_theme"]
     }
)

