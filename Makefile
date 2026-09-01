# cothrom top-level orchestration.
#
#   make container   build the Singularity image (cothrom.sif) from cothrom.def
#   make ED_data     grab/build the public data set using the container
#                    (depends on the container being built first)
#   make prepare     set up the .txt files for an MCMC_SA run, from the container
#                    (depends on the container + ED_data); takes the area from
#                    the command line, e.g.
#                      make prepare AREA_TYPE=County \
#                                   AREA_LIST=LONGFORD,WESTMEATH,OFFALY,LAOIS \
#                                   AREA_NAME="Midland counties"
#   make cpp         configure + compile the C++ code with CMake into build/
#   make all         container + cpp
#   make clean       remove the build directory, the image, and generated data

# --- container -------------------------------------------------------------
SIF        = cothrom.sif
DEF        = cothrom.def
SINGULARITY = singularity
# bind the repo so scripts in the container can read/write ./data
RUN         = $(SINGULARITY) exec --bind $(CURDIR) $(SIF)

# --- C++ / CMake -----------------------------------------------------------
BUILD_DIR  = build
# override the compiler the standard CMake way, e.g.
#   make cpp CXX=CC          (LUMI Cray wrapper)
#   make cpp CXX=clang++
CMAKE_FLAGS =
ifdef CXX
CMAKE_FLAGS += -DCMAKE_CXX_COMPILER=$(CXX)
endif

.PHONY: all container ED_data prepare cpp clean

all: container cpp

# --- a) build the container ------------------------------------------------
container: $(SIF)

$(SIF): $(DEF) requirements.txt
	# unprivileged proot build (no --fakeroot, no root)
	$(SINGULARITY) build $(SIF) $(DEF)

# --- b) python initialisation (needs the container) ------------------------
ED_data: data/ED_data.csv

data/ED_data.csv: $(SIF) code/combine_data.py
	$(RUN) python code/combine_data.py

# --- c) set up the .txt files for an MCMC_SA run (needs container + data) ---
# Wraps: python code/txt_for_MCMC.py <AREA_TYPE> <AREA_LIST> <AREA_NAME>
# Pass the area on the command line, e.g.
#   make prepare AREA_TYPE=County AREA_LIST=LONGFORD,WESTMEATH,OFFALY,LAOIS \
#                AREA_NAME="Midland counties"
# Quote values containing spaces. 
USAGE_PREPARE = Usage: make prepare AREA_TYPE=<type> AREA_LIST=<csv> AREA_NAME="<name>"
prepare: data/ED_data.csv
	@test -n '$(AREA_TYPE)' || { echo 'AREA_TYPE not set. $(USAGE_PREPARE)'; exit 1; }
	@test -n '$(AREA_LIST)' || { echo 'AREA_LIST not set. $(USAGE_PREPARE)'; exit 1; }
	@test -n '$(AREA_NAME)' || { echo 'AREA_NAME not set. $(USAGE_PREPARE)'; exit 1; }
	$(RUN) python code/txt_for_MCMC.py "$(AREA_TYPE)" "$(AREA_LIST)" "$(AREA_NAME)"

# --- d) C++ build via CMake in build/ --------------------------------------
cpp:
	cmake -S . -B $(BUILD_DIR) $(CMAKE_FLAGS)
	cmake --build $(BUILD_DIR)

clean:
	rm -rf $(BUILD_DIR) $(SIF) data/ED_data.csv data/Constituency_data.csv
