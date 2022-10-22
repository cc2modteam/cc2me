from random import randrange

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