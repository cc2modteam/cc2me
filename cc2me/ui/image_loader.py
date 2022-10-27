import os
from typing import Optional, Dict

from PIL import Image, ImageTk
from pathlib import Path

HERE = Path(__file__).absolute().parent

IMAGES: Dict[str, ImageTk.PhotoImage] = {}


def load_icon(name: str) -> Optional[ImageTk.PhotoImage]:
    filename = HERE / "icons" / f"{name}.png"
    tkimg = IMAGES.get(name, None)
    if not tkimg:
        if filename.exists():
            tkimg = ImageTk.PhotoImage(file=str(filename))
            IMAGES[name] = tkimg
    return tkimg
