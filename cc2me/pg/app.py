"""The CC2 Map Editor (pygame version)"""
import argparse
import pygame
from pathlib import Path

from cc2me.savedata.loader import load_save_file
from .map import MapRenderer

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("SAVE", type=Path, nargs="?")


def run(args=None):
    opts = parser.parse_args(args)
    filename = opts.SAVE

    pygame.init()
    screen = pygame.display.set_mode((1024, 480), pygame.RESIZABLE|pygame.DOUBLEBUF, 32)
    world = MapRenderer(screen)
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
