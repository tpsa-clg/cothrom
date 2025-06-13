CC = g++

ED_data.csv: combine_data.py
	python3 combine_data.py

%.o: %.c %.h
	${CC} $< -c

MCMC_SA: MCMC_SA.cpp Map.o statfuncs.o
	${CC} MCMC_SA.cpp Map.o statfuncs.o -o MCMC_SA -lm -fopenmp

.PHONY: clean
clean:
	rm -f MCMC_SA *.o