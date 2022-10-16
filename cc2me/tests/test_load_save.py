from pathlib import Path
from io import StringIO
from ..savedata.loader import load_save_file

HERE = Path(__file__).parent


def test_read_save():
    data = load_save_file(str(HERE / "basic-save.xml"))
    assert data

    scene = StringIO()
    data["scene"].write(scene, encoding="unicode")

    assert True