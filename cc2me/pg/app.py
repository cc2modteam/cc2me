"""The CC2 Map Editor (pygame version)"""
import argparse
import pygame
from pathlib import Path

from cc2me.savedata.loader import load_save_file
from .map import MapRenderer
from .gfx import GfxContext, Frame, Point, Label

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("SAVE", type=Path, nargs="?")

cc2 = Path("C:\Program Files (x86)\Steam\steamapps\common\Carrier Command 2")
cc2_locale = cc2 / "mod_dev_kit"/ "source" / "locale"



def run(args=None):
    opts = parser.parse_args(args)
    filename = opts.SAVE

    pygame.init()
    pygame.font.init()

    lanapixel = cc2_locale / "lanapixel.ttf"
    font_size = 24
    if lanapixel.exists():
        font = pygame.font.Font(lanapixel, font_size)
    else:
        font = pygame.font.SysFont("dejavusansmono", font_size)

    pygame_flags = pygame.DOUBLEBUF|pygame.RESIZABLE# |pygame.SCALED
    screen_width = 550
    screen_height = 300

    screen = pygame.display.set_mode((screen_width, screen_height), pygame_flags, 32)

    gfx = GfxContext(screen, font)

    world = MapRenderer(gfx)

    toolbar = Frame(gfx,
                    Point.new(0, 0), Point.new(gfx.w, gfx.font.get_height()),
                    border=pygame.Color("#232323"),
                    background=pygame.Color("#cdcdcd"))
    Label(toolbar, Point.new(2, 2), "CC2ME",
          color=pygame.Color("#000000"))

    if filename:
        save = load_save_file(filename)
        world.load(save)

    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.VIDEORESIZE:
                pass
                # pygame.display.set_mode((int(event.w / scale), int(event.h / scale)), pygame_flags, 32)
                # continue

            if event.type == pygame.QUIT:
                running = False

            world.event(event)


        screen.fill((0, 0, 0, 255))
        world.draw()
        toolbar.draw()
        pygame.display.flip()
        toolbar.size = Point.new(gfx.w, toolbar.size.y)
        clock.tick(20)


if __name__ == "__main__":
    run()
