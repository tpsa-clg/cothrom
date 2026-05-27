import matplotlib.pyplot as plt
import sys
import os
from glob import glob

area = sys.argv[1]
seats = int(sys.argv[2])
constituencies = int(sys.argv[3])

data_dir = os.path.join(*[os.path.dirname(os.path.realpath(__file__)), os.pardir, "data"])
area_dir = os.path.join(data_dir, area)
Pareto_dir = os.path.join(area_dir, f"{seats}_{constituencies}")

config_files = glob(os.path.join(Pareto_dir, "*.csv"))
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

colours = ["#004488", "#BB5566", "#DDAA33", "k"]
colour_dict = {seat_config: colour for seat_config, colour in zip(seat_configs, colours)}
# TODO find and mark Pareto front - big markers for front points?
if actual_tuple:
    plt.scatter(actual_tuple[0], actual_tuple[1], marker="*", color=colour_dict[actual_seat_config])
for seat_config in seat_configs:
    optimal_xs = [optimal[0] for optimal in optimal_tuples[seat_config]]
    optimal_ys = [optimal[1] for optimal in optimal_tuples[seat_config]]
    plt.scatter(optimal_xs, optimal_ys, marker=".", color=colour_dict[seat_config], label=seat_config)
plt.xlabel(r"$H_P$")
plt.xscale("log")
plt.ylabel(r"$H_D$")
plt.legend()
# TODO label/identify front points
plt.savefig(os.path.join(Pareto_dir, "Pareto.pdf"), bbox_inches="tight")
