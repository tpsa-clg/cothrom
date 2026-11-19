.. prompt:: bash $ auto

    # Virtual environment
    $ python code/txt_for_MCMC.py <area_type> <area_list> <area_name>

    # Singularity container
    $ make prepare AREA_TYPE=<area_type> AREA_LIST=<area_list> AREA_NAME=<area_name>	# singularity run cothrom.sif code/txt_for_MCMC.py <area_type> <area_list> <area_name>
