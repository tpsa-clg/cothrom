Current state of affairs
- plotting Python script `plot.py` unfinished: need to plot energies/variances/acceptance rates
- can only split into single-seat groupings
- contiguity term extremely inefficient (breadth-first search instead of potential martrix multiplication?)
- no county border term
- nothing for Pareto front

`readfile_findneighbours.py` - reads .csv and .geojson files and saves population, geography, and ED ID to text files

`MCMC_SA.cpp` - uses Metropolis/heatbath algorithm to approximate optimal configuration for given constituency (or general area) and coupling constants via simulated annealing

`plot.py` - plots statistical physics observables (Hamiltonians, specific heat capacities, acceptance rates)