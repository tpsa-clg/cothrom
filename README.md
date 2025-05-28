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
- update `.geojson` and `.csv` files and corresponding code in `readfile_findneighbours.py` (currently using preliminary 2022 population data and 2019 ED boundaries), check if output of `readfile_findneighbours.py` is the same when using generalised vs non-generalised `.geojson`s
  - 2022 population `.csv` and geographical `.geojson`s might work - both have 3420 CSO EDs ("amalgated to ensure statistical confidentiality or where a change was required to ensure better CSO ED/LEA alignment") with seemingly matching GUIDs and amalgated EDs
  - 2024 geographical `.geojson` has 3445 EDs (seemingly the new correct amount?) and 2019 geographical `.geojson`s have 3440 EDs (seemingly the previous correct amount?) but too awkward to combine with any population data
- try useful small redistricting instead of proofs-of-concept e.g. Dublin constituency, Cork constituency, European MP map, some local election maps (note that these all conveniently have no county borders involved so can work on this without extra Hamiltonian terms. EU MP constituencies can theoretically have border violations but have always comprised whole counties)
- split `MCMC_SA.cpp` into multiple files e.g. `.h` for classes and functions, class inheritance for different map types e.g. single-seat ED groupings (original proof-of-concept), multiple-seat ED groupings (Dublin/Cork, full-scale Ireland, LEAs), multiple-seat county groupings (EU Parliament constituencies)
- set up a Makefile to track C++ executables (after above step)
- consider something like `pyerrors` for observable and error tracking - would need to store measurements for each config (approx. 30MB for each Hamiltonian + acceptance rate at 10,000 iterations and 151 temperatures) but can do all stats in Python instead of C++

`readfile_findneighbours.py` - reads `.csv` and `.geojson` files and saves population, geography, and ED ID to text files

`MCMC_SA.cpp` - uses Metropolis/heatbath algorithm to approximate optimal configuration for given constituency (or general area) and coupling constants via simulated annealing, takes constituency/area name and number of seats as command line input

`plot.py` - plots statistical physics observables (Hamiltonians, specific heat capacities, acceptance rates)

also required (but not tracked because of storage concerns): `FP009.csv` and `Electoral_Divisions_-_National_Statutory_Boundaries_-_2019_-_Generalised_20m.geojson`