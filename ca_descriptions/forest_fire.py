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

# Real minutes per step. Fire moves at most one cell per step, so 500 m
# every 10 minutes gives a top speed of 3 km/h, about 10% of an 8 m/s wind
# (Cruz and Alexander 2019)
STEP_MINUTES = 10

# Shortest and longest hours each terrain burns, from the team's ranges
# (canyon 1 to 6 hours, chaparral 2 to 5 days, forest 2 to 4 weeks).
# Town uses the chaparral range
BURN_HOURS_MIN = np.array([48, 336, 1, 0, 48])
BURN_HOURS_MAX = np.array([120, 672, 6, 0, 120])

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

# Ignition sites from the brief, as (row, column) with row 0 at the north edge
POWER_PLANT = (0, 0)
INCINERATOR = (0, GRID_SIZE - 1)
# Where the fire starts in this run
IGNITION = INCINERATOR
# The fire starts on a 2 x 2 block of cells (1 km2) at the site, so it cannot
# die out on the first step by bad luck
IGNITION_CELLS = 2

# Cells soaked by the water drop, which cannot burn until they dry
WET = 11

# Water drop for Q3, enough water to cover about 12.5 km2
# Hours after ignition the water is dropped. The fire reaches the town at
# 14.5 h at the earliest, so 10 h keeps the strip wet when it arrives
# (mean +6.1 h, against +4.1 h for a 6 h drop). 12 h gives a mean of +6.7 h
# but the same median (+4.0 h) and leaves only 2.5 h of margin
DROP_HOURS = 10
WET_HOURS = 12      # hours until soaked cells dry out
# Drop area in km as (left, right, bottom, top): a 12.5 km x 1 km strip
# (50 cells) along the town's north edge, the best of 1,020 positions in Q3
DROP_AREA = (12.5, 25, 5, 6)
DROP_STEP = int(DROP_HOURS * 60 / STEP_MINUTES)
DRY_STEP = DROP_STEP + int(WET_HOURS * 60 / STEP_MINUTES)

# Other drops for Results III, as (row, column) cells. A ring one cell wide
# touching the town (rows 88 to 92, columns 38 to 42) on every side, only
# 24 cells
TOWN_RING = [(row, col) for row in range(87, 94) for col in range(37, 44)
             if row in (87, 93) or col in (37, 43)]
# Early drops at the incinerator, where the fire starts on rows 0 to 1,
# columns 98 to 99 and spreads up to 6 cells an hour. FIRE_BLOCK soaks a
# 3.5 km square over the fire, 49 cells, as a 50th cell would stick out
FIRE_BLOCK = [(row, col) for row in range(7) for col in range(93, 100)]
# L shapes boxing the fire into its corner, 6 km out (25 cells) and 12 km
# out (49 cells), each a line south of the fire and a line west of it
BOX_6KM = ([(12, col) for col in range(87, 100)]
           + [(row, 87) for row in range(12)])
BOX_12KM = ([(24, col) for col in range(75, 100)]
            + [(row, 75) for row in range(24)])

# Drop the GUI run uses, as the cells (None for the DROP_AREA strip) and the
# hours after ignition it lands. Early drops only work if they land before
# the fire passes them, so each lands at the last whole or half hour that
# works (median delay over 20 runs in brackets): fire_block puts the fire
# out at 0.5 h but does nothing at 1 h, box_6km at 1 h (+15.1 h) does
# nothing at 2 h, box_12km at 3 h (+13.7 h) does nothing at 4 h. The strip
# gives +4.0 h and town_ring +10.4 h
DROP_PLANS = {'strip': (None, DROP_HOURS),
              'town_ring': (TOWN_RING, DROP_HOURS),
              'fire_block': (FIRE_BLOCK, 0.5),
              'box_6km': (BOX_6KM, 1),
              'box_12km': (BOX_12KM, 3)}
DROP_PLAN = 'box_12km'

# The extreme forest case: the top forest band made 10 km thick and stretched
# across the whole map (306 km2 of new forest). Median delay 0 h over 20
# runs, and 1.2 h even at 20 km thick
FOREST_WALL = (0, 50, 35, 45)
# Extra dense forest planted for Q4 as (left, right, bottom, top) in km, or
# None for the map as given. Only chaparral and canyon get replanted. Set it
# to FOREST_WALL to watch the wall in the GUI
EXTRA_FOREST = None



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

    if EXTRA_FOREST is not None:
        planted = np.zeros(grid.shape, dtype=bool)
        fill_rect(planted, True, *EXTRA_FOREST)
        grid[planted & np.isin(grid, [CHAPARRAL, CANYON])] = FOREST

    return grid


# Block of cells the fire starts on, kept inside the map at corner sites
def ignition_block(site):
    row = min(site[0], GRID_SIZE - IGNITION_CELLS)
    col = min(site[1], GRID_SIZE - IGNITION_CELLS)
    return (slice(row, row + IGNITION_CELLS),
            slice(col, col + IGNITION_CELLS))


