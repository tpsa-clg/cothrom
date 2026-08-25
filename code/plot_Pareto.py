import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import sys
import os
from glob import glob
import itertools as it


# Area name, number of seats, number of constituencies
area_name = sys.argv[1]
seats = int(sys.argv[2])
constituencies = int(sys.argv[3])

# Directories
data_dir = os.path.join(*[os.path.dirname(os.path.realpath(__file__)), os.pardir, "data"])
area_dir = os.path.join(data_dir, area_name)
Pareto_dir = os.path.join(area_dir, f"{seats}_{constituencies}")

# Loading configurations and Hamiltonians
config_files = glob(os.path.join(Pareto_dir, "*.csv"))
seat_configs = sorted({config_file.split("/")[-1].split("_")[0] for config_file in config_files})
optimal_tuples = {seat_config: set() for seat_config in seat_configs}
for config_file in config_files:
    with open(config_file) as f:
        line = f.readline().replace("\n", "")
        seat_config = line[2:]
        while line[0] != "optimals":
            line = f.readline().replace("\n", "").split(",")
        line = f.readline().replace("\n", "").split(",")
        while line[0] == "H":
            Hs = [float(H) for H in line[1:]]
            if Hs[1] == 0:
                optimal_tuples[seat_config].add((Hs[0], Hs[2]))
            next(f)
            line = f.readline().replace("\n", "").split(",")

# Loading actual configuration
actual_file = os.path.join(area_dir, "actual.csv")
actual_tuple = tuple()
with open(actual_file) as f:
    line = f.readline().replace("\n", "")
    actual_seat_config = line[2:]
    seat_list = [int(s) for s in line.split(",")[1:]]
    line = f.readline().replace("\n", "").split(",")
    if line[0] == "H" and sum(seat_list) == seats and len(seat_list) == constituencies:
        Hs = [float(H) for H in line[1:]]
        actual_tuple = (Hs[0], Hs[2])

# Getting Pareto front for each seat configuration
Pareto_tuples = {}
for seat_config in seat_configs:
    optimal_tuples[seat_config] = list(optimal_tuples[seat_config])
    Pareto_tuples[seat_config] = {True: optimal_tuples[seat_config].copy(), False: []}
    for i, this_tuple in enumerate(optimal_tuples[seat_config]):
        if Pareto_tuples[seat_config][True][i] is None:
            continue
        for j, that_tuple in enumerate(Pareto_tuples[seat_config][True][i+1:], i+1):
            if that_tuple is None:
                continue
            if this_tuple[0] <= that_tuple[0] and this_tuple[1] <= that_tuple[1]:
                Pareto_tuples[seat_config][True][j] = None
                Pareto_tuples[seat_config][False].append(that_tuple)
            elif this_tuple[0] >= that_tuple[0] and this_tuple[1] >= that_tuple[1]:
                Pareto_tuples[seat_config][True][i] = None
                Pareto_tuples[seat_config][False].append(this_tuple)
                break
    Pareto_tuples[seat_config][True] = [Pareto_tuple for Pareto_tuple in Pareto_tuples[seat_config][True] if Pareto_tuple is not None]

# Ordering Pareto front points
for seat_config in seat_configs:
    Pareto_tuples[seat_config][True] = sorted(Pareto_tuples[seat_config][True], key=lambda Pareto_tuple: Pareto_tuple[0])

# Population vs compactness scatterplot, Pareto fronts
colours = ["#004488", "#BB5566", "#DDAA33"]
linestyles = ["dotted", "dashed", "dashdot"]
plot_dict = {seat_config: {"colour": colour, "linestyle": linestyle} for seat_config, colour, linestyle in zip(seat_configs, colours, linestyles)}
if actual_tuple:
    plt.scatter(actual_tuple[0], actual_tuple[1], marker="*", color=plot_dict[actual_seat_config]["colour"])
for seat_config, front_bool in it.product(seat_configs, [True, False]):
    optimal_xs, optimal_ys = ([optimal[z] for optimal in Pareto_tuples[seat_config][front_bool]] for z in range(2))
    if front_bool:
        plt.step(optimal_xs, optimal_ys, where="post", marker="o", color=plot_dict[seat_config]["colour"], linestyle=plot_dict[seat_config]["linestyle"], label=seat_config)
    else:
        plt.scatter(optimal_xs, optimal_ys, marker=".", color=plot_dict[seat_config]["colour"], alpha=.5, linewidths=0.)
plt.xlabel(r"$H_P$")
plt.xscale("log")
plt.ylabel(r"$H_D$")
xlim, ylim = plt.gca().get_xlim(), plt.gca().get_ylim()
plt.xlim(xlim)
plt.ylim(ylim)
ax = plt.gca()
for seat_config in seat_configs:
    left_point = Pareto_tuples[seat_config][True][0]
    ax.vlines(x=left_point[0], ymin=left_point[1], ymax=ylim[1], color=plot_dict[seat_config]["colour"], linestyle=plot_dict[seat_config]["linestyle"])
    bottom_point = Pareto_tuples[seat_config][True][-1]
    ax.hlines(y=bottom_point[1], xmin=bottom_point[0], xmax=xlim[1], color=plot_dict[seat_config]["colour"], linestyle=plot_dict[seat_config]["linestyle"])
plt.legend(fontsize="small")
# TODO label/identify front points
plt.savefig(os.path.join(Pareto_dir, "Pareto.pdf"), bbox_inches="tight")
