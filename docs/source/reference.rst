Reference
=========


Python scripts ``code/*.py``
----------------------------

.. script:: combine_data.py

    combines the data, downloads inputs if not already in ``data/``. TODO

    :usage:

    .. include:: /snippets/combine_data.rst

    :input F1060\*.csv: TODO
    :input \*100m\*.geojson: TODO
    :input Counties\*.geojson: TODO
    :output ED\_data.csv: TODO
    :output Constituency\_data.csv: TODO

.. script:: plot_config.py

    plots configurations TODO

    :usage:

    .. prompt:: bash $ auto

        # Virtual environment
        $ python code/plot_config.py <area_name> <run_ID>

        # Singularity container
        $ singularity run --bind ${PWD} cothrom.sif code/plot_config.py <area_name> <run_ID>
    
    :arg <area_name>: name of area TODO
    :arg <run_ID>: ID number for algorithm run TODO
    :input <seat_makeup>_<coupling_constants>_<run_ID>.csv: TODO
    :output Configurations\_<run_ID>.pdf: TODO - also add i/o files from below

.. script:: plot_Pareto.py

    plots Pareto fronts TODO

    :usage:

    .. include:: /snippets/plot_Pareto.rst

    :arg <area_name>: name of area TODO
    :arg <seats>: number of seats TODO
    :arg <constituencies>: number of constituencies TODO

.. script:: plot_stats.py

    plots observable statistics TODO

    :usage:

    .. prompt:: bash $ auto

        # Virtual environment
        $ python code/plot_stats.py <area_name> <run_ID>

        # Singularity container
        $ singularity run --bind ${PWD} cothrom.sif code/plot_stats.py <area_name> <run_ID>

    :arg <area_name>: name of area TODO
    :arg <run_ID>: ID number for algorithm run TODO

.. script:: txt_for_MCMC.py

    prepares for MCMC TODO

    :usage:

    .. include:: /snippets/txt_for_MCMC.rst

    :arg <area_type>: type of area TODO
    :arg <area_list>: list of areas TODO
    :arg <area_name>: name of area TODO


C++ scripts ``src/*.cpp``
-------------------------

.. script:: actual_H.cpp

    actual Hamiltonian script TODO

    :usage:

    .. include:: /snippets/actual_H.rst

    :arg <area_name>: name of area TODO

.. script:: MCMC_SA.cpp

    main algorithm TODO

    :usage:

    .. include:: /snippets/MCMC_SA.rst

    :arg <area_name>: name of area TODO
    :arg <seat_makeup>: seats per constituency TODO
    :arg <coupling_constants>: objective weights TODO
    :arg <measured_discarded_sweeps>: measurement and thermalising sweeps TODO
    :env OMP_NUM_THREADS: number of threads TODO
    :env SEED: random seed TODO


Bash scripts ``code/*.sh``
--------------------------

.. script:: Pareto.sh

    Slurm script for Pareto analysis TODO

    :conf string area_type: type of area TODO
    :conf string area_list: list of areas TODO
    :conf string area_name: name of area TODO
    :conf integer seats: number of seats TODO
    :conf integer constituencies: number of constituencies TODO
    :conf array[string] seat_configs: constituency seat makeups for Pareto analysis TODO
    :conf float JC_proportion: proportion of total objective weight given to contiguity TODO
    :conf array[float] JDs: compactness objective weights TODO
    :conf array[float] JBs: county boundary objective weights TODO
    :conf integer N_meas: measurement sweeps TODO
    :conf integer N_dics: thermalising sweeps TODO
    :conf integer threads: number of OpenMP threads TODO


Environment variables
---------------------

.. envvar:: OMP_NUM_THREADS

    number of OpenMP threads TODO

.. envvar:: SEED

    random number seed, default 1234 TODO


Makefile targets
----------------

.. maketarget:: container

    make the container TODO

    :usage:

    .. include:: /snippets/container.rst

.. maketarget:: cpp

    make the executables TODO

    :usage:

    .. include:: /snippets/cpp.rst

.. maketarget:: ED_data

    makes ``ED_data.csv``, see :script:`combine_data.py` TODO

.. maketarget:: prepare

    prepare the text files, see :script:`txt_for_MCMC.py` TODO

    :arg AREA_TYPE: type of area TODO
    :arg AREA_LIST: list of areas TODO
    :arg AREA_NAME: name of area TODO


Input files
-----------

data/\*100m\*.geojson
.....................

ED geographical data or something, `webpage <https://data.gov.ie/dataset/cso-electoral-divisions-national-statistical-boundaries-2022-generalised-100m>`_, :script:`combine_data.py` uses `API <https://data-osi.opendata.arcgis.com/api/download/v1/items/a55332e0d15148688e06893086cb023b/geojson?layers=1>`_, used by :script:`plot_config.py`

data/Counties\*.geojson
.......................

county geographical data or something, `webpage <https://data.gov.ie/dataset/counties-national-statutory-boundaries-2019-generalised-20m>`_, :script:`combine_data.py` uses `API <https://data-osi.opendata.arcgis.com/api/download/v1/items/7ef9c5102d61424295e98505a00251ea/geojson?layers=0>`_, used by :script:`plot_config.py`

data/F1060\*.csv
................

population data or something, `webpage <https://data.cso.ie/table/F1060>`_, :script:`combine_data.py` uses `API <https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.PxAPIv1/en/76/C2022P1/F1060?query=%7B%22query%22:%5B%7B%22code%22:%22STATISTIC%22,%22selection%22:%7B%22filter%22:%22item%22,%22values%22:%5B%22F1060C01%22%5D%7D%7D,%7B%22code%22:%22C02199V02655%22,%22selection%22:%7B%22filter%22:%22item%22,%22values%22:%5B%22-%22%5D%7D%7D%5D,%22response%22:%7B%22format%22:%22csv%22,%22pivot%22:null,%22codes%22:true%7D%7D>`_


Generated files
---------------

data/Constituency_data.csv
..........................

2023 constituency seats or something, generated by :script:`combine_data.py`, used by :script:`txt_for_MCMC.py`

data/ED_data.csv
................

electoral division data required for cothrom framework or something, generated by :script:`combine_data.py`, used by :script:`txt_for_MCMC.py`

data/<area_name>/actual.csv
...........................

2023 constituency configuration or something, generated by :script:`txt_for_MCMC.py` and :script:`actual_H.cpp`, used by :script:`plot_config.py` and :script:`plot_Pareto.py`

data/<area_name>/Area.pdf
.........................

histograms of electoral division areas or something, generated by :script:`txt_for_MCMC.py`

data/<area_name>/County.txt
...........................

list of electoral division counties or something, generated by :script:`txt_for_MCMC.py`, used by :script:`MCMC_SA.cpp`

data/<area_name>/GUID.txt
.........................

list of electoral division GUIDs or something, generated by :script:`txt_for_MCMC.py`, used by :script:`MCMC_SA.cpp` and :script:`plot_config.py`

data/<area_name>/Neighbours.pdf
...............................

histograms of number of electoral division neighbours or something, generated by :script:`txt_for_MCMC.py`

data/<area_name>/Neighbours.txt
...............................

list of number of electoral division neighbours or something, generated by :script:`txt_for_MCMC.py`, used by :script:`MCMC_SA.cpp`

data/<area_name>/Perimeter.pdf
..............................

histograms of electoral division perimeters or something, generated by :script:`txt_for_MCMC.py`

data/<area_name>/Population.pdf
...............................

histograms of electoral division populations or something, generated by :script:`txt_for_MCMC.py`

data/<area_name>/Population.txt
...............................

list of electoral division populations or something, generated by :script:`txt_for_MCMC.py`, used by :script:`MCMC_SA.cpp` and :script:`plot_config.py`

data/<area_name>/<seats>_<constituencies>/<seat_makeup>_<coupling_constants>_<run_ID>.csv
.........................................................................................

algorithm output or something, generated by :script:`MCMC_SA.cpp`, used by :script:`plot_config.py`, :script:`plot_Pareto.py`, and :script:`plot_stats.py`

data/<area_name>/<seats>_<constituencies>/Configurations\_<run_ID>.pdf
...................................................................................

plots of initial and optimal configurations or something, generated by :script:`plot_config.py`

data/<area_name>/<seats>_<constituencies>/Objectives\_per\_observable\_<run_ID>.pdf
...................................................................................

plots of each objective per observable or something, generated by :script:`plot_stats.py`

data/<area_name>/<seats>_<constituencies>/Observables\_per\_objective\_<run_ID>.pdf
...................................................................................

plots of each observable per objective or something, generated by :script:`plot_stats.py`

data/<area_name>/<seats>_<constituencies>/Pareto.pdf
....................................................

plots of Pareto fronts or something, generated by :script:`plot_Pareto.py`

data/<area_name>/<seats>_<constituencies>/Runtime\_Acceptance\_<run_ID>.pdf
...........................................................................

plots runtimes and acceptance rates or something, generated by :script:`plot_stats.py`
