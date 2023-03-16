import pygame
import game
import logger

size = game.size

pygame.init()
screen = pygame.display.set_mode((size * 40, size * 42))

g = game.Game(screen)
clock = pygame.time.Clock()
run = True

logger.resetLog()
logger.log("Game Initialized")

while run:
    clock.tick(60)
    run = g.update()
    g.draw()
    pygame.display.update()

pygame.quit()
