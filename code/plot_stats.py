import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf as mpdf
import sys
import os
from glob import glob


# Directories, config file ID
area_name = sys.argv[1]
data_dir = os.path.join(*[os.path.dirname(os.path.realpath(__file__)), os.pardir, "data"])
area_dir = os.path.join(data_dir, area_name)
config_id = sys.argv[2]

# Loading .geojson map, sorting by same index used in C++ code
config_data = gpd.read_file(os.path.join(data_dir, "100m.geojson"))[["ED_GUID", "geometry"]].rename(columns={"ED_GUID": "GUID"})
GUIDs = np.loadtxt(os.path.join(area_dir, "GUID.txt"), dtype="str")
EDs = len(GUIDs)
config_data = config_data[config_data.GUID.isin(GUIDs)].set_index("GUID").reindex(index=GUIDs).reset_index()

# Reading & plotting initial & final configurations
config_file = glob(os.path.join(area_dir, f"**/*{config_id}*.csv"))[0]
config_dir = os.path.dirname(config_file)
optimal_Hs = []
with open(config_file) as f:
    seats = [int(s) for s in f.readline().replace("\n", "").split(",")[1:]]
    next(f)
    couplings = [float(j) for j in f.readline().replace("\n", "").split(",")[1:]]
    norms = [float(z) for z in f.readline().replace("\n", "").split(",")[1:]]
    next(f)
    config_data["Initial"] = [int(q) for q in f.readline().replace("\n", "").split(",")]
    next(f)
    degeneracy = 0
    optimal_config = f.readline().replace("\n", "").split(",")
    while optimal_config[0] == "H":
        degeneracy += 1
        optimal_Hs.append([float(H) for H in optimal_config[1:]])
        optimal_config = f.readline().replace("\n", "").split(",")
        config_data[f"Optimal {degeneracy}"] = [int(q) for q in optimal_config]
        optimal_config = f.readline().replace("\n", "").split(",")
for state in ["Initial"] + [f"Optimal {d}" for d in range(1, degeneracy+1)]:
    config_data.explore(column=state).save(os.path.join(area_dir, f"{state}.html"))
del config_data

# Loading and re-organising MCMCSA data
MCMC_data = pd.read_csv(config_file, skiprows=7+2*degeneracy)
betas = np.array(1. / MCMC_data["T"])
runtimes = MCMC_data["time"]
objectives = ["Combination", "Population", "Contiguity", "Compactness", "Counties", "Acceptance Rate"]
obj_dict = {objective: {"csv_tag": tag, "normalisation": normalisation, "LaTeX": LaTeX}
            for objective, tag, normalisation, LaTeX in zip(
                objectives,
                [f"H{sub}" for sub in ["", "P", "C", "D", "B"]] + ["acc"],
                [sum(couplings)] + norms + [EDs],
                [r"{}", "P", "C", "D", "B", r"\alpha"])}
if norms[3] == 0:
    objectives.remove("Counties")
    del obj_dict["Counties"]
observables = ["Energy", "Heat Capacity", "Autocorrelation Time"]
data_dict = {objective: {
    "Energy": {
        "estimate": MCMC_data[f"{obj_dict[objective]['csv_tag']}"]/obj_dict[objective]["normalisation"],
        "error": MCMC_data[f"{obj_dict[objective]['csv_tag']}_err"]/obj_dict[objective]["normalisation"],
        "label": rf"$E_{obj_dict[objective]['LaTeX']}$" if objective != "Acceptance Rate" else rf"$\langle{obj_dict[objective]['LaTeX']}\rangle$"},
    "Heat Capacity": {
        "estimate": MCMC_data[f"{obj_dict[objective]['csv_tag']}_var"]*(betas/obj_dict[objective]["normalisation"])**2,
        "error": MCMC_data[f"{obj_dict[objective]['csv_tag']}_var_err"]*(betas/obj_dict[objective]["normalisation"])**2,
        "label": rf"$C_{obj_dict[objective]['LaTeX']}$" if objective != "Acceptance Rate" else rf"$\beta^2\mathrm{{Var}}({obj_dict[objective]['LaTeX']})$"},
    "Autocorrelation Time": {
        "estimate": MCMC_data[f"{obj_dict[objective]['csv_tag']}_tau"],
        "error": MCMC_data[f"{obj_dict[objective]['csv_tag']}_tau_err"],
        "label": rf"$\tau_{{H_{obj_dict[objective]['LaTeX']}}}$" if objective != "Acceptance Rate" else rf"$\tau_{obj_dict[objective]['LaTeX']}$"}}
    for objective in objectives}
del MCMC_data

# Plotting objectives (combination, population, contiguity, compactness, counties, acceptance) for each observable (energy/expectation value, heat capacity/variance*beta**2, autocorrelation time)
pdf = mpdf.PdfPages(os.path.join(config_dir, f"Objectives per observable {config_id}.pdf"))
for observable in observables:
    fig, ax = plt.subplots()
    fig.suptitle(observable)
    ax.set_xscale("log")
    ax.set_xlim(betas[0], betas[-1])
    ax.set_xlabel(r"$\beta$")
    if observable == "Autocorrelation Time":
        ax.set_yscale("log")
    for objective in objectives:
        if [err for err in data_dict[objective][observable]["error"] if err == err]:
            _, __, bars = ax.errorbar(betas,
                                      data_dict[objective][observable]["estimate"],
                                      yerr=data_dict[objective][observable]["error"], linestyle="", marker=".",
                                      label=data_dict[objective][observable]["label"])
            if observable == "Autocorrelation Time":
                for bar in bars:
                    bar.set_alpha(.5)
        else:
            ax.scatter(betas,
                    data_dict[objective][observable]["estimate"], marker=".",
                    label=data_dict[objective][observable]["label"])
    ax.legend()
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)
pdf.close()

# Plotting observables for each objective (energy/expectation value, heat capacity/variance*beta**2, autocorrelation time)
colours = ["#004488", "#BB5566", "#DDAA33", "k"]
pdf = mpdf.PdfPages(os.path.join(config_dir, f"Observables per objective {config_id}.pdf"))
for objective in objectives:
    fig, ax = plt.subplots()
    fig.suptitle(objective)
    ax.set_xscale("log")
    ax.set_xlim(betas[0], betas[-1])
    ax.set_xlabel(r"$\beta$")
    for o, observable in enumerate(observables):
        if o == 0:
            obs_ax = ax
        else:
            obs_ax = ax.twinx()
            if o > 1:
                obs_ax.spines['right'].set_position(('outward', 60))
        obs_ax.set_ylabel(observable)
        obs_ax.yaxis.label.set_color(colours[o])
        if [err for err in data_dict[objective][observable]["error"] if err == err]:
            _, __, bars = obs_ax.errorbar(betas,
                                          data_dict[objective][observable]["estimate"],
                                          yerr=data_dict[objective][observable]["error"],
                                          color=colours[o], linestyle="", marker=".",
                                          label=data_dict[objective][observable]["label"])
            if observable == "Autocorrelation Time":
                for bar in bars:
                    bar.set_alpha(.5)
        else:
            obs_ax.scatter(betas, data_dict[objective][observable]["estimate"], color=colours[o], marker=".", label=data_dict[objective][observable]["label"])
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)
pdf.close()

# Plotting runtime
plt.xscale("log")
plt.xlim(betas[0], betas[-1])
plt.xlabel(r"$\beta$")
plt.ylabel("Milliseconds")
plt.plot(betas, runtimes)
plt.savefig(os.path.join(config_dir, f"runtime vs β {config_id}.pdf"))
plt.close()
