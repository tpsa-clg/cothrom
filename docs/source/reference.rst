Reference
=========


Python scripts ``code/*.py``
----------------------------

.. script:: combine_data.py

    Merges the ED population and geography data for use by the optimisation algorithm. Attempts to download :datafile:`Counties*.geojson` if not already available.

    :usage:

    .. include:: /snippets/combine_data.rst

    :input F1060\*.csv: population data (downloaded if not already available)
    :input \*100m\*.geojson: geography data (downloaded if not already available)
    :output ED\_data.csv: all electoral division data required for the optimisation algorithm
    :output Constituency\_data.csv: 2023 electoral constituency seats

.. script:: plot_config.py

    Plots the initial and optimised constituency configurations for a given algorithm run, or the 2023 electoral constituencies for a given area.

    :usage:

    .. prompt:: bash $ auto

        # Virtual environment
        $ python code/plot_config.py <area_name> <run_ID>

        # Singularity container
        $ singularity run --bind ${PWD} cothrom.sif code/plot_config.py <area_name> <run_ID>
    
    :arg <area_name>: name of area
    :arg <run_ID>: ID number (timestamp) of algorithm run, or ``"actual"`` for 2023 configuration
    :input \*100m\*.geojson: ED geography data
    :input GUID.txt: ED identifiers
    :input <seat_makeup>_<coupling_constants>_<run_ID>.csv: output of algorithm run (if ``<run_ID> != "actual"``)
    :input actual.csv: 2023 electoral constituencies (if ``<run_ID> == "actual"``)
    :input Population.txt: ED populations
    :input Counties\*.geojson: ED counties
    :output Configurations\_<run_ID>.pdf: constituency configuration(s)

.. script:: plot_Pareto.py

    Plots the Pareto fronts for all algorithm runs for given numbers of seats and constituencies and a given area. Includes the 2023 constituencies if available.

    :usage:

    .. include:: /snippets/plot_Pareto.rst

    :arg <area_name>: name of area
    :arg <seats>: number of seats
    :arg <constituencies>: number of constituencies
    :input <seat_makeup>_<coupling_constants>_<run_ID>.csv: all algorithm outputs for given seats and constituencies
    :input actual.csv: 2023 electoral constituencies (optional)
    :output Pareto.pdf: Pareto fronts

.. script:: plot_stats.py

    Plots the evolution of energies, heat capacities, autocorrelations, runtime, and acceptance rate during the simulated annealing process of a given algorithm run.

    :usage:

    .. prompt:: bash $ auto

        # Virtual environment
        $ python code/plot_stats.py <area_name> <run_ID>

        # Singularity container
        $ singularity run --bind ${PWD} cothrom.sif code/plot_stats.py <area_name> <run_ID>

    :arg <area_name>: name of area
    :arg <run_ID>: ID number (timestamp) of algorithm run
    :input <seat_makeup>_<coupling_constants>_<run_ID>.csv: output of algorithm run
    :output Objectives_per_observable_<run_ID>.pdf: observable plots grouped by observable type
    :output Observables_per_objective_<run_ID>.pdf: observable plots grouped by objective
    :output Runtime_Acceptance_<run_ID>.pdf: runtime and acceptance rate plots

.. script:: txt_for_MCMC.py

    Prepares the necessary files for algorithm runs for a given area.

    :usage:

    .. include:: /snippets/txt_for_MCMC.rst

    :arg <area_type>: type of areas specified in ``<area_list>``
    :arg <area_list>: list of areas of type ``<area_type>``
    :arg <area_name>: custom name given to area
    :input ED_data.csv: ED data
    :input Constituency_data.csv: constituency seats
    :output GUID.txt: ED identifiers
    :output Population.txt: ED populations
    :output Neighbours.txt: ED neighbours
    :output County.txt: ED counties
    :output actual.csv: 2023 electoral constituencies
    :output Population.pdf: histogram of ED populations
    :output Area.pdf: histogram of ED areas
    :output Perimeter.pdf: histogram of ED perimeters
    :output Neighbours.pdf: histogram of number of ED neighbours


C++ scripts ``src/*.cpp``
-------------------------

.. script:: actual_H.cpp

    Calculates and saves to :datafile:`actual.csv` the Hamiltonians of the 2023 electoral boundaries.

    :usage:

    .. include:: /snippets/actual_H.rst

    :arg <area_name>: name of area
    :input actual.csv: 2023 electoral constituencies
    :input Population.txt: ED populations
    :input Neighbours.txt: ED neighbours
    :input County.txt: ED counties
    :output actual.csv: 2023 electoral constituencies and corresponding Hamiltonians

.. script:: MCMC_SA.cpp

    Optimises constituency boundaries of a given area for given makeup of constituency seats, set of objective weights, and number of sweeps per temperature.

    :usage:

    .. include:: /snippets/MCMC_SA.rst

    :arg <area_name>: name of area
    :arg <seat_makeup>: seats per constituency
    :arg <coupling_constants>: objective weights (excluding equality of representation)
    :arg <measured_discarded_sweeps>: number of MCMC sweeps per temperature for observbale calculations and thermalisation
    :env OMP_NUM_THREADS: number of OpenMP threads
    :env SEED: seed for random number generation
    :input Population.txt: ED populations
    :input Neighbours.txt: ED neighbours
    :input County.txt: ED counties
    :output <seat_makeup>_<coupling_constants>_<run_ID>.csv: algorithm parameters, initial and optimised configurations, and observable evolutions


Shell scripts ``code/*.sh``
---------------------------

.. script:: Pareto.sh

    Makes the :maketarget:`ED data <ED_data>` and :maketarget:`C++ <cpp>` executables, :maketarget:`prepares <prepare>` required text files for the algorithm, and submits Slurm jobs for parallel :script:`runs <MCMC_SA.cpp>`. The output data listed below includes only that used in the Python plotting scripts, and excludes intermediarily generated data.

    :conf string area_type: see :script:`txt_for_MCMC.py`
    :conf string area_list: see :script:`txt_for_MCMC.py`
    :conf string area_name: see :script:`txt_for_MCMC.py`, :script:`actual_H.cpp`, :script:`MCMC_SA.cpp`
    :conf array[string] seat_configs: constituency seat makeups, see :script:`MCMC_SA.cpp`
    :conf float JC_proportion: contiguity objective weight as a proportion of sum of objective weights, see :script:`MCMC_SA.cpp`
    :conf array[float] JDs: compactness objective weights, see :script:`MCMC_SA.cpp`
    :conf array[float] JBs: county boundary objective weights, see :script:`MCMC_SA.cpp`
    :conf integer N_meas: number of measurement sweeps per temperature, see :script:`MCMC_SA.cpp`
    :conf integer N_dics: number of thermalisation sweeps per temperature, see :script:`MCMC_SA.cpp`
    :conf integer threads: see :envvar:`OMP_NUM_THREADS`
    :env SEED: see :script:`MCMC_SA.cpp`
    :input F1060\*.csv: see :script:`combine_data.py`
    :input \*100m\*.geojson: see :script:`combine_data.py`
    :output GUID.txt: see :script:`txt_for_MCMC.py`
    :output Population.txt: see :script:`txt_for_MCMC.py`
    :output actual.csv: see :script:`actual_H.cpp`
    :output <seat_makeup>_<coupling_constants>_<run_ID>.csv: all algorithm outputs for given seat makeups and coupling constants, see :script:`MCMC_SA.cpp`


Environment variables
---------------------

.. envvar:: OMP_NUM_THREADS

    Number of OpenMP threads to use for parallelisation in :script:`MCMC_SA.cpp`. Note that the ``Map::GS_Sweep`` method avails of parallelism only when set greater than 32.

.. envvar:: SEED

    Seed for random number generation in :script:`MCMC_SA.cpp`. ``Map.cpp`` uses a default seed of 1234 if not set.


Makefile targets
----------------

.. maketarget:: container

    Makes a Singularity container for running Python scripts.

    :usage:

    .. include:: /snippets/container.rst

.. maketarget:: cpp

    Makes the C++ executables.

    :usage:

    .. include:: /snippets/cpp.rst

.. maketarget:: ED_data

    Makes :datafile:`ED_data.csv` according to :script:`combine_data.py`.

    :dependency container: uses the Singularity container to run Python

.. maketarget:: prepare

    Prepare the text files according to :script:`txt_for_MCMC.py`.

    :dependency ED_data: uses the ED data to prepare files


Input files
-----------

.. datafile:: *100m*.geojson

    ED geographies.

    :directory: ``data/``
    :source: `Tailte Éireann <https://data.gov.ie/dataset/cso-electoral-divisions-national-statistical-boundaries-2022-generalised-100m>`_ (`API <https://data-osi.opendata.arcgis.com/api/download/v1/items/a55332e0d15148688e06893086cb023b/geojson?layers=1>`_)
    :usedby combine_data.py: used to obtain ED area, perimeter, and neighbours
    :usedby plot_config.py: used to plot constituency configurations

.. datafile:: Counties*.geojson

    County geographies.

    :directory: ``data/``
    :source: `Tailte Éireann <https://data.gov.ie/dataset/counties-national-statutory-boundaries-2019-generalised-20m>`_ (`API <https://data-osi.opendata.arcgis.com/api/download/v1/items/7ef9c5102d61424295e98505a00251ea/geojson?layers=0>`_)
    :usedby plot_config.py: used to show county boundaries in constituency configuration plots

.. datafile:: F1060*.csv

    ED populations.

    :directory: ``data/``
    :source: `Central Statistics Office <https://data.cso.ie/table/F1060>`_ (`API <https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.PxAPIv1/en/76/C2022P1/F1060?query=%7B%22query%22:%5B%7B%22code%22:%22STATISTIC%22,%22selection%22:%7B%22filter%22:%22item%22,%22values%22:%5B%22F1060C01%22%5D%7D%7D,%7B%22code%22:%22C02199V02655%22,%22selection%22:%7B%22filter%22:%22item%22,%22values%22:%5B%22-%22%5D%7D%7D%5D,%22response%22:%7B%22format%22:%22csv%22,%22pivot%22:null,%22codes%22:true%7D%7D>`_)
    :usedby combine_data.py: used for population column in :datafile:`ED_data.csv`


Generated files
---------------

.. datafile:: Constituency_data.csv

    Number of seats for the 2023 electoral constituencies.

    :directory: ``data/``
    :source: :script:`combine_data.py`
    :usedby txt_for_MCMC.py: used in creating :datafile:`actual.csv`

.. datafile:: ED_data.csv

    Spreadsheet of ED data used in the optimisation procedure.

    :directory: ``data/``
    :source: :script:`combine_data.py`
    :usedby txt_for_MCMC.py: used to prepare files for :script:`actual_H.cpp` and :script:`MCMC_SA.cpp`

.. datafile:: actual.csv

    ED allocations according to the 2023 electoral constituencies.

    :directory: ``data/<area_name>/``
    :source: created by :script:`txt_for_MCMC.py`, modified by :script:`actual_H.cpp` TODO
    :usedby plot_config.py: used to plot 2023 electoral constituencies
    :usedby plot_Pareto.py: used to include 2023 electoral constituencies in Pareto fronts (optional)

.. datafile:: Area.pdf

    Histograms of ED areas.

    :directory: ``data/<area_name>/``
    :source: :script:`txt_for_MCMC.py`

.. datafile:: County.txt

    List of ED county indices.

    :directory: ``data/<area_name>/``
    :source: :script:`txt_for_MCMC.py`
    :usedby actual_H.cpp: used to calculate :math:`H_C`
    :usedby MCMC_SA.cpp: used to calculate :math:`H_C` and :math:`\Delta H_C`

.. datafile:: GUID.txt

    List of unique ED identifiers.

    :directory: ``data/<area_name>/``
    :source: :script:`txt_for_MCMC.py`
    :usedby plot_config.py: used to match constituency allocations to geographies

.. datafile:: Neighbours.pdf

    Histograms of numbers of ED neighbours.

    :directory: ``data/<area_name>/``
    :source: :script:`txt_for_MCMC.py`

.. datafile:: Neighbours.txt

    List of numbers of ED neighbours.

    :directory: ``data/<area_name>/``
    :source: :script:`txt_for_MCMC.py`
    :usedby actual_H.cpp: used to calculate :math:`H_D`
    :usedby MCMC_SA.cpp: used to calculate :math:`H_D` and :math:`\Delta H_D`

.. datafile:: Perimeter.pdf

    Histograms of ED perimeters.

    :directory: ``data/<area_name>/``
    :source: :script:`txt_for_MCMC.py`

.. datafile:: Population.pdf

    Histograms of ED populations.

    :directory: ``data/<area_name>/``
    :source: :script:`txt_for_MCMC.py`

.. datafile:: Population.txt

    List of ED populations.

    :directory: ``data/<area_name>/``
    :source: :script:`txt_for_MCMC.py`
    :usedby actual_H.cpp: used to calculate :math:`H_P`
    :usedby MCMC_SA.cpp: used to calculate :math:`H_P` and :math:`\Delta H_P`
    :usedby plot_config.py: used to show population variances in figure legend

.. datafile:: <seat_makeup>_<coupling_constants>_<run_ID>.csv

    Algorithm parameters, initial and optimised configurations, and observable evolutions.

    :directory: ``data/<area_name>/<seats>_<constituencies>/``
    :source: :script:`MCMC_SA.cpp`
    :usedby plot_config.py: used to plot initial and optimised configurations
    :usedby plot_Pareto.py: used to plot Pareto scatterplot
    :usedby plot_stats.py: used to plot observable evolutions

.. datafile:: Configurations_<run_ID>.pdf

    Plots of initial and optimised (or actual) constituency configurations.

    :directory: ``data/<area_name>/<seats>_<constituencies>/``
    :source: :script:`plot_config.py`

.. datafile:: Objectives_per_observable_<run_ID>.pdf

    Plots of energies, heat capacities, and autocorrelation times, grouped by observable.

    :directory: ``data/<area_name>/<seats>_<constituencies>/``
    :source: :script:`plot_stats.py`

.. datafile:: Observables_per_objective_<run_ID>.pdf

    Plots of energies, heat capacities, and autocorrelation times, grouped by objective.

    :directory: ``data/<area_name>/<seats>_<constituencies>/``
    :source: :script:`plot_stats.py`

.. datafile:: Pareto.pdf

    Plots of estimated Pareto fronts.

    :directory: ``data/<area_name>/<seats>_<constituencies>/``
    :source: :script:`plot_Pareto.py`

.. datafile:: Runtime_Acceptance_<run_ID>.pdf

    Plots of algorithm runtimes and MCMC acceptance rates.

    :directory: ``data/<area_name>/<seats>_<constituencies>/``
    :source: :script:`plot_stats.py`
