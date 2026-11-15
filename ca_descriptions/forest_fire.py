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
BURNT_CHAPARRAL, BURNT_FOREST, BURNT_CANYON, BURNT_TOWN = range(6, 10)

 # State each terrain becomes once burnt out (lakes never burn)
BURNT_STATES = np.array([BURNT_CHAPARRAL, BURNT_FOREST, BURNT_CANYON,
                         LAKE, BURNT_TOWN])

# Real minutes per step, set by how fast the fire front crosses a cell
STEP_MINUTES = 30
# Hours each terrain keeps burning, midpoints of the team's ranges
# (canyon 1 to 6 hours, chaparral 2 to 5 days, forest 2 to 4 weeks)
BURN_HOURS = np.array([84, 504, 3.5, 0, 84])
BURN_STEPS = BURN_HOURS * 60 / STEP_MINUTES

# Cells that caught fire last step, which spread fire at full strength
FIRE_FRONT = 10

# Base chance a burning neighbour spreads fire, with no wind or slope
# (Alexandridis et al. 2008, Table 4)
P_H = 0.58
# How strongly cells burning behind the front still spread fire,
# as a fraction of the front's chance (our own choice, to be tested)
RESIDUAL_SPREAD = 0.001
# Ignition adjustment per terrain, our own values ordered by the brief
VEG_FACTOR = np.array([0, -0.4, 0.4, 0, 0])

# Wind (Alexandridis et al. 2008, Table 4)
WIND_SPEED = 8      # m/s
WIND_FROM = 0       # compass bearing the wind blows from, 0 = northerly
C1 = 0.045
C2 = 0.131
# Bearing fire travels when it spreads from each neighbour into the cell,
# in CAPyLE's neighbour order [NW, N, NE, W, E, SW, S, SE]
SPREAD_BEARINGS = np.array([135, 180, 225, 90, 270, 45, 0, 315])

CELL_KM = 0.5
GRID_SIZE = 100


def to_cells(km):
    # Adding 0.5 rounds halves up, so the 2.5 km town stays 5 cells wide
    return int(km / CELL_KM + 0.5)


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
    config.states = (CHAPARRAL, FOREST, CANYON, LAKE, TOWN, BURNING,
                     BURNT_CHAPARRAL, BURNT_FOREST, BURNT_CANYON, BURNT_TOWN,
                     FIRE_FRONT)

    config.state_colors = [(0.75, 0.75, 0), (0.3, 0.35, 0.15), (1, 1, 0.2),
                           (0.2, 0.6, 1), (0, 0, 0), (1, 0.2, 0),
                           (0.4, 0.38, 0.25), (0.25, 0.25, 0.2),
                           (0.55, 0.52, 0.4), (0.45, 0.45, 0.45), (1, 0.65, 0)]

    config.grid_dims = (GRID_SIZE, GRID_SIZE)
    config.num_generations = 1000
    config.wrap = False

    terrain = build_terrain()
    terrain[0, GRID_SIZE - 1] = FIRE_FRONT
    config.initial_grid = terrain

    # ----------------------------------------------------------------------

    # the GUI calls this to pass the user defined config
    # into the main system with an extra argument
    # do not change
    if len(args) == 2:
        config.save()
        sys.exit()

    return config


# Wind factor for fire arriving from each neighbour (Alexandridis eq. 3)
def wind_factors(wind_from, speed):
    wind_to = wind_from + 180
    theta = np.radians(SPREAD_BEARINGS - wind_to)

    return np.exp(speed * (C1 + C2 * (np.cos(theta) - 1)))


# Function to apply the transition rules and return the new grid
def transition_function(grid, neighbourstates, neighbourcounts, terrain,
                        burn_time, wind):
    # Work out every mask from the current grid before changing it
    has_fuel = np.isin(grid, [CHAPARRAL, FOREST, CANYON, TOWN])
    front = grid == FIRE_FRONT
    burning = front | (grid == BURNING)

    # Front neighbours spread at full strength and burning neighbours weakly,
    # both pushed by wind
    p_burn = P_H * (1 + VEG_FACTOR[terrain])
    p_escape = np.ones(grid.shape)
    for i in range(8):
        p = np.minimum(p_burn * wind[i], 1)
        from_front = neighbourstates[i] == FIRE_FRONT
        from_burning = neighbourstates[i] == BURNING
        p_escape[from_front] *= 1 - p[from_front]
        p_escape[from_burning] *= 1 - RESIDUAL_SPREAD * p[from_burning]
    catches_fire = has_fuel & (np.random.random(grid.shape) < 1 - p_escape)

    # Count how long each burning cell has been alight
    burn_time[burning] += 1
    burnt_out = burning & (burn_time >= BURN_STEPS[terrain])

    grid[front] = BURNING
    grid[burnt_out] = BURNT_STATES[terrain[burnt_out]]
    grid[catches_fire] = FIRE_FRONT

    return grid




# Main function that sets up, runs and saves CA
def main():
    # Get the config object from set up
    config = setup(sys.argv[1:])

    # Original terrain map, so burning cells still know what fuel they had
    terrain = build_terrain()

    # Number of steps each cell has been burning for, kept between steps
    burn_time = np.zeros((GRID_SIZE, GRID_SIZE))

    # Wind factor per neighbour direction, fixed for the whole run
    wind = wind_factors(WIND_FROM, WIND_SPEED)

    # Create grid object using parameters from config + transition function
    grid = Grid2D(config, (transition_function, terrain, burn_time, wind))

    # Run the CA, save grid state every generation to timeline
    timeline = grid.run()

    # Save updated config to file
    config.save()
    
    # Save timeline to file
    utils.save(timeline, config.timeline_path)

if __name__ == "__main__":
    main()
