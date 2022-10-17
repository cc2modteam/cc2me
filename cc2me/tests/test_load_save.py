from pathlib import Path
import random

from ..savedata.constants import VEHICLE_DEF_CARRIER, BIOME_DARK_MESAS
from ..savedata.loader import load_save_file

HERE = Path(__file__).parent


def test_read_save():
    cc2 = load_save_file(str(HERE / "canned_saves" / "save.xml"))
    assert len(cc2.tiles) == 4

    assert len(cc2.teams) == 3

    first_tile = cc2.tile(1)
    # move it 2500 east
    first_tile.world_position.x += 2500

    # make a 5 x 5 grid of islands close together
    sep = 1000
    for j in range(5):
        for i in range(5):
            spread = random.randint(250, 1600)
            island = cc2.new_tile()
            island.biome_type = i
            island.team_control = 1
            island.set_position(x=7000 + (spread * j), z=6000 + (spread * i))

    # move the team 1 (player) carrier
    carriers = cc2.find_vehicles_by_definition(VEHICLE_DEF_CARRIER)
    team1_carrier = [x for x in carriers if x.team_id == 1][0]
    # put the carrier near to the first island
    team1_carrier.set_location(x=first_tile.world_position.x + first_tile.bounds.max.x, z=first_tile.world_position.z)

    # remove the first tile
    cc2.remove_tile(first_tile)

    saved = cc2.export()
    assert saved
    saved = saved.replace("> ", ">\n")
    with open("save.xml", "w") as fd:
        fd.write(saved)
