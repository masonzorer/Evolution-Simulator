# Main driver for the simulation
from random import randint
import numpy as np
import time
import pygame
import prey
import predator

init_predators = 100
init_prey = 100

max_predators = 300
max_prey = 500

grid_size = 225
scaling_factor = 4

PREY = []
PREDATORS = []

WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

def check_occupied(game_board, x, y, is_predator):
    if (x >= 0 and x < game_board.shape[0] and y >= 0 and y < game_board.shape[1]) == False:
        return True
    elif game_board[x, y] == 0 and is_predator == False:
        return True
    elif game_board[x, y] == 1 and is_predator == True:
        return True
    else:
        return False

def find_random_unoccupied(game_board, is_predator):
    x, y = randint(0, grid_size-1), randint(0, grid_size-1)
    while check_occupied(game_board, x, y, is_predator):
        x, y = randint(0, grid_size-1), randint(0, grid_size-1)
    return x, y
    

def create_population(num_prey, num_predators):
    game_board = np.full((grid_size, grid_size), -1)

    for i in range(num_prey):
        # Create new prey with random starting position
        x, y = find_random_unoccupied(game_board, False)
        nprey = prey.Prey(x, y)
        game_board[nprey.x, nprey.y] = 0
        PREY.append(nprey)

    for i in range(num_predators):
        # Create new predator with random starting position
        x, y = find_random_unoccupied(game_board, True)
        npredator = predator.Predator(x, y)
        game_board[npredator.x, npredator.y] = 1
        PREDATORS.append(npredator)

def main():
    # create simulation game board
    screen = None
    clock = None
 
    screen_width, screen_height = grid_size, grid_size

    pygame.init()
    win = pygame.display.set_mode((screen_width*scaling_factor, screen_height*scaling_factor))
    screen = pygame.Surface((screen_width, screen_height))
    clock = pygame.time.Clock() 

    # create the original population
    create_population(init_prey, init_predators)

    # start the simulation
    while 1:
        # update game board
        screen.fill(WHITE)

        # init new board state
        game_board = np.full((grid_size, grid_size), -1)

        # update game board positions
        for prey in PREY:
            game_board[prey.x, prey.y] = 0
        for predator in PREDATORS:
            game_board[predator.x, predator.y] = 1

        # update each entity
        for prey in PREY:
            pygame.draw.circle(screen, GREEN, (prey.x, prey.y), 1)
            prey.update(game_board, PREDATORS, PREY, max_prey)
        for predator in PREDATORS:
            pygame.draw.circle(screen, RED, (predator.x, predator.y), 1)
            predator.update(game_board, PREDATORS, PREY, max_predators)

        win.blit(pygame.transform.scale(screen, win.get_rect().size), (0, 0))
        pygame.display.update()
        clock.tick(60)

        print(f'predators: {len(PREDATORS)}, prey: {len(PREY)}')
        time.sleep(.02)
        

if __name__ == "__main__":
    main()