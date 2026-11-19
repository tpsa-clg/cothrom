Usage
=====


.. _setup:

Set-Up
------------

The required Python packages can be installed in a virtual environment

.. prompt:: bash

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

or by creating a Singularity container

.. include:: /snippets/container.rst

C++ executables are compiled using CMake

.. include:: /snippets/cpp.rst


.. _prelim:

Preliminary Data
----------------

The ``code/combine_data.py`` script obtains and re-organises publicly available electoral division population and geographical data into a CSV file for the constituency optimisation stage.

.. include:: /snippets/combine_data.rst

Unless they already exist in the ``data/`` directory, the `population`_ ``F1060*.csv`` and `geographical`_ ``*100m*.geojson`` files are downloaded.
The `geographical file`_ ``Counties*.geojson`` is also downloaded for county boundaries for use in plotting results.

.. _population: https://data.cso.ie/table/F1060
.. _geographical: https://data.gov.ie/dataset/cso-electoral-divisions-national-statistical-boundaries-2022-generalised-100m
.. _geographical file: https://data.gov.ie/dataset/counties-national-statutory-boundaries-2019-generalised-20m


.. _finding:

Finding Optimal Constituencies
------------------------------

.. _preparing:

Preparing data for area of consideration
........................................

The ``txt_for_MCMC.py`` script prepares ``.txt`` files for ED identifier, population, neighbours, and county data of a given area to be used by the optimisation algorithm.

.. include:: /snippets/txt_for_MCMC.rst

``<area_type>`` denotes the column from which data is selected, and must be one of ``GUID``, ``County``, ``"Administrative Region"``, ``Constituency``, or ``LEA``.
``<area_list>`` denotes the list of column entries defining the area of consideration, and must be provided as a comma-separated list.
``<area_name`` is the user's nickname for the area under consideration, where generated data is saved in the directory ``data/<area_name>``.
For example, the following pairs of ``<area_type> <area_list>`` are equivalent for preparing for County Cork:

.. code-block:: bash

    County Cork
    "Administrative Region" CORK,"CORK CITY"
    Constituency "CORK EAST","CORK NORTH-CENTRAL","CORK NORTH-WEST","CORK SOUTH-CENTRAL","CORK SOUTH-WEST"
    LEA FERMOY,"BANTRY-WEST CORK",CARRIGALINE,MIDLETON,MACROOM,"SKIBBEREEN-WEST CORK","CORK CITY SOUTH WEST",KANTURK,MALLOW,"BANDON-KINSALE",COBH,"CORK CITY NORTH EAST","CORK CITY SOUTH EAST","CORK CITY SOUTH CENTRAL","CORK CITY NORTH WEST"

The Python script also prepares a CSV for the 2023 electoral boundaries (under ``data/<area_name>/actual.csv``) in the same format as the algorithm output for comparison.

.. _running:

Running the algorithm
.....................

The ``MCMC_SA`` executable finds optimal constituency configurations for a given area and algorithm parameters

.. include:: /snippets/MCMC_SA.rst

where ``<area_name>`` is defined as above, ``<seat_makeup>`` is a comma-separated list of the number of seats in each constituency, ``<coupling_constants>`` is a comma-separated list of the weights given to each objective (except for equality of representation), and ``<measured_discarded_sweeps>`` is a comma-separated pair of numbers of sweeps for expected value calculations and sampling thermalisation, respectively, e.g.

.. prompt:: bash

    ./build/MCMC_SA "Midland counties" 2,3,3,3 2,1,3 5000,100
    ./build/MCMC_SA Limerick 3,4 0,0,0 1000,0
    ./build/MCMC_SA Cork 3,3,4,5,5 4,0.72,0 10000,1000

Seeds for the random number generators can be set via

.. prompt:: bash

    export SEED=<seed>

where the default value ``1234`` is used otherwise.

The Hamiltonians for the 2023 electoral boundaries are inserted into ``actual.csv`` via

.. include:: /snippets/actual_H.rst


.. _analysing:

Analysing & Visualising Results
-------------------------------

The ``plot_stats.py`` and ``plot_config.py`` scripts plot observables of interest and initial and final constituency configurations for a given algorithm run.

.. prompt:: bash $ auto

    # Virtual environment
    $ python code/plot_{stats,config}.py <area_name> <run_ID>

    # Singularity container
    $ singularity run --bind ${PWD} cothrom.sif code/plot_{stats,config}.py <area_name> <run_ID>

``<run_ID>`` corresponds to a timestamp identifier of an algorithm run or to the 2023 electoral boundaries, e.g.

.. prompt:: bash ... auto

    ... code/plot_stats.py "Midland counties" 3133663620
    ... code/plot_config.py Limerick actual

Plots are saved to ``data/<area_name>/<seats>_<constituencies>``.


.. _pareto:

Pareto Analysis
---------------

Additionally provided is a shell script for parallel runs over algorithm parameters using Slurm

.. prompt:: bash

    bash code/Pareto.sh

and a Python script for multi-criteria decision analysis

.. include:: /snippets/plot_Pareto.rst

``Pareto.sh`` can be modified for custom parameter sets. Plots of the resulting Pareto fronts can be found at ``data/<area_name>/<seats>_<constituencies>/Pareto.pdf``.
