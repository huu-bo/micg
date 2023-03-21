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

try:
    g.load_config()
except Exception as e:
    logger.log("Failed to load config! Error traceback: ")
    logger.log(str(e))
    pass

while run:
    clock.tick(60)
    run = g.update()
    g.draw()
    pygame.display.update()

try:
    g.save_config()
except Exception as e:
    logger.log("Failed to save config! Error traceback: ")
    logger.log(str(e))
    pass

g.quit()
pygame.quit()
logger.log('Game quit successfully')
