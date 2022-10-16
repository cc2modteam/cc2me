from pathlib import Path
from io import StringIO
from ..savedata.loader import load_save_file

HERE = Path(__file__).parent


def test_read_save():
    cc2 = load_save_file(str(HERE / "basic-save.xml"))
    assert len(cc2.tiles) == 4

    assert len(cc2.teams) == 3

    first_tile = cc2.tile(1)
    # move it 2500 east
    first_tile.world_position.x += 2500

    # make a new island
    island2 = cc2.new_tile()
    island2.biome_type = 3
    island2.team_control = 1
    island2.seed = 31
    island2.set_position(x=6500, z=5000)

    # move the team 1 (player) carrier right on top of the island
    vehicles = cc2.vehicles
    for v in vehicles:
        if v.attrib.get("team_id") == "1":
            if v.attrib.get("definition_index") == "0":
                # carrier
                transfm = v.findall("transform")[0]


    saved = cc2.export()
    assert saved
    saved = saved.replace("> ", ">\n")
    with open("save.xml", "w") as fd:
        fd.write(saved)
