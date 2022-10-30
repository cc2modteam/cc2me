from setuptools import setup, find_packages
VERSION = "0.0.1"

requirements = [
    "tkintermapview==1.15",
    "pillow==9.2.0",
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
            "cc2me = cc2me.ui.tool:run"
        ],
        "console_scripts": [
            "cc2mec = cc2me.ui.tool:run"
        ]
    },
)
