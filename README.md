Current state of affairs
- `plot.py` unfinished: need to plot energies/variances/acceptance rates vs temperature, initial + final maps, bar charts etc. of each grouping's Hamiltonian contribution (i.e. population, compactness)
- make histograms in `txt_for_MCMC.py` e.g. population, neighbours, area, perimeter and compare to national histograms
- population term only allows for single-seat groupings (i.e. proof of concept)
- contiguity term extremely inefficient (breadth-first search instead of potential matrix multiplication?)
- no testing of alternative compactness terms e.g. something with area and perimeter, convex hull, etc. rather than number of neighbours
- no county border or temporal continuity terms
- nothing for Pareto front
- test alternative parallelisation e.g. keep threads open and use single/master thread when needed rather than closing and re-launching threads
- consider stopping annealing when new states stop being accepted, instead of continuing for entire temperature range
- try useful small redistricting instead of proofs-of-concept e.g. Dublin constituency, Cork constituency, European MP map, some local election maps (note that these all conveniently have no county borders involved so can work on this without county border Hamiltonian. EU MP constituencies can theoretically have border violations but have always comprised whole counties)
- split `MCMC_SA.cpp` into multiple files e.g. `.h` for classes and functions, class inheritance for different map types e.g. single-seat ED groupings (original proof-of-concept), multiple-seat ED groupings (Dublin/Cork, full-scale Ireland, LEAs), multiple-seat county groupings (EU Parliament constituencies) - update Makefile accordingly (object files)
- consider something like `pyerrors` for observable and error tracking - would need to store measurements for each config (approx. 30MB for each Hamiltonian + acceptance rate at 10,000 iterations and 151 temperatures) but can do all stats in Python instead of C++

`combine_data.py` - combines CSO population, Tailte Éireann geographical, and Electoral (Amendment) Act 2023 constituency data into `ED_data.csv` file for `txt_files_for_MCMC.py` - downloads population data `F1060*.csv` from https://data.cso.ie/table/F1060 and geographical datasets `"CSO*{100m, 50m, 20m, ungeneralised}*.geojson"` from https://data.gov.ie/dataset/cso-electoral-divisions-national-statistical-boundaries-2022-{generalised-100m, generalised-50m, generalised-20m, ungeneralised}1 if not in current directory - only needs to be executed once and can delete CSO & Tailte Éireann files after `ED_data.csv` created - constituency shapes and populations checked against EC report (difference of 2 between Limerick City & County, 20 between Kildare North & South, 1187 between Dublin South-Central & West, 370 between Cork South-Central + North-West & North-Central)

`txt_files_for_MCMC.py` - creates `.txt` files with GUID, population, and neighbours for each ED in specified area for `MCMC_SA.cpp` - command line input takes the form `area_type area_list area_name`, e.g.
````
python3 txt_for_MCMC.py County LONGFORD,WESTMEATH,OFFALY,LAOIS "Midland counties"
python3 txt_for_MCMC.py Constituency "CORK NORTH-CENTRAL","CORK NORTH-WEST","CORK SOUTH-CENTRAL","CORK SOUTH-WEST" Cork
````

`MCMC_SA.cpp` - uses Metropolis/heatbath algorithm to approximate optimal configuration for given area and coupling constants via simulated annealing, executable takes area name and number of seats as command line input assuming files for population and neighbours exist in the current directory, e.g.
````
./MCMC_SA "Midland counties" 11
./MCMC_SA Cork 20
````

`plot.py` - plots statistical physics observables (Hamiltonians, specific heat capacities, acceptance rates) from `MCMC_SA.cpp` output