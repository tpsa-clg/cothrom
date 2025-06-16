CC = g++
DATA_DIR = data
CODE_DIR = code
HEADERS_DIR = headers
VPATH = ${DATA_DIR}:${CODE_DIR}:${HEADERS_DIR}

ED_data.csv: combine_data.py
	python3 $<

%.o: %.cpp %.h
	${CC} $< -c

MCMC_SA: MCMC_SA.cpp Map.o statfuncs.o
	${CC} $^ -I ${HEADERS_DIR} -o $@ -lm -fopenmp

.PHONY: clean
clean:
	rm -f MCMC_SA *.o