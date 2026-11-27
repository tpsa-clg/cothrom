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
    :input \*100m\*.geojson: TODO
    :input GUID.txt: TODO
    :input <seat_makeup>_<coupling_constants>_<run_ID>.csv: TODO (or actual)
    :input Population.txt: TODO
    :input Counties\*.geojson: TODO
    :output Configurations\_<run_ID>.pdf: TODO

.. script:: plot_Pareto.py

    plots Pareto fronts TODO

    :usage:

    .. include:: /snippets/plot_Pareto.rst

    :arg <area_name>: name of area TODO
    :arg <seats>: number of seats TODO
    :arg <constituencies>: number of constituencies TODO
    :input <seat_makeup>_<coupling_constants>_<run_ID>.csv: TODO (multiple)
    :input actual.csv: TODO (optional)
    :output Pareto.pdf: TODO

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
    :input <seat_makeup>_<coupling_constants>_<run_ID>.csv: TODO
    :output Objectives_per_observable_<run_ID>.pdf: TODO
    :output Observables_per_objective_<run_ID>.pdf: TODO
    :output Runtime_Acceptance_<run_ID>.pdf: TODO

.. script:: txt_for_MCMC.py

    prepares for MCMC TODO

    :usage:

    .. include:: /snippets/txt_for_MCMC.rst

    :arg <area_type>: type of area TODO
    :arg <area_list>: list of areas TODO
    :arg <area_name>: name of area TODO
    :input ED_data.csv: TODO
    :input Constituency_data.csv: TODO
    :output GUID.txt: TODO
    :output Population.txt: TODO
    :output Neighbours.txt: TODO
    :output County.txt: TODO
    :output actual.csv: TODO
    :output Population.pdf: TODO
    :output Area.pdf: TODO
    :output Perimeter.pdf: TODO
    :output Neighbours.pdf: TODO


