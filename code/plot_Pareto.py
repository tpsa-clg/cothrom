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
# TODO order seat configurations to ensure same behaviour?
seat_configs = {config_file.split("/")[-1].split("_")[0] for config_file in config_files}
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
    if sum(seat_list) == seats and len(seat_list) == constituencies:
        next(f)
        line = f.readline().replace("\n", "").split(",")
        Hs = [float(H) for H in line[1:]]
        actual_tuple = (Hs[0], Hs[2])

# Getting and sorting Pareto front
all_tuples = {optimal_tuple for seat_config in seat_configs for optimal_tuple in optimal_tuples[seat_config]} | {actual_tuple}
Pareto_tuples = set()
for point in all_tuples:
    Pareto_point = True
    for other_point in all_tuples:
        if point[0] > other_point[0] and point[1] > other_point[1]:
            Pareto_point = False
            break
    if Pareto_point:
        Pareto_tuples.add(point)
Pareto_tuples = sorted(Pareto_tuples, key=lambda x: x[0])

# Population vs compactness scatterplot, Pareto front
colours = ["#004488", "#BB5566", "#DDAA33", "k"]
colour_dict = {seat_config: colour for seat_config, colour in zip(seat_configs, colours)}
if actual_tuple:
    plt.scatter(actual_tuple[0], actual_tuple[1], marker="*", color=colour_dict[actual_seat_config])
for seat_config in seat_configs:
    optimal_xs = [optimal[0] for optimal in optimal_tuples[seat_config]]
    optimal_ys = [optimal[1] for optimal in optimal_tuples[seat_config]]
    plt.scatter(optimal_xs, optimal_ys, marker=".", color=colour_dict[seat_config], label=seat_config)
plt.xlabel(r"$H_P$")
plt.xscale("log")
plt.ylabel(r"$H_D$")
xlim, ylim = plt.gca().get_xlim(), plt.gca().get_ylim()
plt.xlim(xlim)
plt.ylim(ylim)
Pareto_tuples = [(Pareto_tuples[0][0], ylim[1])] + Pareto_tuples + [(xlim[1], Pareto_tuples[-1][1])]
Pareto_xs = [Pareto_tuple[0] for Pareto_tuple in Pareto_tuples]
Pareto_ys = [Pareto_tuple[1] for Pareto_tuple in Pareto_tuples]
plt.plot(Pareto_xs, Pareto_ys, marker="", color="lightgrey", zorder=.5)
plt.legend()
# TODO label/identify front points
plt.savefig(os.path.join(Pareto_dir, "Pareto.pdf"), bbox_inches="tight")
