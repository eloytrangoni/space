from skbuild import setup

setup(
    name="elo_space",
    version="0.1.0",
    description="Simulador modular de predicción acústica y rigging Line Array - Elo Acoustics",
    author="eloytrangoni",
    packages=["elo_space"],  # Si tienes código Python en ./elo_space/
    package_dir={"": "."},
    cmake_minimum_required_version="3.15",
    cmake_args=[
        "-DCMAKE_BUILD_TYPE=Release",  # o Debug
    ],
    install_requires=[
        "pybind11",
        "numpy",
        "scikit-build",
        "cmake",
        "PyQt5"
    ],
)
