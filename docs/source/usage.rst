Usage
=====


Set-Up
------

The required Python packages can be installed in a virtual environment

.. prompt:: bash

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

or by creating a Singularity :maketarget:`container`

.. include:: /snippets/container.rst

:maketarget:`C++ <cpp>` executables are compiled using CMake

.. include:: /snippets/cpp.rst


Preliminary Data
----------------

The :script:`combine_data.py` script obtains and re-organises publicly available electoral division population and geographical data into a CSV file for the constituency optimisation stage.

.. include:: /snippets/combine_data.rst

Unless they already exist in the ``data/`` directory, the ED population and geography files are downloaded.
The county geography file is also downloaded for use in plotting results.


Finding Optimal Constituencies
------------------------------

Preparing data for area of consideration
........................................

The :script:`txt_for_MCMC.py` script prepares ``.txt`` files for ED identifier, population, neighbours, and county data of a given area to be used by the optimisation algorithm.

.. include:: /snippets/txt_for_MCMC.rst

``<area_type>`` denotes the column from which data is selected, and must be one of ``GUID``, ``County``, ``"Administrative Region"``, ``Constituency``, or ``LEA``.
``<area_list>`` denotes the list of column entries defining the area of consideration, and must be provided as a comma-separated list.
``<area_name>`` is the user's nickname for the area under consideration, where generated data is saved in the directory ``data/<area_name>/``.
For example, the following pairs of ``<area_type> <area_list>`` are equivalent for preparing for County Cork:

.. code-block:: bash

    County Cork
    "Administrative Region" CORK,"CORK CITY"
    Constituency "CORK EAST","CORK NORTH-CENTRAL","CORK NORTH-WEST","CORK SOUTH-CENTRAL","CORK SOUTH-WEST"
    LEA FERMOY,"BANTRY-WEST CORK",CARRIGALINE,MIDLETON,MACROOM,"SKIBBEREEN-WEST CORK","CORK CITY SOUTH WEST",KANTURK,MALLOW,"BANDON-KINSALE",COBH,"CORK CITY NORTH EAST","CORK CITY SOUTH EAST","CORK CITY SOUTH CENTRAL","CORK CITY NORTH WEST"

The Python script also prepares a CSV for the 2023 electoral boundaries in the same format as the algorithm output for comparison.

Running the algorithm
.....................

The :script:`MCMC_SA <MCMC_SA.cpp>` executable finds optimal constituency configurations for a given area and algorithm parameters

.. include:: /snippets/MCMC_SA.rst

where ``<area_name>`` is defined as above, ``<seat_makeup>`` is a comma-separated list of the number of seats in each constituency, ``<coupling_constants>`` is a comma-separated list of the weights given to each objective (except for equality of representation), and ``<measured_discarded_sweeps>`` is a comma-separated pair of numbers of sweeps for expected value calculations and sampling thermalisation, respectively, e.g.

.. prompt:: bash

    ./build/MCMC_SA "Midland counties" 2,3,3,3 2,1,3 5000,100
    ./build/MCMC_SA Limerick 3,4 0,0,0 1000,0
    ./build/MCMC_SA Cork 3,3,4,5,5 4,0.72,0 10000,1000

The :envvar:`seed <SEED>` for the random number generators can be set via

.. prompt:: bash

    export SEED=<seed>

where the default value ``1234`` is used otherwise.

The :script:`actual_H <actual_H.cpp>` executable calculates and saves the Hamiltonians for the 2023 electoral boundaries via

.. include:: /snippets/actual_H.rst


Analysing & Visualising Results
-------------------------------

The :script:`plot_stats.py` and :script:`plot_config.py` scripts plot observables of interest and initial and final constituency configurations for a given algorithm run.

.. prompt:: bash $ auto

    # Virtual environment
    $ python code/plot\_{stats,config}.py <area_name> <run_ID>

    # Singularity container
    $ singularity run --bind ${PWD} cothrom.sif code/plot\_{stats,config}.py <area_name> <run_ID>

``<run_ID>`` corresponds to a timestamp identifier of an algorithm run or to the 2023 electoral boundaries, e.g.

.. prompt:: bash ... auto

    ... code/plot_stats.py "Midland counties" 3133663620
    ... code/plot_config.py Limerick actual


Pareto Analysis
---------------

Additionally provided is a :script:`Pareto.sh` script for parallel runs over algorithm parameters using Slurm

.. prompt:: bash

    bash code/Pareto.sh

and a :script:`plot_Pareto.py` script for multi-criteria decision analysis

.. include:: /snippets/plot_Pareto.rst

The configuration values of the shell script can be modified for custom parameter sets.
