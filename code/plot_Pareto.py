import matplotlib.pyplot as plt
import sys
import os
from glob import glob


# Area name, number of seats, number of constituencies
area = sys.argv[1]
seats = int(sys.argv[2])
constituencies = int(sys.argv[3])

# Directories
data_dir = os.path.join(*[os.path.dirname(os.path.realpath(__file__)), os.pardir, "data"])
area_dir = os.path.join(data_dir, area)
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
            # TODO save non-contiguous points, make transparent
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
    Pareto_tuples[seat_config] = optimal_tuples[seat_config].copy()
    for i, this_tuple in enumerate(optimal_tuples[seat_config]):
        if Pareto_tuples[seat_config][i] is None:
            continue
        for j, that_tuple in enumerate(Pareto_tuples[seat_config][i+1:], i+1):
            if that_tuple is None:
                continue
            if this_tuple[0] <= that_tuple[0] and this_tuple[1] <= that_tuple[1]:
                Pareto_tuples[seat_config][j] = None
            elif this_tuple[0] >= that_tuple[0] and this_tuple[1] >= that_tuple[1]:
                Pareto_tuples[seat_config][i] = None
                break
    Pareto_tuples[seat_config] = [Pareto_tuple for Pareto_tuple in Pareto_tuples[seat_config] if Pareto_tuple is not None]

# Getting Pareto front across all seat configurations
Pareto_tuples["all"] = {seat_config: Pareto_tuples[seat_config].copy() for seat_config in seat_configs}
for a, this_config in enumerate(seat_configs):
    for i, this_tuple in enumerate(Pareto_tuples[this_config]):
        if Pareto_tuples["all"][this_config][i] is None:
            continue
        for b, that_config in enumerate(seat_configs[a+1:], a+1):
            for j, that_tuple in enumerate(Pareto_tuples["all"][that_config]):
                if that_tuple is None:
                    continue
                if this_tuple[0] <= that_tuple[0] and this_tuple[1] <= that_tuple[1]:
                    Pareto_tuples["all"][that_config][j] = None
                elif this_tuple[0] >= that_tuple[0] and this_tuple[1] >= that_tuple[1]:
                    Pareto_tuples["all"][this_config][i] = None
                    break
            if Pareto_tuples["all"][this_config][i] is None:
                break
Pareto_tuples["all"] = [Pareto_tuple for seat_config in seat_configs for Pareto_tuple in Pareto_tuples["all"][seat_config] if Pareto_tuple is not None]

# Ordering Pareto front points
Pareto_fronts = seat_configs + ["all"] if len(seat_configs) > 1 else seat_configs
for Pareto_front in Pareto_fronts:
    Pareto_tuples[Pareto_front] = sorted(Pareto_tuples[Pareto_front], key=lambda Pareto_front: Pareto_front[0])

# Population vs compactness scatterplot, Pareto fronts
colours = ["#004488", "#BB5566", "#DDAA33", "k"]
colour_dict = {Pareto_front: colour for Pareto_front, colour in zip(Pareto_fronts, colours)}
if actual_tuple:
    plt.scatter(actual_tuple[0], actual_tuple[1], marker="*", color=colour_dict[actual_seat_config])
for seat_config in seat_configs:
    optimal_xs, optimal_ys = ([optimal[z] for optimal in optimal_tuples[seat_config]] for z in range(2))
    plt.scatter(optimal_xs, optimal_ys, marker=".", color=colour_dict[seat_config], label=seat_config)
plt.xlabel(r"$H_P$")
plt.xscale("log")
plt.ylabel(r"$H_D$")
xlim, ylim = plt.gca().get_xlim(), plt.gca().get_ylim()
plt.xlim(xlim)
plt.ylim(ylim)
for Pareto_front in Pareto_fronts:
    Pareto_tuples[Pareto_front] = [(Pareto_tuples[Pareto_front][0][0], ylim[1])] + Pareto_tuples[Pareto_front] + [(xlim[1], Pareto_tuples[Pareto_front][-1][1])]
    Pareto_xs, Pareto_ys = ([Pareto_tuple[z] for Pareto_tuple in Pareto_tuples[Pareto_front]] for z in range(2))
    plt.plot(Pareto_xs, Pareto_ys, marker="", color=colour_dict[Pareto_front], linestyle="dashed" if Pareto_front == "all" else "solid", alpha=.5, zorder=.5)
plt.legend()
# TODO label/identify front points
plt.savefig(os.path.join(Pareto_dir, "Pareto.pdf"), bbox_inches="tight")
