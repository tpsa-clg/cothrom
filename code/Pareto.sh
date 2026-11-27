#!/bin/sh

rel_dir="$(dirname "$0")/.."
cd ${rel_dir}
base_dir=$(pwd)
code_dir=${base_dir}/code
data_dir=${base_dir}/data

area_type=County
area_list=CORK
area_name=Cork

declare -a seat_configs=(3,3,4,5,5 3,4,4,4,5 4,4,4,4,4)

JC_proportion=0.5
declare -a JDs=($(seq 0 0.1 2.5))
declare -a JBs=(0)

N_meas=100
N_disc=50

threads=16


make ED_data cpp
make prepare AREA_TYPE=${area_type} AREA_LIST=${area_list} AREA_NAME=${area_name}
./actual_H ${area_name}

for seat_config in ${seat_configs[@]}
do
  for JD in ${JDs[@]}
  do
    for JB in ${JBs[@]}
    do
      JC=$(bc <<< "scale=3; (${JD}+${JB}+1)*${JC_proportion}/(1-${JC_proportion})")
      sbatch -N 1 -t 4-00:00:00 -p compute -J Pareto --wrap="OMP_NUM_THREADS=${threads}; ./build/MCMC_SA ${area_name} ${seat_config} ${JC},${JD},${JB} ${N_meas},${N_disc}"
    done
  done
done
