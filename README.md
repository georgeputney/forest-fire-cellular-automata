# Forest fire cellular automaton

A probabilistic cellular automaton of a forest fire spreading towards a town, built on the CAPyLE simulator for the COM3524 group project (Team 17).

The map is a 100 x 100 grid of 500 m cells, each step is 10 minutes, and a run lasts 1,000 steps (about 7 days).
Fire spreads to the 8 neighbouring cells with the ignition rule and wind constants from Alexandridis et al. (2008).

## Setup

The code needs Python 3.7 with numpy, matplotlib, and tkinter.
The conda environment file installs all of them:

```
conda env create -f environment.yml
conda activate COM3524
```

## Running the model

From this folder, run:

```
python main.py
```

On macOS or Linux `./run.sh` does the same, and on Windows `run.bat`.

The GUI opens with the forest fire model already loaded.
Click "Apply configuration & run CA" at the bottom left, then use Play or drag the slider under the map to watch the fire spread.

## Changing the scenario

The Scenario menus beside the configuration panel set where the fire starts, the wind, the water drop, extra forest, and a firebreak round the town.
Changing a menu does not change the map on its own: click "Apply configuration & run CA" again to run the new scenario.

The same settings are at the top of `ca_descriptions/forest_fire.py`, under "Run settings", as the defaults the menus start on.
Editing them there also allows values the menus do not offer, such as any wind bearing or forest rectangle.
After editing the file, reload the model with File > Open and choose `forest_fire.py`.

| Setting | What it does | Options |
|---|---|---|
| `IGNITION` | Where the fire starts | `POWER_PLANT` or `INCINERATOR` |
| `WIND_FROM` | Compass bearing the wind blows from | 0 (north), 45, 90, and so on |
| `WIND_SPEED` | Wind speed in m/s | 8 by default |
| `DROP_PLAN` | Which water drop lands, and when | `None`, `'strip'`, `'town_ring'`, `'fire_block'`, `'box_6km'`, or `'box_12km'` |
| `EXTRA_FOREST` | Extra dense forest, as (left, right, bottom, top) in km | `None`, or `(0, 50, 35, 45)` for the forest wall |
| `TOWN_FIREBREAK` | Cleared ground around the town, as (sides, width km, gap km) | `None`, or `('ring', 0.5, 0)` for the ring |

## Reproducing the results

Each run is random, so a single run will differ a little from these figures.
The figures in the presentation are medians over 20 runs with the same 20 random seeds.

| Result | Settings | Median over 20 runs |
|---|---|---|
| Results I, power plant | `IGNITION = POWER_PLANT` | Reaches the town at 15.2 h |
| Results I, incinerator | `IGNITION = INCINERATOR` | Reaches the town at 14.9 h |
| Results II, wind direction | `WIND_FROM` = 0, 45, 90, 135, 180, 225, 270, or 315 | 14 to 16 h from N, NE, or E; never from S, SW, or W |
| Results III, soak the fire | `DROP_PLAN = 'fire_block'` (lands at 0.5 h) | Fire out in every run |
| Results III, box it in | `DROP_PLAN = 'box_12km'` (lands at 3 h) | 13.7 h later than with no water |
| Results III, ring the town | `DROP_PLAN = 'town_ring'` (lands at 10 h) | 10.4 h later than with no water |
| Results III, forest wall | `EXTRA_FOREST = (0, 50, 35, 45)` | No delay |
| Results III, firebreak ring | `TOWN_FIREBREAK = ('ring', 0.5, 0)` | Fire kept out in every run |
| Results IV, sensitivity | `STEP_MINUTES`, `WIND_SPEED`, `RESIDUAL_SPREAD`, or the burn hours, under "Model parameters" | See Appendix E |

## Files

- `ca_descriptions/forest_fire.py` is the model: its settings, map, and transition rules.
- `main.py` starts the CAPyLE GUI with the model loaded.
- `capyle/` is the CAPyLE simulator, with small changes so it opens the model on start up, shows the Scenario menus (`capyle/guicomponents/scenarioui.py`), names each colour, hides the grid size and neighbourhood controls the model cannot use, and fits its run button on a laptop screen.

## Acknowledgements

Built on [CAPyLE](https://github.com/pjworsley/capyle) by Peter Worsley, a cellular automaton teaching tool made at the University of Sheffield.
CAPyLE is licensed under a BSD licence, the terms of which are in the LICENCE file.