# Set up the config object used to interact with the GUI
def setup(args):
    config_path = args[0]
    config = utils.load(config_path)

    # -- THE CA MUST BE RELOADED IN THE GUI IF ANY OF THE BELOW ARE CHANGED --

    config.title = "Forest fire"
    config.dimensions = 2
    config.states = (CHAPARRAL, FOREST, CANYON, LAKE, TOWN, BURNING,
                     BURNT_CHAPARRAL, BURNT_FOREST, BURNT_CANYON, BURNT_TOWN,
                     FIRE_FRONT, WET)

    # Burnt states are greys so they stand apart from the greens of fuel
    config.state_colors = [(0.75, 0.75, 0), (0.3, 0.35, 0.15), (1, 1, 0.2),
                           (0.2, 0.6, 1), (0, 0, 0), (1, 0.2, 0),
                           (0.5, 0.5, 0.5), (0.35, 0.35, 0.35),
                           (0.65, 0.65, 0.65), (0.25, 0.25, 0.25), (1, 0.65, 0),
                           (0.6, 0.85, 1)]

    config.grid_dims = (GRID_SIZE, GRID_SIZE)
    config.num_generations = 1000
    config.wrap = False

    terrain = build_terrain()
    terrain[ignition_block(IGNITION)] = FIRE_FRONT
    config.initial_grid = terrain

    # ----------------------------------------------------------------------

    # the GUI calls this to pass the user defined config
    # into the main system with an extra argument
    # do not change
    if len(args) == 2:
        config.save()
        sys.exit()

    return config


# Picks how many steps each cell will burn for, anywhere in its terrain's range
def random_burn_steps(terrain):
    hours = np.random.uniform(BURN_HOURS_MIN[terrain], BURN_HOURS_MAX[terrain])
    
    return hours * 60 / STEP_MINUTES


# Wind factor for fire arriving from each neighbour (Alexandridis eq. 3)
def wind_factors(wind_from, speed):
    wind_to = wind_from + 180
    theta = np.radians(SPREAD_BEARINGS - wind_to)

    return np.exp(speed * (C1 + C2 * (np.cos(theta) - 1)))


# Function to apply the transition rules and return the new grid
def transition_function(grid, neighbourstates, neighbourcounts, terrain,
                        burn_time, burn_steps, wind, water, step):
    step[0] += 1

    # Soak everything in the drop area that has not burnt out yet
    if step[0] == DROP_STEP:
        soaked = water & np.isin(grid, [CHAPARRAL, FOREST, CANYON, TOWN,
                                        BURNING, FIRE_FRONT])
        grid[soaked] = WET

    # Once dry, soaked cells go back to their original fuel
    if step[0] == DRY_STEP:
        dry = grid == WET
        grid[dry] = terrain[dry]
        burn_time[dry] = 0

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
    burnt_out = burning & (burn_time >= burn_steps)

    grid[front] = BURNING
    grid[burnt_out] = BURNT_STATES[terrain[burnt_out]]
    grid[catches_fire] = FIRE_FRONT

    return grid




# Main function that sets up, runs and saves CA
def main():
    # The drop plan sets when the water lands, which the transition reads
    global DROP_STEP, DRY_STEP

    # Get the config object from set up
    config = setup(sys.argv[1:])

    # Original terrain map, so burning cells still know what fuel they had
    terrain = build_terrain()

    # Number of steps each cell has been burning for, kept between steps
    burn_time = np.zeros((GRID_SIZE, GRID_SIZE))

    # How many steps each cell will burn for, picked once per run
    burn_steps = random_burn_steps(terrain)

    # Wind factor per neighbour direction, fixed for the whole run
    wind = wind_factors(WIND_FROM, WIND_SPEED)

    # Cells covered by the water drop chosen in DROP_PLAN, and when it lands
    cells, drop_hours = DROP_PLANS[DROP_PLAN]
    water = np.zeros((GRID_SIZE, GRID_SIZE), dtype=bool)
    if cells is None:
        fill_rect(water, True, *DROP_AREA)
    else:
        rows, cols = zip(*cells)
        water[list(rows), list(cols)] = True
    DROP_STEP = int(drop_hours * 60 / STEP_MINUTES)
    DRY_STEP = DROP_STEP + int(WET_HOURS * 60 / STEP_MINUTES)

    # Steps run so far, in an array so the transition function can update it
    step = np.zeros(1)

    grid = Grid2D(config, (transition_function, terrain, burn_time,
                           burn_steps, wind, water, step))

    # Run the CA, save grid state every generation to timeline
    timeline = grid.run()

    # Save updated config to file
    config.save()
    
    # Save timeline to file
    utils.save(timeline, config.timeline_path)

if __name__ == "__main__":
    main()
