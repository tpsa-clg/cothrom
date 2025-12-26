import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf as mpdf
import sys
import os


# Data parameters
area_name = sys.argv[1]
data_dir = os.path.join(*[os.path.dirname(os.path.realpath(__file__)), os.pardir, "data"])
area_dir = os.path.join(data_dir, area_name)

# Loading .geojson map, sorting by same index used in C++ code
config_data = gpd.read_file(os.path.join(data_dir, "100m.geojson"))[["ED_GUID", "geometry"]].rename(columns={"ED_GUID": "GUID"})
GUIDs = np.loadtxt(os.path.join(area_dir, "GUID.txt"), dtype="str")
EDs = len(GUIDs)
config_data = config_data[config_data.GUID.isin(GUIDs)].set_index("GUID").reindex(index=GUIDs).reset_index()

# Reading & plotting initial & final configurations
degeneracy = 0
config_file = os.path.join(area_dir, "configs.csv")
with open(config_file) as f:
    seats = [int(q.replace("\n", "")) for q in f.readline().split(",")[1:]]
    next(f)
    couplings = [float(j.replace("\n", "")) for j in f.readline().split(",")[1:]]
    norms = [float(z.replace("\n", "")) for z in f.readline().split(",")[1:]]
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

# Loading and re-organising MCMCSA data
MCMC_data = pd.read_csv(config_file, skiprows=7+degeneracy)
betas = np.array(1. / MCMC_data["T"])
runtimes = MCMC_data["time"]
objectives = ["Combination", "Population", "Contiguity", "Compactness", "Counties", "Acceptance Rate"]
obj_dict = {objective: {"csv_tag": tag, "normalisation": normalisation, "LaTeX": LaTeX}
            for objective, tag, normalisation, LaTeX in zip(
                objectives,
                [f"H{sub}" for sub in ["", "P", "C", "D", "B"]] + ["acc"],
                [sum(couplings)] + norms + [EDs],
                [r"{}", "P", "C", "D", "B", r"\alpha"])}
observables = ["Energy", "Heat Capacity", "Autocorrelation Time"]
data_dict = {objective: {
    "Energy": {
        "estimate": MCMC_data[f"{obj_dict[objective]["csv_tag"]}"]/obj_dict[objective]["normalisation"],
        "error": MCMC_data[f"{obj_dict[objective]["csv_tag"]}_err"]/obj_dict[objective]["normalisation"],
        "label": rf"$E_{obj_dict[objective]['LaTeX']}$" if objective != "Acceptance Rate" else rf"$\langle{obj_dict[objective]['LaTeX']}\rangle$"},
    "Heat Capacity": {
        "estimate": MCMC_data[f"{obj_dict[objective]["csv_tag"]}_var"]*(betas/obj_dict[objective]["normalisation"])**2,
        "error": MCMC_data[f"{obj_dict[objective]["csv_tag"]}_var_err"]*(betas/obj_dict[objective]["normalisation"])**2,
        "label": rf"$C_{obj_dict[objective]['LaTeX']}$" if objective != "Acceptance Rate" else rf"$\beta^2\mathrm{{Var}}({obj_dict[objective]['LaTeX']})$"},
    "Autocorrelation Time": {
        "estimate": MCMC_data[f"{obj_dict[objective]["csv_tag"]}_tau"],
        "error": MCMC_data[f"{obj_dict[objective]["csv_tag"]}_tau_err"],
        "label": rf"$\tau_{{H_{obj_dict[objective]['LaTeX']}}}$" if objective != "Acceptance Rate" else rf"$\tau_{obj_dict[objective]['LaTeX']}$"}}
    for objective in objectives}
del MCMC_data

# Plotting objectives (combination, population, contiguity, compactness, counties, acceptance) for each observable (energy/expectation value, heat capacity/variance*beta**2, autocorrelation time)
pdf = mpdf.PdfPages(os.path.join(area_dir, "Objectives per observable.pdf"))
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
            ax.errorbar(betas,
                        data_dict[objective][observable]["estimate"],
                        yerr=data_dict[objective][observable]["error"],
                        label=data_dict[objective][observable]["label"])
        else:
            ax.plot(betas,
                    data_dict[objective][observable]["estimate"],
                    label=data_dict[objective][observable]["label"])
    ax.legend()
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)
pdf.close()

# Plotting observables for each objective (energy/expectation value, heat capacity/variance*beta**2, autocorrelation time)
colours = ["#004488", "#BB5566", "#DDAA33", "k"]
pdf = mpdf.PdfPages(os.path.join(area_dir, "Observables per objective.pdf"))
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
            line = obs_ax.errorbar(betas,
                                   data_dict[objective][observable]["estimate"],
                                   yerr=data_dict[objective][observable]["error"],
                                   color=colours[o],
                                   label=data_dict[objective][observable]["label"])
        else:
            line = obs_ax.plot(betas,
                               data_dict[objective][observable]["estimate"],
                               color=colours[o],
                               label=data_dict[objective][observable]["label"])
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)
pdf.close()

# Plotting runtime
plt.xscale("log")
plt.xlim(betas[0], betas[-1])
plt.xlabel(r"$\beta$")
plt.ylabel("Millieconds")
plt.plot(betas, runtimes)
plt.savefig(os.path.join(area_dir, "runtime vs β.pdf"))
plt.close()

# TODO loop over a bunch of MCMC SA results
