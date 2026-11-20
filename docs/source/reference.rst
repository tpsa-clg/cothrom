Reference
=========


Python scripts
--------------

code/combine_data.py
....................

.. program:: combine_data.py

combines the data or something

.. include:: /snippets/combine_data.rst

code/plot_config.py
...................

.. program:: plot_config.py

plots configurations or something

.. prompt:: bash $ auto

    # Virtual environment
    $ python code/plot_config.py <area_name> <run_ID>

    # Singularity container
    $ singularity run --bind ${PWD} cothrom.sif code/plot_config.py <area_name> <run_ID>

.. option:: <area_name>

    name of area or something

.. option:: <run_ID>

    ID number for algorithm run or something

code/plot_Pareto.py
....................

.. program:: plot_Pareto.py

plots Pareto fronts or something

.. include:: /snippets/plot_Pareto.rst

.. option:: <area_name>

    name of area or something

.. option:: <seats>

    number of seats or something

.. option:: <constituencies>

    number of constituencies or something

code/plot_stats.py
...................

.. program:: plot_stats.py

plots observable statistics or something

.. prompt:: bash $ auto

    # Virtual environment
    $ python code/plot_stats.py <area_name> <run_ID>

    # Singularity container
    $ singularity run --bind ${PWD} cothrom.sif code/plot_stats.py <area_name> <run_ID>

.. option:: <area_name>

    name of area or something

.. option:: <run_ID>

    ID number for algorithm run or something

code/txt_for_MCMC.py
....................

.. program:: txt_for_MCMC.py

prepares for MCMC or something

.. include:: /snippets/txt_for_MCMC.rst

.. option:: <area_type>

    type of area or something

.. option:: <area_list>

    list of areas or something

.. option:: <area_name>

    name of area or something


C++ scripts
-----------

src/actual_H.cpp
................

.. program:: actual_H

actual Hamiltonian script or something

.. include:: /snippets/actual_H.rst

.. option:: <area_name>

    name of area or something

src/MCMC_SA.cpp
...............

.. program:: MCMC_SA

main algorithm or something

.. include:: /snippets/MCMC_SA.rst

.. option:: <area_name>

    name of area or something

.. option:: <seat_makeup>

    seats per constituency or something

.. option:: <coupling_constants>

    objective weights or something

.. option:: <measured_discarded_sweeps>

    measurement and thermalising sweeps or something


Bash scripts
-------------

code/Pareto.sh
..............

.. program:: Pareto.sh

Slurm script for Pareto analysis or something

.. confval:: area_type
    :type: ``string``

    type of area or something

.. confval:: area_list
    :type: ``string``

    list of areas or something

.. confval:: area_name
    :type: ``string``

    name of area or something

.. confval:: seats
    :type: ``integer``

    number of seats or something

.. confval:: constituencies
    :type: ``integer``

    number of constituencies or something

.. confval:: seat_configs
    :type: ``array[string]``

    constituency seat makeups for Pareto analysis or something

.. confval:: JC_proportion
    :type: ``float``

    proportion of total objective weight given to contiguity or something

.. confval:: JDs
    :type: ``array[float]``

    compactness objective weights or something

.. confval:: JBs
    :type: ``array[float]``

    county boundary objective weights or something

.. confval:: N_meas
    :type: ``integer``

    measurement sweeps or something

.. confval:: N_disc
    :type: ``integer``

    thermalising sweeps or something

.. confval:: threads
    :type: ``integer``

    number of OpenMP threads or something


Environment variables
---------------------

OMP_NUM_THREADS
...............

number of OpenMP threads or something

SEED
....

random number seed or something, default 1234


Makefile targets
----------------

container
.........

.. program:: make container

make the container or something

.. include:: /snippets/container.rst

cpp
...

.. program:: make cpp

make the executables or something

.. include:: /snippets/cpp.rst

ED_data
.......

.. program:: make ED_data

makes ``ED_data.csv`` or something, see `code/combine_data.py`_

prepare
.......

.. program:: make prepare

prepare the text files or something, see `code/txt_for_MCMC.py`_


Input files
-----------

\*100m\*.geojson
................

ED geographical data or something, `webpage <https://data.gov.ie/dataset/cso-electoral-divisions-national-statistical-boundaries-2022-generalised-100m>`_, `code/combine_data.py`_ uses `API <https://data-osi.opendata.arcgis.com/api/download/v1/items/a55332e0d15148688e06893086cb023b/geojson?layers=1>`_, used for plotting in `code/plot_config.py`_

Counties\*.geojson
..................

county geographical data or something, `webpage <https://data.gov.ie/dataset/counties-national-statutory-boundaries-2019-generalised-20m>`_, `code/combine_data.py`_ uses `API <https://data-osi.opendata.arcgis.com/api/download/v1/items/7ef9c5102d61424295e98505a00251ea/geojson?layers=0>`_, used for plotting in `code/plot_config.py`_

F1060\*.csv
...........

population data or something, `webpage <https://data.cso.ie/table/F1060>`_, `code/combine_data.py`_ uses `API <https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.PxAPIv1/en/76/C2022P1/F1060?query=%7B%22query%22:%5B%7B%22code%22:%22STATISTIC%22,%22selection%22:%7B%22filter%22:%22item%22,%22values%22:%5B%22F1060C01%22%5D%7D%7D,%7B%22code%22:%22C02199V02655%22,%22selection%22:%7B%22filter%22:%22item%22,%22values%22:%5B%22-%22%5D%7D%7D%5D,%22response%22:%7B%22format%22:%22csv%22,%22pivot%22:null,%22codes%22:true%7D%7D>`_


Generated files
---------------

generated files or something
