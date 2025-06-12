ED_data.csv: combine_data.py
	python3 combine_data.py

MCMC_SA:
	g++ MCMC_SA.cpp -o MCMC_SA -lm -fopenmp

clean:
	rm MCMC_SA