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

from capyle.ca import Grid2D
import capyle.utils as utils

import numpy as np


# Run settings. These are the defaults: the Scenario menus in the GUI change
# them for a run, or edit them here and reopen this file (File > Open)

# Ignition sites from the brief, as (row, column) with row 0 at the north edge
POWER_PLANT = (0, 0)
INCINERATOR = (0, 99)
IGNITION = INCINERATOR      # where the fire starts: POWER_PLANT or INCINERATOR
WIND_FROM = 0               # compass bearing the wind blows from, 0 = north
WIND_SPEED = 8              # m/s
DROP_PLAN = None            # a name from DROP_PLANS below, or None for no water
EXTRA_FOREST = None         # (left, right, bottom, top) in km, or None. The
                            # forest wall is (0, 50, 35, 45)
TOWN_FIREBREAK = None       # (sides, width km, gap km), or None. sides is
                            # 'north', 'u' (north, east and west) or 'ring'.
                            # The ring around the town is ('ring', 0.5, 0)

# Choices the GUI offers for each run setting, as (setting, menu label,
# [(choice shown, value)])
GUI_CHOICES = [
    ('IGNITION', 'Fire starts at',
     [('Incinerator', INCINERATOR), ('Power plant', POWER_PLANT)]),
    ('WIND_FROM', 'Wind from',
     list(zip(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'],
              range(0, 360, 45)))),
    ('WIND_SPEED', 'Wind speed',
     [('%d m/s' % speed, speed) for speed in range(0, 14, 2)]),
    ('DROP_PLAN', 'Water drop',
     [('None', None),
      ('Soak the fire at 0.5 h', 'fire_block'),
      ('Box it in 6 km out at 1 h', 'box_6km'),
      ('Box it in 12 km out at 3 h', 'box_12km'),
      ('Ring round the town at 10 h', 'town_ring'),
      ('Strip north of the town at 10 h', 'strip')]),
    ('EXTRA_FOREST', 'Extra forest',
     [('None', None), ('Forest wall, 10 km thick', (0, 50, 35, 45))]),
    ('TOWN_FIREBREAK', 'Firebreak round the town',
     [('None', None),
      ('North side, 0.5 km wide', ('north', 0.5, 0)),
      ('Three sides, 0.5 km wide', ('u', 0.5, 0)),
      ('Ring, 0.5 km wide', ('ring', 0.5, 0)),
      ('Ring, 1 km wide', ('ring', 1, 0))]),
]


# Cell states. The first five are the terrain types, in the order the
# per-terrain arrays below use
CHAPARRAL, FOREST, CANYON, LAKE, TOWN = range(5)
BURNING = 5
BURNT_CHAPARRAL, BURNT_FOREST, BURNT_CANYON, BURNT_TOWN = range(6, 10)
FIRE_FRONT = 10     # caught fire last step, spreads at full strength
WET = 11            # soaked by a water drop, cannot burn until it dries
FIREBREAK = 12      # cleared ground with no fuel, never burns

# State each terrain becomes once burnt out (lakes never burn)
BURNT_STATES = np.array([BURNT_CHAPARRAL, BURNT_FOREST, BURNT_CANYON,
                         LAKE, BURNT_TOWN])


# Map
CELL_KM = 0.5
GRID_SIZE = 100
# Town edges in km as (left, right, bottom, top)
TOWN_AREA = (18.75, 21.25, 3.75, 6.25)
# The fire starts on a 2 x 2 block of cells (1 km2) at the site, so it cannot
# die out on the first step by bad luck
IGNITION_CELLS = 2


# Model parameters

# Real minutes per step. Fire moves at most one cell per step, so 500 m
# every 10 minutes gives a top speed of 3 km/h, about 10% of an 8 m/s wind
# (Cruz and Alexander 2019)
STEP_MINUTES = 10

# Base chance a burning neighbour spreads fire, with no wind or slope
# (Alexandridis et al. 2008, Table 4)
P_H = 0.58
# How strongly cells burning behind the front still spread fire, as a
# fraction of the front's chance (our own choice, tested in Results IV)
RESIDUAL_SPREAD = 0.001
# Ignition adjustment per terrain, our own values ordered by the brief
VEG_FACTOR = np.array([0, -0.4, 0.4, 0, 0])

# Shortest and longest hours each terrain burns, from the team's ranges
# (canyon 1 to 6 hours, chaparral 2 to 5 days, forest 2 to 4 weeks).
# Town uses the chaparral range
BURN_HOURS_MIN = np.array([48, 336, 1, 0, 48])
BURN_HOURS_MAX = np.array([120, 672, 6, 0, 120])

# Wind constants (Alexandridis et al. 2008, Table 4)
C1 = 0.045
C2 = 0.131
# Bearing fire travels when it spreads from each neighbour into the cell,
# in CAPyLE's neighbour order [NW, N, NE, W, E, SW, S, SE]
SPREAD_BEARINGS = np.array([135, 180, 225, 90, 270, 45, 0, 315])


