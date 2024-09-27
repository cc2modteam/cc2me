"""The CC2 Map Editor (pygame version)"""
import argparse
import pygame
from pathlib import Path

from cc2me.savedata.loader import load_save_file
from .map import MapRenderer
from .gfx import GfxContext

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
    if lanapixel.exists():
        font = pygame.font.Font(lanapixel, 10)
    else:
        font = pygame.font.SysFont("dejavusansmono", 10)

    screen = pygame.display.set_mode((1024, 480), pygame.RESIZABLE|pygame.DOUBLEBUF, 32)
    gfx = GfxContext(screen, [font])
    world = MapRenderer(gfx)
    if filename:
        save = load_save_file(filename)
        world.load(save)

    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            world.event(event)


        screen.fill((0, 0, 0, 255))
        world.draw()

        pygame.display.flip()
        clock.tick(20)


if __name__ == "__main__":
    run()
