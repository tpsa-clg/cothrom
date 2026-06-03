# Set-Up

## Dependencies

````
sudo apt install python3-venv
````

## Virtual Python Environment

````
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
````

# Instructions

## Grabbing Public Data

````
make ED_data.csv    # python code/combine_data.py
````

`combine_data.py` - combines CSO population, Tailte Éireann geographical, and Electoral (Amendment) Act 2023 constituency data into `ED_data.csv` file for `txt_files_for_MCMC.py` - downloads population data `F1060*.csv` from https://data.cso.ie/table/F1060 and geographical datasets `"CSO*{100m, 50m, 20m, ungeneralised}*.geojson"` from https://data.gov.ie/dataset/cso-electoral-divisions-national-statistical-boundaries-2022-{generalised-100m, generalised-50m, generalised-20m, ungeneralised}1 if not in data directory - only needs to be executed once and can delete CSO file after `ED_data.csv` created - constituency shapes and populations checked against EC report (difference of 2 between Limerick City & County, 20 between Kildare North & South, 1187 between Dublin South-Central & West, 370 between Cork South-Central + North-West & North-Central) - also gets county geographical data for configuration plotting

## Setting Up MCMCSA Runs

````
python code/txt_for_MCMC.py <area_type> <area_list> <area_name>
````

`txt_files_for_MCMC.py` - creates `.txt` files with GUID, population, and neighbours for each ED in specified area for `MCMC_SA.cpp` - makes `actual.csv` file for the area's current configuration - command line input takes area definition as input, e.g.
````
python code/txt_for_MCMC.py County LONGFORD,WESTMEATH,OFFALY,LAOIS "Midland counties"
python code/txt_for_MCMC.py "Administrative Region" LIMERICK,"LIMERICK CITY" Limerick
python code/txt_for_MCMC.py Constituency "CORK EAST","CORK NORTH-CENTRAL","CORK NORTH-WEST","CORK SOUTH-CENTRAL","CORK SOUTH-WEST" Cork
````

## Running MCMCSA Algortihm

````
OMP_SET_NUM_THREADS=<num_threads>
make MCMC_SA
./MCMC_SA <area_name> <seat_makeup> <coupling_constants> <measured_discarded_sweeps>
````

`MCMC_SA.cpp` - uses Metropolis/heatbath algorithm to approximate optimal configuration for given area and coupling constants via simulated annealing - saves results in a `.csv` file with unique ID (from timestamp) - executable takes area name, number of seats per constituency, (non-population) coupling constants, and number of measured/discarded iterations per temperature as command line input assuming files for population and neighbours exist in the current directory, e.g.
````
./MCMC_SA "Midland counties" 2,3,3,3 2,1,3 5000,100
./MCMC_SA Limerick 3,4 0,0,0 1000,0
./MCMC_SA Cork 3,3,4,5,5 4,0.72,0 10000,1000
````

## Visualising Runs & Configurations

````
make actual_H
./actual_H <area_name>
python code/plot_stats.py <area_name> <config_ID>
python code/plot_config.py <area_name> <config_ID>
````

`actual_H.cpp` - gets the Hamiltonians for a given area's current configuration

`plot_stats.py` - plots statistical physics observables (Hamiltonians, specific heat capacities, autocorrelations, acceptance rates) from `MCMC_SA.cpp` output with config ID, e.g.
````
python code/plot_stats.py "Midland counties" 3133663620
````

`plot_config.py` - plots initial and optimal configurations from `.csv` file with config ID (including `actual.csv`), e.g.
````
python code/plot_config.py "Midland counties" 3133663620
python code/plot_config.py Cork actual
````

## Pareto Analysis

````
bash code/Pareto.sh
python code/plot_Pareto.py <area_name> <seats> <constituencies>
````

`Pareto.sh` - submits Slurm jobs for running `MCMC_SA.cpp` in parallel for combinations of seat configurations and couplings - assumes a fixed contiguity coupling proportion - must be run from parent directory

`plot_Pareto.py` - plots Pareto front for a given area and seat configuration - takes area, number of seats, and number of constituencies as inputs, e.g.
````
python code/plot_Pareto.py "Midland counties" 11 3
python code/plot_Pareto.py Cork 20 5
````

# TODO
- contiguity term extremely inefficient
    - look into Euler characteristic stuff
    - check for zero/one neighbour before removing + re-connecting - negligible cost, possible speedup
- county boundary term needs improvement
    - look at Eliza's stuff in appendix about area ratios
- no testing of alternative compactness terms e.g. something with area and perimeter, convex hull, etc. rather than number of neighbours ([#5](https://github.com/campioru/Electoral_Redistricting/issues/5))
- test sets vs vectors for Map::connect_, optimal_configs
- no temporal continuity term
- remove redundant Hamiltonian calculations for certain maps
    - don't consider county boundaries for areas within counties or EU redistricting
    - could check if coupling constant is zero
    - above could also apply to other Hamiltonians, particularly temporal continuity when implemented (we usually always care about compactness and contiguity)
- test alternative parallelisation e.g. keep threads open and use single/master thread when needed rather than closing and re-launching threads
- extend to useful proofs of concept e.g. European MP constituencies, council LEAs
    - append LEA data stuff to `combine_data.py`
    - EU MP constituencies can theoretically have border violations but have always comprised whole counties
- consider something like `pyerrors` for observable and error tracking to do stats in Python instead of C++
    - would need to store measurements for each config (approx. 30MB for each Hamiltonian + acceptance rate at 10,000 iterations and 151 temperatures) but can do all stats in Python instead of C++
    - this would also avoid manual autocorrelation in C++
