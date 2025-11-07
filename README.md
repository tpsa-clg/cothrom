Current state of affairs
- modify data saving (`MCMC_SA.cpp`) & plotting (`plot.py`) to allow for multiple sets of parameters
    - parallelise `MCMC_SA.cpp` over parameter sets instead of calculations within MCMC updates?
    - plot some Pareto fronts/phase diagrams in `plot.py` from multiple sets of results of the C++ code
- extend `plot.py` code
    - plot autocorrelation times
    - plot specific heat capacities
        - this needs proper errorbar considerations, probably by thinning data in the C++ code until it's independent and then calculating standard error of the variance (needs a lot of samples for high autocorrelation)
- contiguity term extremely inefficient (breadth-first search instead of potential matrix multiplication?)
- no testing of alternative compactness terms e.g. something with area and perimeter, convex hull, etc. rather than number of neighbours
- crazy idea: consider combining contiguity and compactness into one shape term (since they are quite strongly correlated anyway, i.e. reducing one generally reduces the other)
    - could be sort of piecewise i.e. H_C + max(H_D) when not contiguous, H_D when contiguous
    - would still need to check contiguity at each step but could skip a lot of compactness calculations in high-temperature phase
    - still need to give this some thought as this could result in poor compactness performance, since the algorithm would only start caring about compactness past the critical point
    - could always go back to the original idea of only suggesting changes that don't split constituencies, but would be pretty difficult to properly implement
- no county border term
    - could be tricky when considering maps without county border violations e.g. EU, LEA, Dublin, Cork
    - could check if no. of sites = no. of counties, or if all sites in same county
    - or could do something similar to population with a subclass for no county border term
    - or just set the coupling constant to be 0 and have some redundant calculations
- no temporal continuity term
- test alternative parallelisation e.g. keep threads open and use single/master thread when needed rather than closing and re-launching threads
- try useful small redistricting instead of proofs-of-concept e.g. Dublin constituencies, Cork constituencies, European MP constituencies, various council LEAs
    - note that these all conveniently have no county borders involved so can work on this without county border Hamiltonian
    - EU MP constituencies can theoretically have border violations but have always comprised whole counties
- duplicate `combine_data.py` for LEAs/counties/cities & counties/constituencies
    - could do more proof-of-concept testing on full-scale Dáil map using 26 counties/33 cities & counties/43 constituencies/166 LEAs before using 3420 EDs
    - also would be useful for EU MP map using counties
- consider something like `pyerrors` for observable and error tracking to do stats in Python instead of C++
    - would need to store measurements for each config (approx. 30MB for each Hamiltonian + acceptance rate at 10,000 iterations and 151 temperatures) but can do all stats in Python instead of C++
    - this would also avoid any weird variance autocorrelation stuff that's probably a nightmare in C++

`combine_data.py` - combines CSO population, Tailte Éireann geographical, and Electoral (Amendment) Act 2023 constituency data into `ED_data.csv` file for `txt_files_for_MCMC.py` - downloads population data `F1060*.csv` from https://data.cso.ie/table/F1060 and geographical datasets `"CSO*{100m, 50m, 20m, ungeneralised}*.geojson"` from https://data.gov.ie/dataset/cso-electoral-divisions-national-statistical-boundaries-2022-{generalised-100m, generalised-50m, generalised-20m, ungeneralised}1 if not in current directory - only needs to be executed once and can delete CSO file after `ED_data.csv` created - constituency shapes and populations checked against EC report (difference of 2 between Limerick City & County, 20 between Kildare North & South, 1187 between Dublin South-Central & West, 370 between Cork South-Central + North-West & North-Central)

`txt_files_for_MCMC.py` - creates `.txt` files with GUID, population, and neighbours for each ED in specified area for `MCMC_SA.cpp` - command line input takes the form `area_type area_list area_name`, e.g.
````
python3 code/txt_for_MCMC.py County LONGFORD,WESTMEATH,OFFALY,LAOIS "Midland counties"
python3 code/txt_for_MCMC.py Constituency "CORK NORTH-CENTRAL","CORK NORTH-WEST","CORK SOUTH-CENTRAL","CORK SOUTH-WEST" Cork
````

`MCMC_SA.cpp` - uses Metropolis/heatbath algorithm to approximate optimal configuration for given area and coupling constants via simulated annealing, executable takes area name, number of seats per constituency, (non-population) coupling constants, and number of measured/discarded iterations per temperature as command line input assuming files for population and neighbours exist in the current directory, e.g.
````
./MCMC_SA "Midland counties" 2,3,3,3 2,1 5000,100
./MCMC_SA Cork 3,3,4,5,5 4,0.72 10000,1000
````
This also uses OpenMP to parallelise computations - number of threads should be set in the command line via
````
OMP_SET_NUM_THREADS=num_threads
````

`plot.py` - plots statistical physics observables (Hamiltonians, specific heat capacities, acceptance rates) from `MCMC_SA.cpp` output