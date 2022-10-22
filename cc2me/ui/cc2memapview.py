from random import randrange

from PIL.ImageTk import PhotoImage, Image
from tkintermapview import TkinterMapView
from tkintermapview.canvas_position_marker import CanvasPositionMarker

from ..savedata.logging import logger

TILE_SIZE = 256

TEAM_COLORS = {
    0: "#990000",
    1: "#0066FF",
    2: "#FFCC00",
    3: "#66FF33",
    4: "#FF00FF",
}


def get_team_color(team: int) -> str:
    if team not in TEAM_COLORS:
        r, g, b = randrange(0, 255), randrange(0, 255), randrange(0, 255)
        TEAM_COLORS[team] = "#{:02X}{:02X}{:02X}".format(r, g, b)
    return TEAM_COLORS[team]


def generate_sea_tile() -> PhotoImage:
    img = Image.new("RGB", (TILE_SIZE, TILE_SIZE), (0, 0, 50))
    return PhotoImage(img)


class CC2MeMapView(TkinterMapView):

    sea_tile_image: PhotoImage = None

    def __init__(self, width: int = 300,
                 height: int = 200,
                 corner_radius: int = 0):
        super(CC2MeMapView, self).__init__(width=width,
                                           height=height,
                                           corner_radius=corner_radius,
                                           max_zoom=10,
                                           )

    def set_zoom(self, zoom: int, relative_pointer_x: float = 0.5, relative_pointer_y: float = 0.5):
        logger.info(f"zoom {zoom}")
        super().set_zoom(zoom, relative_pointer_x, relative_pointer_y)

    def request_image(self, zoom: int, x: int, y: int, db_cursor=None) -> PhotoImage:
        return self.empty_tile_image
        #if self.sea_tile_image is None:
        #    self.sea_tile_image = generate_sea_tile()
        #return self.sea_tile_image

    def add_marker(self, marker: CanvasPositionMarker):
        marker.draw()
        self.canvas_marker_list.append(marker)
        return marker