# Water drops, each enough water for about 12.5 km2 (50 cells)

# Hours a soaked cell stays wet before it dries back to its own fuel
WET_HOURS = 12
# Each drop is a list of rectangles in km as (left, right, bottom, top).
# A 12.5 km x 1 km strip along the town's north edge, the best of 1,020
# positions tried. It lands at 10 h so it is still wet when the fire arrives
# at about 15 h
DROP_HOURS = 10
DROP_AREA = (12.5, 25, 5, 6)
# A ring 0.5 km wide touching the town on every side, only 24 cells
TOWN_RING = [(18.25, 21.75, 6.25, 6.75), (18.25, 21.75, 3.25, 3.75),
             (18.25, 18.75, 3.75, 6.25), (21.25, 21.75, 3.75, 6.25)]
# A 3.5 km square over the incinerator, where the fire starts, 49 cells
FIRE_BLOCK = [(46.5, 50, 46.5, 50)]
# L shapes boxing the fire into its corner, 6 km out (25 cells) and 12 km
# out (49 cells), each a line south of the fire and a line west of it
BOX_6KM = [(43.5, 50, 43.5, 44), (43.5, 44, 44, 50)]
BOX_12KM = [(37.5, 50, 37.5, 38), (37.5, 38, 38, 50)]

# Each drop plan as its rectangles and the hours after ignition it lands.
# Drops near the incinerator only work if they land before the fire passes
# them, so each lands at the latest whole or half hour that still works
DROP_PLANS = {'strip': ([DROP_AREA], DROP_HOURS),
              'town_ring': (TOWN_RING, DROP_HOURS),
              'fire_block': (FIRE_BLOCK, 0.5),
              'box_6km': (BOX_6KM, 1),
              'box_12km': (BOX_12KM, 3)}


def to_cells(km):
    # Adding 0.5 rounds halves up, so the 2.5 km town stays 5 cells wide
    return int(km / CELL_KM + 0.5)


# Fills a rectangle given in km, with y measured from the south edge
def fill_rect(grid, state, left, right, bottom, top):
    grid[to_cells(50 - top):to_cells(50 - bottom),
         to_cells(left):to_cells(right)] = state


# True/False grid of the cells inside any of the given rectangles in km
def cells_in(*rects):
    mask = np.zeros((GRID_SIZE, GRID_SIZE), dtype=bool)
    for rect in rects:
        fill_rect(mask, True, *rect)
    return mask


# The map from the brief, with any extra forest or firebreak from the run
# settings added
def build_terrain():
    grid = np.full((GRID_SIZE, GRID_SIZE), CHAPARRAL)

    fill_rect(grid, FOREST, 0, 25, 42.5, 45)
    fill_rect(grid, FOREST, 5, 12.5, 20, 42.5)
    fill_rect(grid, FOREST, 5, 25, 15, 20)
    fill_rect(grid, FOREST, 32.5, 45, 35, 40)
    fill_rect(grid, LAKE, 17.5, 22.5, 27.5, 37.5)
    fill_rect(grid, LAKE, 37.5, 40, 10, 22.5)
    fill_rect(grid, CANYON, 25, 45, 25, 27.5)
    fill_rect(grid, TOWN, *TOWN_AREA)

    # Extra forest only replaces chaparral and canyon
    if EXTRA_FOREST is not None:
        planted = cells_in(EXTRA_FOREST)
        grid[planted & np.isin(grid, [CHAPARRAL, CANYON])] = FOREST

    if TOWN_FIREBREAK is not None:
        cleared = firebreak_cells(*TOWN_FIREBREAK)
        grid[cleared & np.isin(grid, [CHAPARRAL, FOREST, CANYON])] = FIREBREAK

    return grid


# Cells cleared for a firebreak around the town, as a True/False grid. gap is
# the distance in km between the town's edge and the firebreak
def firebreak_cells(sides, width, gap):
    left, right, bottom, top = TOWN_AREA

    inner = cells_in((left - gap, right + gap, bottom - gap, top + gap))

    outer = cells_in((left - gap - width, right + gap + width,
                      bottom - gap - width, top + gap + width))
    cleared = outer & ~inner

    # Leave out the sides that are not cleared
    if sides != 'ring':
        cleared &= ~cells_in((0, 50, 0, bottom - gap))

    if sides == 'north':
        cleared &= ~cells_in((0, 50, bottom - gap, top + gap))

    return cleared


# Terrain the rules use for each cell. Firebreaks hold no fuel, so they
# behave like lakes
def fuel_of(terrain):
    return np.where(terrain == FIREBREAK, LAKE, terrain)


