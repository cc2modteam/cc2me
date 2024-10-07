from setuptools import setup, find_packages
VERSION = "0.2.1"

requirements = [
    "pygame==2.6.0",
    "pygame-gui==0.6.12",
]

setup(
    name="cc2me",
    version=VERSION,
    description="Carrier Command 2 Mission Editor",
    author="Ian Norton",
    author_email="inorton@gmail.com",
    url="https://gitlab.com/inorton/cc2me",
    platforms=["any"],
    license="License :: OSI Approved :: MIT License",
    long_description="Edit Carrier Command 2 save files",
    install_requires=requirements,
    packages=find_packages(where="."),
    package_dir={"": "."},
    package_data={"cc2me": ["ui/icons/*.png"]},
    entry_points={
        "gui_scripts": [
            "cc2mex = cc2me.pg.app:run",
            "cc2me = cc2me.ui.tool:run"
        ],
    },
)
