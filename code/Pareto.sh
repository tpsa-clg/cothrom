#!/bin/sh
#SBATCH -N 1
#SBATCH -t 4-00:00:00
#SBATCH -p compute
#SBATCH -J grid

base_dir=/home/users/campioru/Electoral_Redistricting
code_dir=${base_dir}/code
data_dir=${base_dir}/data

cd $base_dir
make ED_data.csv MCMC_SA actual_H
python3 code/txt_for_MCMC.py County CORK "Cork"
mkdir ${data_dir}/Cork/20_5 -p
OMP_SET_NUM_THREADS=1

for JD in $(seq 0 0.1 2.5)
do
  JC=$(bc <<< $JD+1)
  ./MCMC_SA "Cork" 3,3,4,5,5 ${JC},${JD},0 500,100 &
  ./MCMC_SA "Cork" 3,4,4,4,5 ${JC},${JD},0 500,100 &
  ./MCMC_SA "Cork" 4,4,4,4,4 ${JC},${JD},0 500,100 &
done
wait