# Block of cells the fire starts on, kept inside the map at corner sites
def ignition_block(site):
    row = min(site[0], GRID_SIZE - IGNITION_CELLS)
    col = min(site[1], GRID_SIZE - IGNITION_CELLS)

    return (slice(row, row + IGNITION_CELLS),
            slice(col, col + IGNITION_CELLS))


# Steps on which a drop lands and dries
def drop_steps(drop_hours, wet_hours):
    land = int(drop_hours * 60 / STEP_MINUTES)
    return np.array([land, land + int(wet_hours * 60 / STEP_MINUTES)])


# Cells a drop plan soaks, and the steps it lands and dries on. With no plan
# nothing is soaked and the drop step is never reached
def drop_plan(name):
    if name is None:
        return cells_in(), np.array([-1, -1])

    rects, drop_hours = DROP_PLANS[name]

    return cells_in(*rects), drop_steps(drop_hours, WET_HOURS)


# Set up the config object used to interact with the GUI
def setup(args):
    config_path = args[0]
    config = utils.load(config_path)

    # The GUI shows a menu for each run setting and saves the choices made
    # there in the config. They replace the run settings for this run
    config.choice_menus = GUI_CHOICES
    if getattr(config, 'choices', None) is None:
        config.choices = {setting: globals()[setting]
                          for setting, _, _ in GUI_CHOICES}
    globals().update(config.choices)

    # -- THE CA MUST BE RELOADED IN THE GUI IF ANY OF THE BELOW ARE CHANGED --

    config.title = "Forest fire"
    config.dimensions = 2
    config.states = (CHAPARRAL, FOREST, CANYON, LAKE, TOWN, BURNING,
                     BURNT_CHAPARRAL, BURNT_FOREST, BURNT_CANYON, BURNT_TOWN,
                     FIRE_FRONT, WET, FIREBREAK)

    # Names the GUI shows beside each colour, in the order of config.states
    config.state_names = ('Chaparral', 'Dense forest', 'Canyon', 'Lake',
                          'Town', 'Burning', 'Burnt chaparral',
                          'Burnt forest', 'Burnt canyon', 'Burnt town',
                          'Fire front', 'Water drop', 'Firebreak')

    # Burnt states are greys so they stand apart from the greens of fuel
    config.state_colors = [(0.75, 0.75, 0), (0.3, 0.35, 0.15), (1, 1, 0.2),
                           (0.2, 0.6, 1), (0, 0, 0), (1, 0.2, 0),
                           (0.5, 0.5, 0.5), (0.35, 0.35, 0.35),
                           (0.65, 0.65, 0.65), (0.25, 0.25, 0.25), (1, 0.65, 0),
                           (0.6, 0.85, 1), (0.85, 0.75, 0.6)]

    config.grid_dims = (GRID_SIZE, GRID_SIZE)
    config.num_generations = 1000
    config.wrap = False
    # The map is drawn for this grid size and the wind rules need all 8
    # neighbours, so the GUI hides its grid size, neighbourhood, and initial
    # grid controls
    config.fixed_map = True

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


# The forest fire rules, applied to every cell at once each step
def transition_function(grid, neighbourstates, neighbourcounts, terrain,
                        burn_time, burn_steps, wind, water, drop, step):
    step[0] += 1

    # Soak everything in the drop area that has not burnt out yet
    if step[0] == drop[0]:
        soaked = water & np.isin(grid, [CHAPARRAL, FOREST, CANYON, TOWN,
                                        BURNING, FIRE_FRONT])
        grid[soaked] = WET

    # Once dry, soaked cells go back to their original fuel
    if step[0] == drop[1]:
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

    burn_time[burning] += 1
    burnt_out = burning & (burn_time >= burn_steps)

    grid[front] = BURNING
    grid[burnt_out] = BURNT_STATES[terrain[burnt_out]]
    grid[catches_fire] = FIRE_FRONT

    return grid


# Runs the CA for the GUI and saves every step for playback
def main():
    config = setup(sys.argv[1:])

    # Original terrain map, so burning cells still know what fuel they had
    terrain = fuel_of(build_terrain())

    # Number of steps each cell has been burning for, kept between steps
    burn_time = np.zeros((GRID_SIZE, GRID_SIZE))

    # How many steps each cell will burn for, picked once per run
    burn_steps = random_burn_steps(terrain)

    # Wind factor per neighbour direction, fixed for the whole run
    wind = wind_factors(WIND_FROM, WIND_SPEED)

    # Cells the chosen water drop soaks, and the steps it lands and dries on
    water, drop = drop_plan(DROP_PLAN)

    # Steps run so far, in an array so the transition function can update it
    step = np.zeros(1)

    grid = Grid2D(config, (transition_function, terrain, burn_time,
                           burn_steps, wind, water, drop, step))

    timeline = grid.run()
    config.save()
    utils.save(timeline, config.timeline_path)


if __name__ == "__main__":
    main()
