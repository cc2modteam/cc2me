"""GUI for cc2me mission editor"""
import argparse
import os
import sys
import customtkinter
import tkinter
import tkinter.messagebox
from tkinter import filedialog
from typing import Optional, List

from cc2me.ui.InventoryEditor import InventoryEditor
from .properties import Properties
from ..savedata.constants import VehicleType, VehicleAttachmentDefinitionIndex, get_persistent_file_path, get_cc2_appdata
from ..savedata.types.objects import MapTile, MapVehicle, get_unit, Spawn, Vehicle
from ..savedata.loader import load_save_file
from ..savedata.types.save import CC2XMLSave, Tile, Waypoint, EmbeddedAttachmentStateData, EmbeddedVehicleStateData
from .cc2memapview import CC2MeMapView
from .toolbar import Toolbar
from .saveslotchooser import SlotChooser
from .mapmarkers import TileMarker, VehicleMarker, MapItemMarker, WaypointMarker

APP_NAME = "cc2me.ui.tool"

parser = argparse.ArgumentParser(description=__doc__, prog=APP_NAME)


class App(customtkinter.CTk):
    WIDTH = 900
    HEIGHT = 750
    cc2dir = get_cc2_appdata()
    persistent = get_persistent_file_path()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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

        self.islands: List[TileMarker] = []
        self.units: List[VehicleMarker] = []
        self.waypoints: List[WaypointMarker] = []
        self.spawns: List[VehicleMarker] = []
        self.paths: List = []

        self.title(APP_NAME)
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        if sys.platform == "darwin":
            self.bind("<Command-q>", self.on_closing)
            self.bind("<Command-w>", self.on_closing)

        self.toolbar = Toolbar(self, relief=tkinter.RAISED)
        self.toolbar.add_button("open", "open", command=self.open_file)
        self.toolbar.add_button("openslot", "open-slot", command=self.open_slot)
        self.toolbar.add_button("save", "save", command=self.save_file, state=tkinter.DISABLED, group="save")
        self.toolbar.add_button("saveas", "saveas", command=self.save_as, state=tkinter.DISABLED, group="save")
        self.toolbar.add_button("saveslot", "save-slot", command=self.save_slot, state=tkinter.DISABLED, group="save")
        self.toolbar.add_button("delete", "delete", command=self.remove_item, state=tkinter.DISABLED, group="selected")
        self.toolbar.add_button("clone", "dupe", command=self.duplicate_selected, state=tkinter.DISABLED, group="selected")
        self.toolbar.add_button("addisland", "add-island", command=self.add_new_island, state=tkinter.DISABLED,
                                group="none-selected")

        self.toolbar.add_button("addseal", "seal", command=self.add_new_seal, state=tkinter.DISABLED,
                                group="none-selected")
        self.toolbar.add_button("addwalrus", "walrus", command=self.add_new_walrus, state=tkinter.DISABLED,
                                group="none-selected")
        self.toolbar.add_button("addbear", "bear", command=self.add_new_bear, state=tkinter.DISABLED,
                                group="none-selected")
        self.toolbar.add_button("addmule", "mule", command=self.add_new_mule, state=tkinter.DISABLED,
                                group="none-selected")
        self.toolbar.add_button("adddroid", "droid", command=self.add_new_droid, state=tkinter.DISABLED,
                                group="none-selected")
        self.toolbar.add_button("inventory", "inventory", command=self.edit_inventory)
        #self.toolbar.add_button("addlifeboat", "lifeboat", command=self.add_new_lifeboat, state=tkinter.DISABLED,
        #                        group="none-selected")
        self.toolbar.add_button("addneedlefish", "needlefish", command=self.add_new_needlefish, state=tkinter.DISABLED,
                                group="none-selected")
        self.toolbar.add_button("addswordfish", "swordfish", command=self.add_new_swordfish, state=tkinter.DISABLED,
                                group="none-selected")
        self.toolbar.add_button("addbarge", "barge", command=self.add_new_barge, state=tkinter.DISABLED,
                                group="none-selected")
        self.toolbar.add_button("addturret", "turret", command=self.add_new_turret, state=tkinter.DISABLED,
                                group="none-selected")

        self.toolbar.add_button("set1shield", icon="1s-island", command=self.set_1s_islands, group="save")

        self.toolbar.add_button("reset_vstates", icon="lifeboat", command=self.reset_vstates, group="save")

        self.middle = tkinter.Frame(self)
        self.map_widget = CC2MeMapView(corner_radius=0)
        self.map_widget.master = self.middle
        self.properties = Properties(self.middle)

        self.status_line = tkinter.Variable(value="Ready..")
        self.status_bar = tkinter.Label(self,
                                        textvariable=self.status_line,
                                        justify=tkinter.LEFT,
                                        width=self.WIDTH,
                                        relief=tkinter.SUNKEN,
                                        anchor=tkinter.W)

        # packing

        self.toolbar.frame.pack(fill=tkinter.X, expand=False, side=tkinter.TOP)
        self.status_bar.pack(fill=tkinter.X, expand=False, side=tkinter.BOTTOM)

        self.map_widget.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)
        self.properties.frame.pack(side=tkinter.TOP, expand=True, fill=tkinter.Y)
        self.properties.frame.pack_propagate(False)
        self.properties.map_widget = self.map_widget
        self.middle.pack(fill=tkinter.BOTH, expand=True)

        self.map_widget.set_position(0, 0)
        self.map_widget.set_zoom(1)
        self.map_widget.add_right_click_menu_command(label="Select Units",
                                                     command=self.start_selection_units,
                                                     pass_coords=False)
        self.map_widget.add_right_click_menu_command(label="Select None",
                                                     command=self.select_none,
                                                     pass_coords=False)
        self.map_widget.on_select_box = self.on_selection
        self.map_widget.on_mouse_drag = self.on_mouse_drag
        self.map_widget.on_mouse_release = self.on_mouse_release

        self.current_marker: Optional[MapItemMarker] = None
        self.dragging_marker = None

    def reset_vstates(self):
        """Fix messed up unit state and attachments"""

        # we only allow 1 gun turret per ground unit, and wipe extraneous state data

        for marker in self.units:
            unit = marker.mapitem
            if isinstance(unit.object, Vehicle):
                v: Vehicle = unit.object
                v.repair()

    def start_selection_units(self):
        self.map_widget.selection_mode = "units"

    def all_markers(self) -> List[MapItemMarker]:
        found: List[MapItemMarker] = []
        for item in self.islands:
            found.append(item)
        for item in self.units + self.spawns:
            found.append(item)
            for wpt in item.waypoints:
                found.append(wpt)

        return found

    def edit_inventory(self):
        selected = self.selected_markers()
        if len(selected) == 1:
            item = selected[0].mapitem
            if item.has_inventory():
                editor = InventoryEditor(self, item)
                for inventory_index, stringvar in editor.string_vars.items():
                    item.set_inventory_item(inventory_index, int(stringvar.get()))

    def set_1s_islands(self):
        for item in self.islands:
            tile = item.island
            tile.difficulty = 0.02

    def all_map_waypoints(self) -> List[Waypoint]:
        found = []
        for item in self.units + self.spawns:
            wpts = item.unit.vehicle().waypoints
            found.extend(wpts)

        return found

    def selected_markers(self) -> List[MapItemMarker]:
        return [x for x in self.all_markers() if x.selected]

    def select_none(self):
        self.map_widget.set_mouse_arrow()
        for item in self.units + self.spawns:
            item.unselect()
        for item in self.islands:
            item.unselect()

        self.map_widget.selected_markers.clear()
        self.properties.clear()

        self.toolbar.disable("delete")
        self.toolbar.disable_group("selected")
        self.toolbar.enable_group("none-selected")

    def on_selection(self, mode, nw, se):
        # format is NW[y], NW[x], SW[y], SW[x]
        print(f"{mode} {nw[0]} {nw[1]} -> {se[0]} {se[1]}")
        # find everything in the box
        selected = []
        self.select_none()
        if mode == "units":
            for u in self.units + self.spawns:
                if se[0] < u.position[0] < nw[0]:
                    if se[1] > u.position[1] > nw[1]:
                        selected.append(u)
        self.select_markers(selected)

    def select_markers(self, markers):
        self.select_none()
        self.toolbar.disable_group("none-selected")
        self.toolbar.enable_group("selected")
        for item in markers:
            item.select()
            self.map_widget.selected_markers.append(item)
        if len(markers) == 1:
            # populate properties panel
            self.properties.clear()
            obj = markers[0].mapitem
            self.properties.objects = [obj]
        else:
            self.properties.clear()
            self.properties.objects = [x.mapitem for x in markers]

        print(f"selected {len(markers)}")

    def on_closing(self, event=0):
        self.destroy()
        exit()

    def add_new_island(self):
        # add in the middle of the canvas
        loc = self.map_widget.convert_canvas_coords_to_decimal_coords(200, 100)
        new_tile = self.cc2me.new_tile()
        marker = self.add_island(new_tile)
        marker.move(loc[0], loc[1])
        marker.draw()
        self.select_markers([marker])

    def add_new_unit(self, vtype: VehicleType) -> VehicleMarker:
        loc = self.map_widget.convert_canvas_coords_to_decimal_coords(200, 200)
        v = self.cc2me.new_vehicle(vtype)
        marker = self.add_unit(v)
        marker.unit.move(loc[0], loc[1])
        self.select_markers([marker])
        z = self.map_widget.zoom
        self.map_widget.set_zoom(z + 10.1)
        self.map_widget.set_zoom(z)
        return marker

    def duplicate_units(self, units: List[MapVehicle]) -> List[VehicleMarker]:
        # loop through each unit
        new_units = []
        for unit in units:
            new_unit = self.add_new_unit(unit.vehicle_type)
            new_unit.unit.team_owner = unit.team_owner
            new_unit.unit.alt = unit.alt
            new_unit.unit.move(unit.loc[0] + 0.1, unit.loc[1] + 0.1)

            for attachment in unit.attachments:
                definition = unit.get_attachment(attachment)
                if definition is not None:
                    new_unit.unit.set_attachment(attachment, definition)

            new_units.append(new_unit)

        return new_units

    def duplicate_selected(self):
        markers = self.selected_markers()

        units = [x.unit for x in markers if isinstance(x, VehicleMarker)]
        if units:
            new_units = self.duplicate_units(units)
            if new_units:
                self.select_markers(new_units)

    def add_new_seal(self):
        self.add_new_unit(VehicleType.Seal)

    def add_new_walrus(self):
        self.add_new_unit(VehicleType.Walrus)

    def add_new_bear(self):
        self.add_new_unit(VehicleType.Bear)

    def add_new_mule(self):
        self.add_new_unit(VehicleType.Mule)

    def add_new_lifeboat(self):
        self.add_new_unit(VehicleType.Lifeboat)

    def add_new_droid(self):
        marker = self.add_new_unit(VehicleType.Droid)

        droid = marker.unit

        droid.set_attachment(0, VehicleAttachmentDefinitionIndex.DriverSeat)
        droid.set_attachment(1, VehicleAttachmentDefinitionIndex.Autocannon)
        self.select_none()
        self.select_markers([marker])

    def add_new_barge(self):
        self.add_new_unit(VehicleType.Barge)

    def add_new_turret(self):
        self.add_new_unit(VehicleType.Turret)

    def add_new_swordfish(self):
        self.add_new_unit(VehicleType.Swordfish)

    def add_new_needlefish(self):
        self.add_new_unit(VehicleType.Needlefish)

    def remove_item(self):
        selected = self.selected_markers()
        for marker in selected:
            if isinstance(marker, TileMarker):
                tile = marker.island.tile()
                self.cc2me.remove_tile(tile)
            if isinstance(marker, VehicleMarker):
                vehicle = marker.unit.vehicle()
                if vehicle is not None:
                    self.cc2me.remove_vehicle(vehicle)
                if isinstance(marker.unit, Spawn):
                    self.cc2me.remove_spawn(marker.mapitem.object.data.respawn_id)

            marker.delete()
        self.select_none()

    def start(self):
        self.mainloop()

    def save_file(self):
        if self.save_filename:
            self.save(self.save_filename)

    def save(self, filename):
        print(f"Saving {filename}")
        with open(filename, "w") as fd:
            fd.write(self.cc2me.export())

    def save_as(self):
        filename = filedialog.asksaveasfilename(title="Save CC2 map as..")
        if filename:
            self.save(filename)

    def clear(self):
        self.map_widget.selected_markers.clear()

        for item in self.all_markers():
            item.delete()

        for markers in [self.paths]:
            for item in markers:
                item.delete()
            markers.clear()

        self.cc2me = None
        self.map_widget.set_zoom(1, 0.0, 0.0)

        for grp in [self.map_widget.canvas_marker_list, self.map_widget.canvas_path_list]:
            for item in grp:
                self.map_widget.delete(item)

        # not totally sure why I have to do this again..
        while len(self.map_widget.canvas_path_list):
            first = self.map_widget.canvas_path_list[0]
            first.delete()

        self.map_widget.update()
        self.dragging_marker = None

    def marker_clicked(self, marker: MapItemMarker) -> bool:
        if marker.selected:
            return True
        return False  # let click bubble up

    def island_clicked(self, shape):
        if not self.marker_clicked(shape):
            self.select_markers([shape])
            self.map_widget.set_mouse_move()

    def unit_clicked(self, unitmarker):
        if not self.marker_clicked(unitmarker):
            self.select_markers([unitmarker])
            self.map_widget.set_mouse_move()

    def waypoint_clicked(self, marker):
        if not self.marker_clicked(marker):
            self.select_markers([marker])
            self.map_widget.set_mouse_move()

    def open_slot(self):
        choice = {}
        SlotChooser(self, persistent_file=self.persistent, choice=choice)
        if choice:
            filename = os.path.join(self.cc2dir, "saved_games", choice[1]["filename"], "save.xml")
            self.read_file(filename)

    def save_slot(self):
        choice = {}
        SlotChooser(self, persistent_file=self.persistent, choice=choice, title="Overwrite CC2 Save Slot")
        if choice:
            filename = os.path.join(self.cc2dir, "saved_games", choice[1]["filename"], "save.xml")
            self.save_filename = filename
            self.save(filename)

    def open_file(self):
        filename = filedialog.askopenfilename(title="Open CC2 Save",
                                              filetypes=(("XML Files", "*.xml"),))
        self.read_file(filename)

    def read_file(self, filename):
        self.clear()
        if filename and os.path.exists(filename):
            self.cc2me = load_save_file(filename)
            self.save_filename = filename
        self.islands.clear()
        self.map_widget.update()
        added = []

        first_carrier = None

        if self.cc2me:
            # islands
            for island_tile in self.cc2me.tiles:
                self.add_island(island_tile)
            # units
            for veh in self.cc2me.vehicles:
                marker = self.add_unit(veh)
                if not first_carrier:
                    if veh.definition_index == VehicleType.Carrier.int:
                        first_carrier = marker
                added.append(marker)
        self.status_line.set(f"Loaded {filename} ({len(self.islands)} islands, {len(self.units)} units)")
        self.toolbar.enable_group("save")
        self.select_none()

        for marker in added:
            marker.update_waypoints(
                command=self.waypoint_clicked,
                start_hover=self.hover_waypoint,
                end_hover=self.end_hover,
                find_vehicle=self.find_vehicle
            )
        if first_carrier:
            self.map_widget.set_zoom(6)
            self.map_widget.set_position(first_carrier.position[0], first_carrier.position[1])

        self.map_widget.canvas.update_idletasks()

    def add_island(self, island_tile: Tile):
        island = MapTile(island_tile)
        marker = TileMarker(self.map_widget, island, on_click=self.island_clicked)
        marker.on_hover_start = self.hover_island
        marker.on_hover_end = self.end_hover
        marker.text = island.display_ident
        self.map_widget.add_marker(marker)

        # if the island has spawns add those if the unit doesn't exist yet
        for spawn in island.tile().spawn_data.vehicles.items():
            vid = spawn.data.respawn_id
            try:
                self.cc2me.vehicle(vid)
            except KeyError:
                self.add_spawn(Spawn(spawn, island_tile))

        self.islands.append(marker)
        return marker

    def _add_unit_marker(self, unit):
        marker = VehicleMarker(self.map_widget, unit)
        marker.command = self.unit_clicked
        marker.on_hover_end = self.end_hover
        marker.on_hover_start = self.hover_unit
        self.map_widget.add_marker(marker)
        if unit.show_waypoints:
            if unit.vehicle() is not None:
                marker.update_waypoints(
                    command=self.waypoint_clicked,
                    start_hover=self.hover_waypoint,
                    end_hover=self.end_hover,
                    find_vehicle=self.find_vehicle
                )

        return marker

    def find_vehicle(self, vid) -> Optional[VehicleMarker]:
        if vid:
            vint = int(vid)
            for v in self.units:
                if vint == v.unit.v_id:
                    return v
        return None

    def add_spawn(self, spawn) -> VehicleMarker:
        marker = self._add_unit_marker(spawn)
        self.spawns.append(marker)
        return marker

    def add_unit(self, vehicle) -> VehicleMarker:
        u = get_unit(vehicle)
        marker = self._add_unit_marker(u)
        self.units.append(marker)
        return marker

    def hover_marker(self, marker):
        self.current_marker = marker
        if marker.selected:
            self.map_widget.set_mouse_move()
        else:
            self.map_widget.set_mouse_choose()

    def hover_waypoint(self, marker: WaypointMarker):
        self.hover_marker(marker)
        self.status_line.set(f"waypoint {marker.mapitem.display_ident}")

    def hover_unit(self, marker: VehicleMarker):
        self.hover_marker(marker)
        vtype = marker.unit.vehicle_type
        text = f"{vtype.name} "
        if isinstance(marker.unit, Spawn):
            text = f"spawn {text}"
        else:
            text += f"{marker.unit.vehicle().id} "
            for item in marker.unit.vehicle().attachments.items():
                text += f"[{item.attachment_index}]:{VehicleAttachmentDefinitionIndex.get_name(item.definition_index)} "

        self.status_line.set(text)

    def hover_island(self, marker: TileMarker):
        self.hover_marker(marker)
        self.status_line.set(f"Island {marker.text} ({marker.island.tile().id})")

    def end_hover(self, *args):
        self.status_line.set("")
        self.current_marker = None

    def on_mouse_drag(self, event: tkinter.Event) -> bool:
        if self.dragging_marker or self.current_marker:
            if self.current_marker:
                self.dragging_marker = self.current_marker

            if self.dragging_marker.selected:
                # move all the selection
                marker = self.dragging_marker
                lat, lon = self.map_widget.convert_canvas_coords_to_decimal_coords(event.x, event.y)
                olat, olon = marker.position
                dlat = lat - olat
                dlon = lon - olon

                selected = self.selected_markers()
                for marker in selected:
                    m_lat, m_lon = marker.position
                    marker.move(m_lat + dlat,
                                m_lon + dlon)

            for marker in self.selected_markers():
                marker.draw()
                if isinstance(marker, VehicleMarker):
                    rm_path = marker.waypoint_path
                    if rm_path:
                        self.map_widget.delete(rm_path)
            self.map_widget.update_idletasks()
            return True  # swallow

        return False  # bubble up

    def on_mouse_release(self):
        if self.dragging_marker:
            if isinstance(self.dragging_marker, VehicleMarker):
                self.update_vehicle_marker(self.dragging_marker)
            elif isinstance(self.dragging_marker, WaypointMarker):
                self.update_vehicle_marker(self.dragging_marker.vehicle_marker)
        self.dragging_marker = None

    def update_vehicle_marker(self, marker):
        marker.update_waypoints(
            command=self.waypoint_clicked,
            start_hover=self.hover_waypoint,
            end_hover=self.end_hover)


def run(args=None):
    parser.parse_args(args)
    app = App()
    app.start()


if __name__ == "__main__":
    run()
