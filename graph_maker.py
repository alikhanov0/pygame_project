# Imports
import pygame


# Initialize game engine
pygame.init()


# Window
WIDTH = 36 * 32
HEIGHT = 10 * 32
SIZE = ([WIDTH, HEIGHT])
TITLE = "_____________________________________"
screen = pygame.display.set_mode(SIZE)
pygame.display.set_caption(TITLE)


# Timer
clock = pygame.time.Clock()
refresh_rate = 60


# Colors
WHITE = (255, 255, 255)
GRAY = (175, 175, 175)

# Game loop
done = False

while not done:
    # Event processing
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
            

    # Drawing code
    screen.fill(WHITE)

    for x in range(0, WIDTH, 32):
        pygame.draw.line(screen, GRAY, [x, 0], [x, HEIGHT], 1)

    for y in range(0, HEIGHT, 32):
        pygame.draw.line(screen, GRAY, [0, y], [WIDTH, y], 1)


    # Update screen (Actually draw the picture in the window.)
    pygame.display.flip()


    # Limit refresh rate of game loop 
    clock.tick(refresh_rate)


# Close window and quit
pygame.quit()
