#!/bin/sh

base_dir=/home/users/campioru/Electoral_Redistricting
code_dir=${base_dir}/code
data_dir=${base_dir}/data

area_type=County
area_list=CORK
area_name=Cork

seats=20
constituencies=5
declare -a seat_configs=(3,3,4,5,5 3,4,4,4,5 4,4,4,4,4)

JC_proportion=0.5
declare -a JDs=($(seq 0 0.1 2.5))
declare -a JBs=(0)

N_meas=100
N_disc=50


cd $base_dir
make ED_data.csv MCMC_SA actual_H
source .venv/bin/activate
python3 ${code_dir}/txt_for_MCMC.py $area_type $area_list $area_name
deactivate
mkdir ${data_dir}/${area_name}/${seats}_${constituencies} -p
./actual_H $area_name

for seat_config in ${seat_configs[@]}
do
  for JD in ${JDs[@]}
  do
    for JB in ${JBs[@]}
    do
      JC=$(bc <<< "scale=3; (${JD}+${JB}+1)*${JC_proportion}/(1-${JC_proportion})")
      sbatch -N 1 -t 4-00:00:00 -p compute -J Pareto --wrap="OMP_SET_NUM_THREADS=16; ./MCMC_SA $area_name $seat_config ${JC},${JD},${JB} ${N_meas},${N_disc}"
    done
  done
done
