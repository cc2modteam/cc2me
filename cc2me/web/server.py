"""Flask webserver for CC2E"""
from pathlib import Path

from flask import Flask, render_template, request
from functools import lru_cache
from ..savedata.constants import read_save_slots, get_cc2_appdata, get_island_name
from ..savedata.loader import CC2XMLSave, load_save_file
from ..ui.cc2constants import get_team_color
from .utils import loc_to_geo_box, loc_to_geo, cc2_to_minutes, latlong_to_cc2loc

WEB_DIR = Path(__file__).parent.absolute()
STATIC_DIR = WEB_DIR / "static"
TEMPLATE_DIR = WEB_DIR / "templates"


app = Flask("CC2E")
app.template_folder = TEMPLATE_DIR
app.static_folder = STATIC_DIR


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/slots")
def slots_route():
    slots = read_save_slots()
    return render_template("slots.html", slots=slots)


@lru_cache(4)
def get_map_slot(slot) -> CC2XMLSave:
    path = Path(get_cc2_appdata()) / "saved_games" / slot / "save.xml"
    save = load_save_file(path)
    return save


@app.route("/geo/<slot>/<layer>")
def geojson_route(slot, layer):
    save = get_map_slot(slot)
    geo = {
        "type": "FeatureCollection",
        "features": [],
    }
    if layer == "tiles":

        for tile in save.tiles:
            item = {
                "type": "Feature",
                "id": tile.id,
                "properties": {
                    "kind": "tile",
                    "name": get_island_name(tile.id),
                    "team": tile.team_control,
                    "team_color": get_team_color(tile.team_control),
                    "difficulty": tile.difficulty_factor,
                    "facility.category": tile.facility.category,
                    "radius": cc2_to_minutes(tile.island_radius),
                    "loc": loc_to_geo(tile.loc),
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": loc_to_geo_box(tile.loc, tile.island_radius, tile.island_radius)
                }
            }
            geo["features"].append(item)

    return geo


@app.route("/map/<slot>")
def map_route(slot):
    save = get_map_slot(slot)
    return render_template("map.html", save=save, slot=slot)


@app.route("/move/<slot>/<kind>/<int:item>", methods=["POST"])
def move_item(slot: str, kind: str, item: int):
    data = request.json
    moved = latlong_to_cc2loc(data["lat"], data["lon"])
    save = get_map_slot(slot)
    if kind == "tile":
        island = save.tile(item)
        previous = island.loc
        island.move(moved.x, island.loc.y, moved.z)
        # move all island-related things (spawns etc) by the same amount
        dx = previous.x - moved.x
        dz = previous.z - moved.z

    return {
        "dx": dx,
        "dz": dz
    }
