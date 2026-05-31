import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf as mpdf
import matplotlib.patches as mpatches
import sys
import os
from glob import glob


# Directories, config file ID
area_name = sys.argv[1]
data_dir = os.path.join(*[os.path.dirname(os.path.realpath(__file__)), os.pardir, "data"])
area_dir = os.path.join(data_dir, area_name)
config_id = sys.argv[2]

# Splitting geographical data into area of consideration and surroundings
config_gdf = gpd.read_file(os.path.join(data_dir, "100m.geojson"))[["ED_GUID", "geometry"]].rename(columns={"ED_GUID": "GUID"})
GUIDs = list(np.loadtxt(os.path.join(area_dir, "GUID.txt"), dtype="str"))
surround_gdf = config_gdf[~config_gdf.GUID.isin(GUIDs)]
config_gdf = config_gdf.set_index("GUID").loc[GUIDs].reset_index()

# Reading configuration data
config_file = glob(os.path.join(area_dir, f"**/*{config_id}*.csv"), recursive=True)
if len(config_file) > 1:
    raise ValueError(f"Multiple existing files with ID {config_id}")
config_file = config_file[0]
actual = "actual.csv" in config_file
config_dir = os.path.dirname(config_file)
optimal_Hs = []
with open(config_file) as f:
    seat_config = [int(s) for s in f.readline().replace("\n", "").split(",")[1:]]
    if not actual:
        next(f)
        couplings = [float(j) for j in f.readline().replace("\n", "").split(",")[1:]]
        norms = [float(z) for z in f.readline().replace("\n", "").split(",")[1:]]
        next(f)
        config_gdf["Initial"] = [int(q) for q in f.readline().replace("\n", "").split(",")]
        next(f)
    degeneracy = 0
    line = f.readline().replace("\n", "").split(",")
    while line and line[0] == "H":
        degeneracy += 1
        optimal_Hs.append([float(H) for H in line[1:]])
        config_gdf["Actual" if actual else f"Optimal {degeneracy}"] = [int(q) for q in f.readline().replace("\n", "").split(",")]
        line = f.readline().replace("\n", "").split(",")
Q = len(seat_config)
configs = ["Actual"] if actual else ["Initial"] + [f"Optimal {config}" for config in range(1, degeneracy+1)]

# Loading populations, getting population variances
config_gdf["Population"] = np.loadtxt(os.path.join(area_dir, "Population.txt"), dtype="int")
pop_per_seat = np.sum(config_gdf.Population) / np.sum(seat_config)
variance_dict = {config: [np.sum(config_gdf[config_gdf[config]==q].Population.values) / (seat_config[q]*pop_per_seat) - 1. for q in range(Q)] for config in configs}

# Plotting optimal configurations
# TODO remove surrounding data outside of frame
cmap = plt.get_cmap("viridis")
norm = plt.Normalize(0, Q-1)
county_gdf = gpd.read_file(os.path.join(data_dir, "Counties.geojson"))
pdf = mpdf.PdfPages(os.path.join(config_dir, f"Configurations_{config_id}.pdf"))
for config in configs:
    fig, ax = plt.subplots()
    config_gdf.plot(ax=ax, column=config, cmap=cmap)
    ax.set_xlim(ax.get_xlim())
    ax.set_ylim(ax.get_ylim())
    surround_gdf.plot(ax=ax, color="lightgrey")
    county_gdf.boundary.plot(ax=ax, color="k")
    handles = [mpatches.Patch(facecolor=cmap(norm(q)), edgecolor="k", label=f"$m={seat_config[q]}$, $v_{q} = {variance_dict[config][q]*100:.2f}\\%$") for q in range(Q)]
    ax.legend(handles=handles, fontsize="x-small", framealpha=0.9)
    ax.set_axis_off()
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)
pdf.close()
