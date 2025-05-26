Current state of affairs
- plotting Python script `plot.py` unfinished: need to plot energies/variances/acceptance rates
- population term only allows for single-seat groupings
- contiguity term extremely inefficient (breadth-first search instead of potential matrix multiplication?)
- no testing of alternative compactness terms e.g. something with area and perimeter rather than number of neighbours
- no county border term
- nothing for Pareto front
- test alternative parallelisation e.g. keep threads open and use single/master thread when desired rather than closing and re-launching threads
- need to change `readfile_findneighbours.py` so that it takes desired area(s) (constituency, county, province, list of EDs) as input and outputs necessary files
- consider stopping annealing when new states stop being accepted, instead of continuing for entire temperature range
- potentially update `.geojson` and `.csv` files with newer data? still using same files from 2023 hackathon
- try useful small redistricting instead of proofs-of-concept e.g. Dublin constituency, Cork constituency, European MP map, some local election maps (note that these all conveniently have no county borders involved so can work on this without extra Hamiltonian terms. EU MP constituencies can theoretically have border violations but have always comprised whole counties)
- split `MCMC_SA.cpp` into multiple files e.g. `.h` for classes and functions, class inheritance for different map types e.g. single-seat ED groupings (original proof-of-concept), multiple-seat ED groupings (Dublin/Cork, full-scale Ireland, LEAs), single-seat county groupings (EU Parliament constituencies)
- consider something like `pyerrors` for observable and error tracking - would need to store measurements for each config (approx. 30MB for each Hamiltonian + acceptance rate at 10,000 iterations and 151 temperatures) but can do all stats in Python instead of C++
- set up a Makefile to track C++ executables (after above step)

`readfile_findneighbours.py` - reads .csv and .geojson files and saves population, geography, and ED ID to text files

`MCMC_SA.cpp` - uses Metropolis/heatbath algorithm to approximate optimal configuration for given constituency (or general area) and coupling constants via simulated annealing, takes constituency/area name and number of seats as command line input

`plot.py` - plots statistical physics observables (Hamiltonians, specific heat capacities, acceptance rates)

`Electoral_Divisions_-_National_Statutory_Boundaries_-_2019_-_Generalised_20m.geojson` - geographical data of EDs

`FP009.csv` - population of EDs