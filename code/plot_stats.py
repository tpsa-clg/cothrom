import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf as mpdf
import sys
import os
from glob import glob


# Area name, configuration ID
area_name = sys.argv[1]
config_id = sys.argv[2]

# Directories
data_dir = os.path.join(*[os.path.dirname(os.path.realpath(__file__)), os.pardir, "data"])
area_dir = os.path.join(data_dir, area_name)

# Getting metadata
config_file = glob(os.path.join(area_dir, f"**/*{config_id}*.csv"), recursive=True)
if len(config_file) == 0:
    raise FileNotFoundError(f"No configuration file found with ID {config_id}.")
if len(config_file) > 1:
    raise ValueError(f"Multiple existing configuration files with ID {config_id}.")
config_file = config_file[0]
config_dir = os.path.dirname(config_file)
with open(config_file) as f:
    next(f)
    N = int(f.readline().split(",")[1])
    couplings = [float(j) for j in f.readline().replace("\n", "").split(",")[1:]]
    norms = [float(z) for z in f.readline().replace("\n", "").split(",")[1:]]
    next(f)
    EDs = len(f.readline().replace("\n", "").split(","))
    next(f)
    degeneracy = 0
    line = f.readline().replace("\n", "").split(",")
    while line[0] == "H":
        degeneracy += 1
        next(f)
        line = f.readline().replace("\n", "").split(",")

# Loading and re-organising MCMCSA data
MCMC_data = pd.read_csv(config_file, skiprows=7+2*degeneracy)
temps = MCMC_data["T"].values
runtimes = MCMC_data["time"].values / 1000.
accepts_per_sweep, accepts_per_sweep_err = (MCMC_data[f"acc{subkey}"].values for subkey in ["", "_err"])
betas = np.array(1. / temps)
objectives = ["Combination",
              "Population",
              "Contiguity",
              "Compactness",
              "Counties"]
obj_dict = {objective: {
    "csv_tag": tag,
    "normalisation": normalisation,
    "LaTeX": LaTeX,
    "colour": colour,
    "marker": "s" if objective == "Combination" else "."
    } for objective, tag, normalisation, LaTeX, colour in zip(
        objectives,
        [f"H{sub}" for sub in ["", "P", "C", "D", "B"]],
        [sum(couplings)] + norms,
        [r"{}", "P", "C", "D", "B"],
        ["k", "#7B3294", "#008837", "#C2A5CF", "#A6DBA0"])}
if norms[3] == 0:
    objectives.remove("Counties")
observables = ["Energy",
               "Heat Capacity",
               "Autocorrelation Time"]
data_dict = {objective: {
    "Energy": {
        "estimate": MCMC_data[f"{obj_dict[objective]['csv_tag']}"].values / obj_dict[objective]["normalisation"],
        "error": MCMC_data[f"{obj_dict[objective]['csv_tag']}_err"].values / obj_dict[objective]["normalisation"],
        "label": rf"$E_{obj_dict[objective]['LaTeX']}$"},
    "Heat Capacity": {
        "estimate": MCMC_data[f"{obj_dict[objective]['csv_tag']}_var"].values * (betas / obj_dict[objective]["normalisation"])**2,
        "error": MCMC_data[f"{obj_dict[objective]['csv_tag']}_var_err"].values * (betas / obj_dict[objective]["normalisation"])**2,
        "label": rf"$C_{obj_dict[objective]['LaTeX']}$"},
    "Autocorrelation Time": {
        "estimate": MCMC_data[f"{obj_dict[objective]['csv_tag']}_tau"].values,
        "error": MCMC_data[f"{obj_dict[objective]['csv_tag']}_tau_err"].values,
        "label": rf"$\tau_{{E_{obj_dict[objective]['LaTeX']}}}$"}
        } for objective in objectives}
del MCMC_data

# Plotting objectives (combination, population, contiguity, compactness, counties) for each observable (energy/expectation value, heat capacity/variance*beta**2, autocorrelation time)
pdf = mpdf.PdfPages(os.path.join(config_dir, f"Objectives_per_observable_{config_id}.pdf"))
for observable in observables:
    fig, ax = plt.subplots()
    ax.set_xscale("log")
    ax.set_xlim(betas[0], betas[-1])
    ax.set_xlabel(r"$\beta$")
    secax = ax.secondary_xaxis("top", functions=(lambda beta: 1. / beta, lambda T: 1. / T))
    secax.set_xlabel(r"$T$")
    if observable == "Autocorrelation Time":
        ax.set_yscale("log")
    ax.plot([
        min([min(data_dict[objective][observable]["estimate"]) for objective in objectives]),
        max([max(data_dict[objective][observable]["estimate"] + data_dict[objective][observable]["error"]) for objective in objectives])
        ], linestyle="", marker="", alpha=0.)
    ax.set_ylim(ax.get_ylim())
    for objective in objectives:
        if [err for err in data_dict[objective][observable]["error"] if err == err]:
            _, __, bars = ax.errorbar(
                betas, data_dict[objective][observable]["estimate"], yerr=data_dict[objective][observable]["error"],
                color=obj_dict[objective]["colour"], linestyle="", marker=".", label=data_dict[objective][observable]["label"])
        else:
            ax.scatter(
                betas, data_dict[objective][observable]["estimate"],
                marker=".", label=data_dict[objective][observable]["label"])
    ax.legend()
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)
pdf.close()

