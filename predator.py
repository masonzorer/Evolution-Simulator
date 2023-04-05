# predator species for simulation

# input: current position, and nearest prey position
# total inputs: 4 inputs

# direction of movement
# possible outputs: still, up, down, left, right, upright, upleft, downright, downleft

import simulation
import torch
import numpy as np
import random

directions = [(0,0), (0,-1), (0,1), (-1,0), (1,0), (-1,-1), (1,-1), (-1, 1), (1,1)]

class Predator:
    def __init__(self, x, y):
        # current position
        self.x = x
        self.y = y

        # life variables
        self.detect_radius = 5
        self.max_seconds = 75

        self.seconds_to_live = self.max_seconds
        self.kills_to_reproduce = 1

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
        if simulation.check_occupied(game_board, new_x, new_y, True):
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
        return simulation.find_random_unoccupied(game_board, True)

    def reproduce(self, predators, game_board):
        # Create a copy of the prey with a slightly mutated neural network brain
        new_predator = Predator(self.x, self.y)
        for child_param, parent_param in zip(new_predator.brain.parameters(), self.brain.parameters()):
            child_param.data = parent_param.data.clone() + torch.randn_like(parent_param.data) * 0.1
        dx, dy = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])

        # Check if chosen space is occupied, if so pick random
        '''
        if simulation.check_occupied(game_board, self.x+dx, self.y+dy, True):
            dx, dy = self.check_surrounding(game_board)
            new_predator.x = dx
            new_predator.y = dy
        else:
            new_predator.move((dx, dy), game_board)
        '''
        new_predator.move((dx, dy), game_board)

        predators.append(new_predator)


    def hunt_prey(self, prey):
        prey_to_kill = None
        for p in prey:
            if p.x == self.x and p.y == self.y:
                prey_to_kill = p
                break
        if prey_to_kill is not None:
            # closer to reproduction
            self.kills_to_reproduce -= 1
            # reset death clock
            self.seconds_to_live = self.max_seconds
            # kill prey
            prey.remove(prey_to_kill)

    def update(self, game_board, predators, prey, max):
        self.seconds_to_live -= 1

        # reproduce
        if self.kills_to_reproduce == 0:
            self.kills_to_reproduce = 1
            if len(predators) < max:
                self.reproduce(predators, game_board)

        # die if out of time
        if self.seconds_to_live <= 0:
            predators.remove(self)

        # Get brain inputs
        perception = self.get_input(game_board)

        # convert outputs into movement direction
        output = self.brain(torch.tensor(perception, dtype=torch.float32))
        output_array = output.detach().numpy()
        movement = output_array.argmax()

        # map movement to direction
        direction = directions[movement]

        self.move(direction, game_board)
        self.hunt_prey(prey)