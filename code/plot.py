import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import sys
import os


# Data parameters
area_name = sys.argv[1]
data_dir = os.path.join(*[os.path.dirname(os.path.realpath(__file__)), os.pardir, "data"])
area_dir = os.path.join(data_dir, area_name)

# Loading .geojson map, sorting by same index used in C++ code
config_data = gpd.read_file(os.path.join(data_dir, "100m.geojson"))[["ED_GUID", "geometry"]].rename(columns={"ED_GUID": "GUID"})
GUIDs = np.loadtxt(os.path.join(area_dir, "GUID.txt"), dtype="str")
config_data = config_data[config_data.GUID.isin(GUIDs)].set_index("GUID").reindex(index=GUIDs).reset_index()

# Reading & plotting initial & final configurations
config_file = os.path.join(area_dir, "configs.csv")
with open(config_file) as f:
    for _ in range(3):
        next(f)
    config_data["Initial"], config_data["Final"] = ([int(q.replace("\n", "")) for q in f.readline().split(",")[1:]] for _ in range(2))
for state in ["Initial", "Final"]:
    config_data.explore(column=state).save(os.path.join(area_dir, f"{state}.html"))
del config_data

# Reading & plotting MCMC SA data (measurements vs temperature)
MCMC_data = pd.read_csv(config_file, skiprows=5)
MCMC_data["beta"] = 1. / MCMC_data["T"]
H_subs = ["P", "C", "D", ""]
Hs = [rf"$H_{sub}$" for sub in H_subs[:-1]] + [r"$H$"]
for sub, H in zip(H_subs, Hs):
    plt.errorbar(MCMC_data.beta, MCMC_data[f"H{sub}"]/MCMC_data[f"H{sub}"][0], yerr=MCMC_data[f"H{sub}_err"]/MCMC_data[f"H{sub}"][0], label=H)
plt.xscale("log")
plt.xlim(MCMC_data.beta.iloc[0], MCMC_data.beta.iloc[-1])
plt.legend(loc="lower left")
plt.savefig(os.path.join(area_dir, "H vs β.pdf"))
# TODO repeat above for autocorrelations, specific heats

# TODO loop over a bunch of MCMC SA results
