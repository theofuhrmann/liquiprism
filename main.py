import pygame

from liquiprism import Liquiprism
from sonifier import Sonifier
from visualizer import Visualizer

SIZE = 7
RANDOM_UPDATE_RATE = True
STEP_TIME = 1000


def main():
    pygame.display.set_caption("3D Liquiprism Visualizer")
    liquiprism = Liquiprism(size=SIZE, random_update_rate=RANDOM_UPDATE_RATE)
    visualizer = Visualizer(liquiprism)
    sonifier = Sonifier(liquiprism)

    running = True
    last_step_time = pygame.time.get_ticks()
    space_pressed = False

    while running:
        visualizer.screen.fill((0, 0, 0))

        current_time = pygame.time.get_ticks()
        if current_time - last_step_time >= STEP_TIME:
            visualizer.liquiprism.step()
            sonifier.update()
            last_step_time = current_time

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            visualizer.angle_x += 0.05
        if keys[pygame.K_DOWN]:
            visualizer.angle_x -= 0.05
        if keys[pygame.K_LEFT]:
            visualizer.angle_y += 0.05
        if keys[pygame.K_RIGHT]:
            visualizer.angle_y -= 0.05
        if keys[pygame.K_SPACE]:
            if not space_pressed:
                # visualizer.liquiprism.step()
                # sonifier.update()
                space_pressed = True
        else:
            space_pressed = False

        visualizer.render()

        pygame.display.flip()
        visualizer.clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