# Plotting observables (combination, population, contiguity, compactness, counties) for each objective (energy/expectation value, heat capacity/variance*beta**2, autocorrelation time)
obs_colours = ["#004488", "#BB5566", "#DDAA33"]
pdf = mpdf.PdfPages(os.path.join(config_dir, f"Observables_per_objective_{config_id}.pdf"))
for objective in objectives:
    fig, ax = plt.subplots(len(observables), 1, figsize=(8, 4*len(observables)), sharex=True)
    ax[-1].set_xscale("log")
    ax[-1].set_xlim(betas[0], betas[-1])
    ax[-1].set_xlabel(r"$\beta$")
    secax = []
    for i, observable in enumerate(observables):
        secax.append(ax[i].secondary_xaxis(
            "top", functions=(lambda beta: 1. / beta, lambda T: 1. / T)))
        if observable == "Autocorrelation Time":
            ax[i].set_yscale("log")
            ax[i].plot([
                min(data_dict[objective][observable]["estimate"]),
                max(data_dict[objective][observable]["estimate"] + data_dict[objective][observable]["error"])
                ], linestyle="", marker="", alpha=0.)
            ax[i].set_ylim(ax[i].get_ylim())
        ax[i].set_ylabel(observable)
        ax[i].yaxis.label.set_color(obs_colours[i])
        if [err for err in data_dict[objective][observable]["error"] if err == err]:
            _, __, bars = ax[i].errorbar(
                betas, data_dict[objective][observable]["estimate"], yerr=data_dict[objective][observable]["error"],
                color=obs_colours[i], linestyle="", marker=".", label=data_dict[objective][observable]["label"])
        else:
            ax[i].scatter(
                betas, data_dict[objective][observable]["estimate"],
                color=obs_colours[i], marker=".", label=data_dict[objective][observable]["label"])
        ax[i].legend()
    secax[0].set_xlabel(r"$T$")
    for i in range(1, len(observables)):
        secax[i].set_xticks([])
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)
pdf.close()

# Plotting runtime and acceptance rate
pdf = mpdf.PdfPages(os.path.join(config_dir, f"Runtime_Acceptance_{config_id}.pdf"))
for page in range(2):
    fig, ax = plt.subplots(2, 1, sharex=True)
    ax[1].set_xscale("log")
    ax[1].set_xlim(betas[0], betas[-1])
    ax[1].set_xlabel(r"$\beta$")
    secax = []
    for i, colour in enumerate(["r", "b"]):
        ax[i].yaxis.label.set_color(colour)
        secax.append(ax[i].secondary_xaxis("top", functions=(lambda beta: 1. / beta, lambda T: 1. / T)))
    secax[0].set_xlabel(r"$T$")
    secax[1].set_xticks([])
    if page == 0:
        ax[0].set_ylabel("Runtime per sweep, s")
        ax[0].scatter(betas, runtimes,
                      marker=".", color="r", label=r"$t$")
        acceptance_rates, acceptance_rates_err = (arr / EDs for arr in [accepts_per_sweep, accepts_per_sweep_err])
        ax[1].set_ylabel("Acceptance rate per sweep")
        ax[1].errorbar(betas, acceptance_rates, yerr=acceptance_rates_err,
                       linestyle="", marker=".", color="b", label=r"$\langle r\rangle$")
    elif page == 1:
        total_runtimes = np.cumsum(runtimes)
        ax[0].set_ylabel("Total runtime, s")
        ax[0].plot(betas, total_runtimes,
                   color="r", label=r"$t$")
        total_accepted = np.cumsum(N * accepts_per_sweep)
        ax[1].set_ylabel("Total accepted changes")
        ax[1].plot(betas, total_accepted,
                   color="b", label="no. changes")
        # ax.set_ylim(bottom=0.)
        # ax2.set_ylim(bottom=0.)
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)
pdf.close()
