from pathlib import Path
from io import StringIO

from ..savedata.constants import BIOME_GREEN
from ..savedata.loader import load_save_file

HERE = Path(__file__).parent


def test_read_save():
    cc2 = load_save_file(str(HERE / "basic-save.xml"))
    assert len(cc2.tiles) == 4

    assert len(cc2.teams) == 3

    first_tile = cc2.tile(1)
    # move it 2500 east
    first_tile.world_position.x += 2500

    # make x islands in a vertical row
    for i in range(5):
        island = cc2.new_tile()
        island.biome_type = i
        island.team_control = 1
        island.set_position(x=7000, z=6000 + (3000 * i))

    # move the team 1 (player) carrier right on top of the island
    vehicles = cc2.vehicles
    for v in vehicles:
        if v.attrib.get("team_id") == "1":
            if v.attrib.get("definition_index") == "0":
                # carrier
                transfm = v.findall("transform")[0]
                break

    saved = cc2.export()
    assert saved
    saved = saved.replace("> ", ">\n")
    with open("save.xml", "w") as fd:
        fd.write(saved)
