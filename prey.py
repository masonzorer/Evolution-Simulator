# prey species for simulation

# input: current position, and nearest predator position
# total inputs: 4 inputs

# direction of movement
# total outputs: still, up, down, left, right, upright, upleft, downright, downleft

import simulation
import torch
import numpy as np
import random

directions = [(0,0), (0,-1), (0,1), (-1,0), (1,0), (-1,-1), (1,-1), (-1, 1), (1,1)]

class Prey:
    def __init__(self, x, y):
        # current position
        self.x = x
        self.y = y

        # life variables
        self.detect_radius = 5
        self.max_seconds = 50

        self.max_energy = 25
        self.current_energy = self.max_energy
        self.cooldown = False
        self.max_cooldown = 5
        self.current_cooldown = self.max_cooldown

        self.seconds_to_reproduce = self.max_seconds

        self.brain = torch.nn.Sequential(
            torch.nn.Linear(16, 32),
            torch.nn.ReLU(),
            torch.nn.Linear(32, 9)
        )

    def get_input(self, game_board):
        # simulate entity sight
        rows, cols = game_board.shape
        scan = np.full((8, 2), -1)

        # search surrounding area
        for i, (dx, dy) in enumerate(directions[1:]):
            distance = 0
            curr_x = self.x
            curr_y = self.y
            while distance <= self.detect_radius:
                curr_x += dx
                curr_y += dy
                # check for boundary
                if curr_x < 0 or curr_x >= rows or curr_y < 0 or curr_y >= cols:
                    break
                # increment distance
                distance += 1
                value = game_board[curr_x, curr_y]
                if value == 0 or value == 1:
                    # Update the results array with the direction and distance
                    scan[i] = [value, distance]
                    break
        return scan.reshape(-1)

    def move(self, direction, game_board):
        dx, dy = direction
        new_x, new_y = self.x + dx, self.y + dy
        # Wrap around the x-axis
        if new_x < 0:
            new_x = simulation.grid_size-1
        elif new_x >= simulation.grid_size:
            new_x = 0

        # Wrap around the y-axis
        if new_y < 0:
            new_y = simulation.grid_size-1
        elif new_y >= simulation.grid_size:
            new_y = 0

        # Check if moving into another
        if simulation.check_occupied(game_board, new_x, new_y, False):
            new_x, new_y = self.x, self.y
        
        # move agent
        self.x, self.y = new_x, new_y

    def check_surrounding(self, game_board):
        for i in range(self.x-1, self.x+2):
            for j in range(self.y-1, self.y+2):
            # Skip current point
                if i == self.x and j == self.y:
                    continue
                # Check for boundaries
                if i >= 0 and i < game_board.shape[0] and j >= 0 and j < game_board.shape[1]:
                    if game_board[i, j] == -1:
                        return i, j
        return simulation.find_random_unoccupied(game_board, False)

    def reproduce(self, prey, game_board):
        # Create a copy of the prey with a slightly mutated neural network brain
        new_prey = Prey(self.x, self.y)
        for child_param, parent_param in zip(new_prey.brain.parameters(), self.brain.parameters()):
            child_param.data = parent_param.data.clone() + torch.randn_like(parent_param.data) * 0.1
        dx, dy = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])

        # Check if chosen space is occupied, if so pick random
        '''
        if simulation.check_occupied(game_board, self.x+dx, self.y+dy, False):
            dx, dy = self.check_surrounding(game_board)
            new_prey.x = dx
            new_prey.y = dy
        else:
            new_prey.move((dx, dy), game_board)
        '''
        new_prey.move((dx, dy), game_board)

        prey.append(new_prey)

    def update(self, game_board, predators, prey, max):

        self.seconds_to_reproduce -= 1

        # reproduce
        if self.seconds_to_reproduce == 0:
            self.seconds_to_reproduce = self.max_seconds
            if (len(prey) < max):
                self.reproduce(prey, game_board)

        # Get brain inputs
        perception = self.get_input(game_board)

        # convert outputs into movement direction
        output = self.brain(torch.tensor(perception, dtype=torch.float32))
        output_array = output.detach().numpy()
        movement = output_array.argmax()

        # map movement to direction
        direction = directions[movement]

        if self.current_energy == 0:
            self.cooldown = True

        if self.current_cooldown == 0:
            self.current_cooldown = self.max_cooldown
            self.current_energy = self.max_energy
            self.cooldown = False

        if self.cooldown == True:
            self.current_cooldown -= 1
        else:
            self.current_energy -= 1
            self.move(direction, game_board)

