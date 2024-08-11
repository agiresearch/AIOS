import pygame

pygame.init()

screen_width = 640
screen_height = 480

snake_position = [100, 100]
food_position = [200, 200]

score = 0

while True:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Update game state
    snake_position[0] += 10
    snake_position[1] += 10

    # Render game graphics
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.draw.rect(screen, (255, 0, 0), (snake_position[0], snake_position[1], 20, 20))
    pygame.draw.rect(screen, (0, 255, 0), (food_position[0], food_position[1], 20, 20))

    # Update score
    score += 1

    # Check for collisions
    if snake_position[0] >= screen_width or snake_position[1] >= screen_height:
        print("Game Over!")
        break

    pygame.display.update()
    pygame.time.delay(100)
