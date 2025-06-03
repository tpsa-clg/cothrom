Current state of affairs
- `txt_for_MCMC.py` unfinished: take area as input, output everything for `MCMC_SA.cpp`
- `plot.py` unfinished: need to plot energies/variances/acceptance rates
- check if neighbour output of `txt_for_MCMC.py` are the same when using generalised vs non-generalised `.geojson`s
- population term only allows for single-seat groupings
- contiguity term extremely inefficient (breadth-first search instead of potential matrix multiplication?)
- no testing of alternative compactness terms e.g. something with area and perimeter rather than number of neighbours
- no county border or temporal continuity terms
- nothing for Pareto front
- test alternative parallelisation e.g. keep threads open and use single/master thread when needed rather than closing and re-launching threads
- consider stopping annealing when new states stop being accepted, instead of continuing for entire temperature range
- try useful small redistricting instead of proofs-of-concept e.g. Dublin constituency, Cork constituency, European MP map, some local election maps (note that these all conveniently have no county borders involved so can work on this without county border Hamiltonian. EU MP constituencies can theoretically have border violations but have always comprised whole counties)
- split `MCMC_SA.cpp` into multiple files e.g. `.h` for classes and functions, class inheritance for different map types e.g. single-seat ED groupings (original proof-of-concept), multiple-seat ED groupings (Dublin/Cork, full-scale Ireland, LEAs), multiple-seat county groupings (EU Parliament constituencies)
- set up a Makefile to track C++ executables (after above step)
- consider something like `pyerrors` for observable and error tracking - would need to store measurements for each config (approx. 30MB for each Hamiltonian + acceptance rate at 10,000 iterations and 151 temperatures) but can do all stats in Python instead of C++

`make_csv_from_data.py` - combines CSO population, Tailte Éireann geographical, and Electoral (Amendment) Act 2023 constituency data into `.csv` file for `txt_files_for_MCMC.py` (assumes population data `F1060*.csv` from https://data.cso.ie/table/F1060 and geographical data `"CSO_ELECTORAL_DIVISIONS_2022_Genralised_100m_view_726581695825557405.geojson"` from https://data.gov.ie/dataset/cso-electoral-divisions-national-statistical-boundaries-2022-generalised-100m1 are in current directory) - only needs to be executed once - constituency shapes and populations checked against EC report (difference of 2 between Limerick City & County, 20 between Kildare North & South, 1187 between Dublin South-Central & West, 370 between Cork South-Central + North-West & North-Central)

`txt_files_for_MCMC.py` - creates `.txt` files with population and neighbours for each ED in specified area for `MCMC_SA.cpp`

`MCMC_SA.cpp` - uses Metropolis/heatbath algorithm to approximate optimal configuration for given area and coupling constants via simulated annealing, takes area name and number of seats as command line input

`plot.py` - plots statistical physics observables (Hamiltonians, specific heat capacities, acceptance rates) from `MCMC_SA.cpp` output