# Name: Forest fire
# Dimensions: 2

# --- Set up executable path, do not edit ---
import sys
import inspect
this_file_loc = (inspect.stack()[0][1])
main_dir_loc = this_file_loc[:this_file_loc.index('ca_descriptions')]
sys.path.append(main_dir_loc)
sys.path.append(main_dir_loc + 'capyle')
sys.path.append(main_dir_loc + 'capyle/ca')
sys.path.append(main_dir_loc + 'capyle/guicomponents')
# ---

from capyle.ca import Grid2D, Neighbourhood, randomise2d
import capyle.utils as utils

import numpy as np

CHAPARRAL, FOREST, CANYON, LAKE, TOWN, BURNING = range(6)
CELL_KM = 0.25
GRID_SIZE = 200


def to_cells(km):
    return int(round(km / CELL_KM))


# Fills a rectangle given in km, with y measured from the south edge
def fill_rect(grid, state, left, right, bottom, top):
    grid[to_cells(50 - top):to_cells(50 - bottom),
         to_cells(left):to_cells(right)] = state


def build_terrain():
    grid = np.full((GRID_SIZE, GRID_SIZE), CHAPARRAL)

    fill_rect(grid, FOREST, 0, 25, 42.5, 45)
    fill_rect(grid, FOREST, 5, 12.5, 20, 42.5) 
    fill_rect(grid, FOREST, 5, 25, 15, 20) 
    fill_rect(grid, FOREST, 32.5, 45, 35, 40)
    fill_rect(grid, LAKE, 17.5, 22.5, 27.5, 37.5)
    fill_rect(grid, LAKE, 37.5, 40, 10, 22.5)
    fill_rect(grid, CANYON, 25, 45, 25, 27.5)
    fill_rect(grid, TOWN, 18.75, 21.25, 3.75, 6.25)

    return grid


# Set up the config object used to interact with the GUI
def setup(args):
    config_path = args[0]
    config = utils.load(config_path)
    # -- THE CA MUST BE RELOADED IN THE GUI IF ANY OF THE BELOW ARE CHANGED --

    config.title = "Forest fire"
    config.dimensions = 2
    config.states = (CHAPARRAL, FOREST, CANYON, LAKE, TOWN, BURNING)

    config.state_colors = [(0.75, 0.75, 0), (0.3, 0.35, 0.15), (1, 1, 0.2),
                           (0.2, 0.6, 1), (0, 0, 0), (1, 0.2, 0)]
    config.grid_dims = (GRID_SIZE, GRID_SIZE)
    config.num_generations = 300
    config.wrap = False

    terrain = build_terrain()
    terrain[0, GRID_SIZE - 1] = BURNING
    config.initial_grid = terrain

    # ----------------------------------------------------------------------

    # the GUI calls this to pass the user defined config
    # into the main system with an extra argument
    # do not change
    if len(args) == 2:
        config.save()
        sys.exit()

    return config


# Function to apply the transition rules and return the new grid
def transition_function(grid, neighbourstates, neighbourcounts):
    # YOUR CODE HERE
    return grid


# Main function that sets up, runs and saves CA
def main():
    # Get the config object from set up
    config = setup(sys.argv[1:])

    # Create grid object using parameters from config + transition function
    grid = Grid2D(config, transition_function)

    # Run the CA, save grid state every generation to timeline
    timeline = grid.run()

    # Save updated config to file
    config.save()
    
    # Save timeline to file
    utils.save(timeline, config.timeline_path)

if __name__ == "__main__":
    main()
