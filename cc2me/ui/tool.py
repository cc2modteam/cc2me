"""GUI for cc2me mission editor"""
import argparse
import sys
import tkinter
import tkinter.messagebox
from tkinter import filedialog
from typing import Optional, List

from cc2me.savedata.types.objects import Island
from .cc2memapview import CC2MeMapView, IslandMarker
from ..savedata.loader import CC2XMLSave, load_save_file

APP_NAME = "cc2me.ui.tool"

parser = argparse.ArgumentParser(description=__doc__, prog=APP_NAME)


class App(tkinter.Tk):

    WIDTH = 800
    HEIGHT = 750

    def __init__(self, *args, **kwargs):
        tkinter.Tk.__init__(self, *args, **kwargs)
        self.cc2me: Optional[CC2XMLSave] = None
        self.islands: List[IslandMarker] = []

        self.title(APP_NAME)
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        if sys.platform == "darwin":
            self.bind("<Command-q>", self.on_closing)
            self.bind("<Command-w>", self.on_closing)

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=2)
        self.grid_columnconfigure(3, weight=0)
        self.grid_rowconfigure(1, weight=1)

        self.open_button = tkinter.Button(master=self, width=6, text="Open", command=self.open_file)
        self.open_button.grid(row=0, column=0, pady=10, padx=5)

        self.save_button = tkinter.Button(master=self, width=6, text="Save", command=None)
        self.save_button.grid(row=0, column=1, pady=10, padx=5)

        self.map_widget = CC2MeMapView(width=self.WIDTH,
                                       height=600,
                                       corner_radius=0)
        self.map_widget.grid(row=1, column=0, columnspan=4, sticky="nsew")
        self.map_widget.set_position(0, 0)
        self.map_widget.set_zoom(1)

    def clear(self):
        pass

    def on_closing(self, event=0):
        self.destroy()
        exit()

    def start(self):
        self.mainloop()

    def open_file(self):

        # remove existing items
        for island in self.islands:
            island.delete()
        self.map_widget.canvas_marker_list = []

        filename = filedialog.askopenfilename(title="Open CC2 Save",
                                              filetypes=(("XML Files", "*.xml"),))
        self.cc2me = load_save_file(filename)
        self.islands.clear()

        # islands
        for island_tile in self.cc2me.tiles:
            island = Island(island_tile)
            marker = IslandMarker(self.map_widget, island)
            marker.text = f"Island {island_tile.id}"
            self.map_widget.add_marker(marker)
            self.islands.append(marker)


def run(args=None):
    parser.parse_args(args)
    app = App()
    app.start()


if __name__ == "__main__":
    run()
