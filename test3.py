import pygame
import game
import logger

size = game.size

pygame.init()
screen = pygame.display.set_mode((size * 40, size * 42))

g = game.Game(screen)
clock = pygame.time.Clock()
run = True

logger.reset_log()
logger.log("Game Initialized")

g.load_config()

while run:
    clock.tick(60)
    run = g.update()
    g.draw()
    pygame.display.update()

g.save_config()

g.quit()
pygame.quit()
logger.log('Game quit successfully')
