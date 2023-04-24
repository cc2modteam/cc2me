"""Flask webserver for CC2E"""
from pathlib import Path

from flask import Flask, render_template, request
from functools import lru_cache
from ..savedata.constants import read_save_slots, get_cc2_appdata, get_island_name
from ..savedata.loader import CC2XMLSave, load_save_file
from ..ui.cc2constants import get_team_color
from .utils import loc_to_geo_box, loc_to_geo, cc2_to_minutes, latlong_to_cc2loc, make_geodata

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


@app.route("/geo/<slot>/<layer>", defaults={"specific_id": -1})
@app.route("/geo/<slot>/<layer>/<int:specific_id>")
def geojson_route(slot: str, layer: str, specific_id: int = -1):
    save = get_map_slot(slot)
    geo = {
        "type": "FeatureCollection",
        "features": [],
    }
    if layer == "spawns":
        for tile in save.tiles:
            for vspawn in tile.spawn_data.vehicles.items():
                if specific_id < 0 or specific_id == vspawn.data.respawn_id:
                    item = make_geodata(
                        id=vspawn.data.respawn_id,
                        properties={
                            "kind": "vehicle_spawn",
                            "team": tile.spawn_data.team_id,
                            "team_color": get_team_color(tile.team_control),
                            "definition_index": vspawn.data.definition_index,
                            "hitpoints": vspawn.data.hitpoints,
                            "tile": tile.id
                        },
                        geometry={
                            "type": "Point",
                            "coordinates": loc_to_geo(vspawn.data.world_position)
                        }
                    )
                    geo["features"].append(item)
                    if specific_id >= 0:
                        break

    elif layer == "tiles":
        for tile in save.tiles:
            if specific_id < 0 or specific_id == tile.id:
                item = make_geodata(
                    id=tile.id,
                    properties={
                        "kind": "tile",
                        "name": get_island_name(tile.id),
                        "team": tile.team_control,
                        "team_color": get_team_color(tile.team_control),
                        "difficulty": tile.difficulty_factor,
                        "facility.category": tile.facility.category,
                        "radius": cc2_to_minutes(tile.island_radius),
                        "loc": loc_to_geo(tile.loc),
                    },
                    geometry={
                        "type": "Polygon",
                        "coordinates": loc_to_geo_box(tile.loc, tile.island_radius, tile.island_radius)
                    }
                )
                geo["features"].append(item)
                if specific_id >= 0:
                    break

    return geo


@app.route("/map/<slot>")
def map_route(slot):
    save = get_map_slot(slot)
    return render_template("map.html", save=save, slot=slot)


@app.route("/move/<slot>/<kind>/<int:item>", methods=["POST"])
def move_item(slot: str, kind: str, item: int):
    data = request.json
    position = latlong_to_cc2loc(data["lat"], data["lng"])
    moved = []
    save = get_map_slot(slot)
    if kind == "tile":
        island = save.tile(item)
        island.move(position.x, island.loc.y, position.z)
        for spawn in island.spawn_data.vehicles.items():
            moved.append({"kind": "spawn", "id": spawn.data.respawn_id})

    elif kind == "spawn":
        # find the island with this spawn
        found = save.spawn(item)
        if found:
            found.move(position.x, found.data.world_position.y, position.z)
            moved.append({"kind": "spawn", "id": item})

    return {
        "moved": moved
    }
