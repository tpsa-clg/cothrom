Current state of affairs
- `plot.py` unfinished: need to plot energies/variances/acceptance rates
- 192 instances of ED neighbours not agreeing between ungeneralised/20m generalised/50m generalised/100m generalised `.geojson`s - can check this (after downloading relevant `.geojson`s) with:
  ````
  import geopandas as gpd

  df100 = gpd.read_file("CSO_ELECTORAL_DIVISIONS_2022_Genralised_100m_view_726581695825557405.geojson", columns=["ED_GUID", "ED_ENGLISH", "geometry"])
  df50 = gpd.read_file("CSO_ELECTORAL_DIVISIONS_2022_Genralised_50m_view_1781847130366767917.geojson", columns=["ED_GUID", "geometry"])
  df20 = gpd.read_file("CSO_ELECTORAL_DIVISIONS_2022_Genralised_20m_view_4542486875773766239.geojson", columns=["ED_GUID", "geometry"])
  df0 = gpd.read_file("CSO_Electoral_Divisions_National_Statistical_Boundaries_2022_Ungeneralised_view_8626007052615061525.geojson", columns=["ED_GUID", "geometry"])

  for df in [df100, df50, df20, df0]:
    df.sort_values(by="ED_GUID", inplace=True)
    df.reset_index(drop=True, inplace=True)
    df["neighbours"] = [[j for j, touch in enumerate(df.geometry.touches(df.geometry[i])) if touch] for i in range(len(df))]

  tally = 0
  for i in range(len(df100)):
    if (df100.neighbours[i] != df50.neighbours[i]) or (df100.neighbours[i] != df20.neighbours[i]) or (df100.neighbours[i] != df0.neighbours[i]):
      tally += 1
      print(i, df100.ED_ENGLISH[i], df100.ED_GUID[i])
      for df in [df100, df50, df20, df0]:
        print(df.neighbours[i], [df100.ED_ENGLISH[j] for j in df.neighbours[i]])

  print()
  print(tally)
  ````
  - no uniformity/generality of disagreements, e.g. sometimes one ED has more neighbours in one map than the others and sometimes it has less (can happen for any map, i.e. not necessarily just the most/least generalised), sometimes two maps agree with each other and so do the other pair but otherwise disagree (can happen for any pairing, i.e. ungen.&20m + 50m&100m, ungen.&50m + 20m&100m), sometimes only one pair agrees and the other two don't agree with any, sometimes more generalisation increases neighbours and sometimes it decreases neighbours
  - after checking a handful of disagreements there are two potential solutions - both involve calculating all neighbours for each ED in each map in `combine_data.py`, determining the best list for each ED, storing the list of lists in `ED_data.geojson`, and then taking the intersection of each neighbour list and the area of consideration in `txt_for_MCMC.py` (instead of calculating each neighbour list for each ED for one map every time `txt_for_MCMC.py` is executed, as is currently the case):
    - for each ED take the longest list across maps - in the handful I checked, the shorter lists excluded obvious neighbours
    - for each ED take the most commonly appearing list across maps - from skimming the list of disagreements, it seems that for each ED there are always either two or three agreeing neighbour lists
- population term only allows for single-seat groupings (i.e. proof of concept)
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

`combine_data.py` - combines CSO population, Tailte Éireann geographical, and Electoral (Amendment) Act 2023 constituency data into `ED_data.geojson` file for `txt_files_for_MCMC.py` (assumes population data `F1060*.csv` from https://data.cso.ie/table/F1060 and geographical data `"CSO_ELECTORAL_DIVISIONS_2022_Genralised_100m_view_726581695825557405.geojson"` from https://data.gov.ie/dataset/cso-electoral-divisions-national-statistical-boundaries-2022-generalised-100m1 are in current directory) - only needs to be executed once and can delete CSO & Tailte Éireann files after `ED_data.geojson` created - constituency shapes and populations checked against EC report (difference of 2 between Limerick City & County, 20 between Kildare North & South, 1187 between Dublin South-Central & West, 370 between Cork South-Central + North-West & North-Central)

`txt_files_for_MCMC.py` - creates `.txt` files with population and neighbours for each ED in specified area for `MCMC_SA.cpp` - command line input takes the form `area_type area_list area_name`, e.g.
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