C++ scripts ``src/*.cpp``
-------------------------

.. script:: actual_H.cpp

    actual Hamiltonian script TODO

    :usage:

    .. include:: /snippets/actual_H.rst

    :arg <area_name>: name of area TODO
    :input actual.csv: TODO
    :input Population.txt: TODO
    :input Neighbours.txt: TODO
    :input County.txt: TODO
    :output actual.csv: TODO

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
    :input Population.txt: TODO
    :input Neighbours.txt: TODO
    :input County.txt: TODO
    :output <seat_makeup>_<coupling_constants>_<run_ID>.csv: TODO


Shell scripts ``code/*.sh``
---------------------------

.. script:: Pareto.sh

    Slurm script for Pareto analysis TODO (maybe only list inputs and outputs needed for plotting?)

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
    :conf integer threads: see :envvar:`OMP_NUM_THREADS` TODO
    :env SEED: TODO
    :input F1060\*.csv: see :script:`combine_data.py` TODO
    :input \*100m\*.geojson: see :script:`combine_data.py` TODO
    :output ED_data.csv: see :script:`combine_data.py` TODO
    :output Constituency_data.csv: see :script:`combine_data.py` TODO
    :output GUID.txt: see :script:`txt_for_MCMC.py` TODO
    :output Population.txt: see :script:`txt_for_MCMC.py` TODO
    :output Neighbours.txt: see :script:`txt_for_MCMC.py` TODO
    :output County.txt: see :script:`txt_for_MCMC.py` TODO
    :output actual.csv: see :script:`txt_for_MCMC.py`, :script:`actual_H.cpp` TODO
    :output Population.pdf: see :script:`txt_for_MCMC.py` TODO
    :output Area.pdf: see :script:`txt_for_MCMC.py` TODO
    :output Perimeter.pdf: see :script:`txt_for_MCMC.py` TODO
    :output Neighbours.pdf: see :script:`txt_for_MCMC.py` TODO
    :output <seat_makeup>_<coupling_constants>_<run_ID>.csv: see :script:`MCMC_SA.cpp` TODO (multiple)


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

    makes :datafile:`ED_data.csv`, see :script:`combine_data.py` TODO

    :dependency container: TODO

.. maketarget:: prepare

    prepare the text files, see :script:`txt_for_MCMC.py` TODO

    :dependency ED_data: TODO


Input files
-----------

.. datafile:: *100m*.geojson

    ED geographical data TODO

    :directory: ``data/``
    :source: `webpage <https://data.gov.ie/dataset/cso-electoral-divisions-national-statistical-boundaries-2022-generalised-100m>`_ TODO
    :usedby combine_data.py: TODO
    :usedby plot_config.py: TODO

.. datafile:: Counties*.geojson

    county geographical data TODO

    :directory: ``data/``
    :source: `webpage <https://data.gov.ie/dataset/counties-national-statutory-boundaries-2019-generalised-20m>`_ TODO
    :usedby plot_config.py: TODO

.. datafile:: F1060*.csv

    population data TODO

    :directory: ``data/``
    :source: `webpage <https://data.cso.ie/table/F1060>`_ TODO
    :usedby combine_data.py: TODO


Generated files
---------------

.. datafile:: Constituency_data.csv

    2023 constituency seats TODO

    :directory: ``data/``
    :source: :script:`combine_data.py` TODO
    :usedby txt_for_MCMC.py: TODO

.. datafile:: ED_data.csv

    electoral division data required for cothrom framework TODO

    :directory: ``data/``
    :source: :script:`combine_data.py` TODO
    :usedby txt_for_MCMC.py: TODO

.. datafile:: actual.csv

    2023 constituency configuration TODO

    :directory: ``data/<area_name>/``
    :source: :script:`txt_for_MCMC.py` and :script:`actual_H.cpp` TODO
    :usedby plot_config.py: TODO
    :usedby plot_Pareto.py: TODO

.. datafile:: Area.pdf

    histograms of electoral division areas TODO

    :directory: ``data/<area_name>/``
    :source: :script:`txt_for_MCMC.py` TODO

.. datafile:: County.txt

    list of electoral division counties TODO

    :directory: ``data/<area_name>/``
    :source: :script:`txt_for_MCMC.py` TODO
    :usedby actual_H.cpp: TODO
    :usedby MCMC_SA.cpp: TODO

.. datafile:: GUID.txt

    list of electoral division GUIDs TODO

    :directory: ``data/<area_name>/``
    :source: :script:`txt_for_MCMC.py` TODO
    :usedby plot_config.py: TODO

.. datafile:: Neighbours.pdf

    histograms of number of electoral division neighbours TODO

    :directory: ``data/<area_name>/``
    :source: :script:`txt_for_MCMC.py` TODO

.. datafile:: Neighbours.txt

    list of number of electoral division neighbours TODO

    :directory: ``data/<area_name>/``
    :source: :script:`txt_for_MCMC.py` TODO
    :usedby actual_H.cpp: TODO
    :usedby MCMC_SA.cpp: TODO

.. datafile:: Perimeter.pdf

    histograms of electoral division perimeters TODO

    :directory: ``data/<area_name>/``
    :source: :script:`txt_for_MCMC.py` TODO

.. datafile:: Population.pdf

    histograms of electoral division populations TODO

    :directory: ``data/<area_name>/``
    :source: :script:`txt_for_MCMC.py` TODO

.. datafile:: Population.txt

    list of electoral division populations TODO

    :directory: ``data/<area_name>/``
    :source: :script:`txt_for_MCMC.py` TODO
    :usedby actual_H.cpp: TODO
    :usedby MCMC_SA.cpp: TODO
    :usedby plot_config.py: TODO

.. datafile:: <seat_makeup>_<coupling_constants>_<run_ID>.csv

    algorithm output TODO

    :directory: ``data/<area_name>/<seats>_<constituencies>/``
    :source: :script:`MCMC_SA.cpp` TODO
    :usedby plot_config.py: TODO
    :usedby plot_Pareto.py: TODO
    :usedby plot_stats.py: TODO

.. datafile:: Configurations_<run_ID>.pdf

    plots of initial and optimal (or actual) configurations TODO

    :directory: ``data/<area_name>/<seats>_<constituencies>/``
    :source: :script:`plot_config.py` TODO

.. datafile:: Objectives_per_observable_<run_ID>.pdf

    plots of each objective per observable TODO

    :directory: ``data/<area_name>/<seats>_<constituencies>/``
    :source: :script:`plot_stats.py` TODO

.. datafile:: Observables_per_objective_<run_ID>.pdf

    plots of each observable per objective TODO

    :directory: ``data/<area_name>/<seats>_<constituencies>/``
    :source: :script:`plot_stats.py` TODO

.. datafile:: Pareto.pdf

    plots of Pareto fronts TODO

    :directory: ``data/<area_name>/<seats>_<constituencies>/``
    :source: :script:`plot_Pareto.py` TODO

.. datafile:: Runtime_Acceptance_<run_ID>.pdf

    plots of runtimes and acceptance rates TODO

    :directory: ``data/<area_name>/<seats>_<constituencies>/``
    :source: :script:`plot_stats.py` TODO
