"""GUI for cc2me mission editor"""
import argparse
import os
import sys
import tkinter
import tkinter.messagebox
from tkinter import filedialog
from typing import Optional, List, Tuple

from cc2me.savedata.constants import get_island_name, get_vehicle_name
from cc2me.savedata.types.objects import Island, Unit
from cc2me.savedata.types.tiles import Tile
from cc2me.savedata.types.vehicles.vehicle import Vehicle
from .cc2memapview import CC2MeMapView
from cc2me.ui.mapmarkers import IslandMarker, UnitMarker
from ..savedata.loader import CC2XMLSave, load_save_file

APP_NAME = "cc2me.ui.tool"

parser = argparse.ArgumentParser(description=__doc__, prog=APP_NAME)


class App(tkinter.Tk):

    WIDTH = 900
    HEIGHT = 750

    def __init__(self, *args, **kwargs):
        tkinter.Tk.__init__(self, *args, **kwargs)
        self.menubar = tkinter.Menu()
        self.filemenu = tkinter.Menu()

        self.menubar.add_cascade(label="File", menu=self.filemenu)
        self.filemenu.add_command(label="Open", command=self.open_file)
        self.filemenu.add_command(label="Save", command=self.save_file)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=self.on_closing)

        self.editmenu = tkinter.Menu()
        self.menubar.add_cascade(label="Edit", menu=self.editmenu)
        self.editmenu.add_command(label="Select None", command=self.select_none)

        self.configure(menu=self.menubar)

        self.save_filename: Optional[str] = None
        self.cc2me: Optional[CC2XMLSave] = None

        self.islands: List[IslandMarker] = []
        self.units: List[UnitMarker] = []

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
        self.status_line = tkinter.Variable(value="Ready..")
        self.status_bar = tkinter.Label(textvariable=self.status_line, justify=tkinter.LEFT, width=self.WIDTH)
        self.status_bar.grid(row=2, column=0, columnspan=4, padx=1, pady=1, sticky=tkinter.NSEW)
        self.grid_rowconfigure(1, weight=1)

        self.open_button = tkinter.Button(master=self, width=6, text="Open", command=self.open_file)
        self.open_button.grid(row=0, column=0, pady=10, padx=5)

        self.save_button = tkinter.Button(master=self, width=6, text="Save", command=self.save_file)
        self.save_button.grid(row=0, column=1, pady=10, padx=5)

        self.map_widget = CC2MeMapView(width=self.WIDTH,
                                       height=600,
                                       corner_radius=0)
        self.map_widget.grid(row=1, column=0, columnspan=4, sticky="nsew")
        self.map_widget.set_position(0, 0)
        self.map_widget.set_zoom(1)
        self.map_widget.add_right_click_menu_command(label="Select Units",
                                                     command=self.start_selection_units,
                                                     pass_coords=False)
        self.map_widget.on_select_box = self.on_selection

    def start_selection_units(self):
        self.map_widget.selection_mode = "units"

    def select_none(self):
        for item in self.units:
            item.unselect()
        for item in self.islands:
            item.unselect()

    def on_selection(self, mode, nw, se):
        # format is NW[y], NW[x], SW[y], SW[x]
        print(f"{mode} {nw[0]} {nw[1]} -> {se[0]} {se[1]}")
        # find everything in the box
        selected = []
        self.select_none()
        if mode == "units":
            for u in self.units:
                if se[0] < u.position[0] < nw[0]:
                    if se[1] > u.position[1] > nw[1]:
                        selected.append(u)

        self.select_markers(selected)
        print(f"selected {len(selected)} {mode}")

    def select_markers(self, markers):
        self.select_none()
        for item in markers:
            item.select()

    def on_closing(self, event=0):
        self.destroy()
        exit()

    def start(self):
        self.mainloop()

    def save_file(self):
        if self.save_filename:
            with open(self.save_filename, "w") as fd:
                fd.write(self.cc2me.export())

    def clear(self):
        # remove existing items
        for x in self.islands + self.units:
            x.delete()
        self.map_widget.canvas_marker_list = []
        self.islands.clear()
        self.units.clear()
        self.map_widget.canvas.delete("all")
        self.cc2me = None
        self.map_widget.set_zoom(1, 0.0, 0.0)
        self.map_widget.update()

    def island_clicked(self, shape):
        print(f"island clicked {shape}")

    def unit_clicked(self, unitmarker):
        self.select_markers([unitmarker])

    def open_file(self):
        self.clear()

        filename = filedialog.askopenfilename(title="Open CC2 Save",
                                              filetypes=(("XML Files", "*.xml"),))
        if filename and os.path.exists(filename):
            self.cc2me = load_save_file(filename)
        self.islands.clear()
        self.map_widget.update()

        if self.cc2me:
            # islands
            for island_tile in self.cc2me.tiles:
                self.add_island(island_tile)
            # units
            for veh in self.cc2me.vehicles:
                self.add_unit(veh)

        self.map_widget.canvas.update_idletasks()

    def add_island(self, island_tile: Tile):
        island = Island(island_tile)
        marker = IslandMarker(self.map_widget, island, on_click=self.island_clicked)
        marker.text = get_island_name(island_tile.id)
        self.map_widget.add_marker(marker)
        self.islands.append(marker)

    def add_unit(self, vehicle):
        u = Unit(vehicle)
        marker = UnitMarker(self.map_widget, u)
        marker.command = self.unit_clicked
        marker.on_hover_end = self.end_hover
        marker.on_hover_start = self.hover_unit
        self.map_widget.add_marker(marker)
        self.units.append(marker)

    def hover_unit(self, marker: UnitMarker):
        definition = marker.unit.vehicle().definition_index
        text = f"Unit: {get_vehicle_name(definition)} {marker.unit.vehicle().id}"
        self.status_line.set(text)

    def end_hover(self, *args):
        self.status_line.set("")


def run(args=None):
    parser.parse_args(args)
    app = App()
    app.start()


if __name__ == "__main__":
    run()
