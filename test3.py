import pygame

import game

size = game.size

pygame.init()
screen = pygame.display.set_mode((size * 40, size * 42))
# screen = pygame.display.set_mode((800, 880))

g = game.Game(screen)
clock = pygame.time.Clock()
run = True
while run:
    clock.tick(60)
    run = g.update()
    g.draw()
    pygame.display.update()

pygame.quit()
