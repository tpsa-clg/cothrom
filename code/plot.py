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
degeneracy = 0
config_file = os.path.join(area_dir, "configs.csv")
with open(config_file) as f:
    for _ in range(4):
        next(f)
    config_data["Initial"] = [int(q.replace("\n", "")) for q in f.readline().split(",")]
    next(f)
    optimal_config = f.readline().split(",")
    while optimal_config[0] != "T":
        degeneracy += 1
        config_data[f"Optimal {degeneracy}"] = [int(q.replace("\n", "")) for q in optimal_config]
        optimal_config = f.readline().split(",")
for state in ["Initial"] + [f"Optimal {d}" for d in range(1, degeneracy+1)]:
    config_data.explore(column=state).save(os.path.join(area_dir, f"{state}.html"))
del config_data

# Reading & plotting MCMC SA data (measurements vs temperature)
MCMC_data = pd.read_csv(config_file, skiprows=6+degeneracy)
MCMC_data["beta"] = 1. / MCMC_data["T"]
subs = ["P", "C", "D", "B", ""]

# TODO make this a function instead of repeating
Hs = [rf"$H_{sub}$" for sub in subs[:-1]] + [r"$H$"]
for sub, H in zip(subs, Hs):
    if [err for err in MCMC_data[f"H{sub}_err"] if err == err]:
        plt.errorbar(MCMC_data.beta, MCMC_data[f"H{sub}"]/MCMC_data[f"H{sub}"][0], yerr=MCMC_data[f"H{sub}_err"]/MCMC_data[f"H{sub}"][0], label=H)
    else:
        plt.plot(MCMC_data.beta, MCMC_data.beta, MCMC_data[f"H{sub}"]/MCMC_data[f"H{sub}"][0], label=H)
plt.xscale("log")
plt.xlim(MCMC_data.beta.iloc[0], MCMC_data.beta.iloc[-1])
plt.legend(loc="lower left")
plt.savefig(os.path.join(area_dir, "H vs β.pdf"))
plt.close()

taus = [rf"$\tau_{sub}$" for sub in subs[:-1]] + [r"$\tau$"]
for sub, tau in zip(subs, taus):
    if [err for err in MCMC_data[f"H{sub}_tau_err"] if err == err]:
        plt.errorbar(MCMC_data.beta, MCMC_data[f"H{sub}_tau"], yerr=MCMC_data[f"H{sub}_tau_err"], label=tau)
plt.xscale("log")
plt.yscale("log")
plt.xlim(MCMC_data.beta.iloc[0], MCMC_data.beta.iloc[-1])
plt.legend(loc="upper left")
plt.savefig(os.path.join(area_dir, "τ vs β.pdf"))

# TODO loop over a bunch of MCMC SA results
