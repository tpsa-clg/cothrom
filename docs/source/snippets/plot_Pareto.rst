.. prompt:: bash $ auto

    # Virtual environment
    $ python code/plot_Pareto.py <area_name> <seats> <constituencies>

    # Singularity container
    $ singularity run --bind ${PWD} cothrom.sif code/plot_Pareto.py <area_name> <seats> <constituencies>
