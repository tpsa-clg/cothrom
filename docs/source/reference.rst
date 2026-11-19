Reference
=========


.. _python:

Python scripts
------------------------

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


.. _C++:

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


.. _bash:

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


.. _env:

Environment variables
---------------------

OMP_NUM_THREADS
...............

number of OpenMP threads or something

SEED
....

random number seed or something, default 1234


.. _make:

Makefile targets
----------------

container
...

.. program:: make container

make the container or something

.. include:: /snippets/container.rst

cpp
...

.. program:: make cpp

make the executables or something

.. include:: /snippets/cpp.rst


.. _input:

Input files
-----------

input files or something


.. _output:

Generated files
---------------

generated files or something
