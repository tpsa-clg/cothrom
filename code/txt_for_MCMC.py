import numpy as np
import pandas as pd
import sys
import os
import matplotlib.pyplot as plt


# Area from command line
area_type = sys.argv[1]
area_list = sys.argv[2].split(",")
area_name = sys.argv[3]


# Reading required data
data_dir = os.path.join(*[os.path.dirname(os.path.realpath(__file__)), os.pardir, "data"])
full_df = pd.read_csv(
    os.path.join(data_dir, "ED_data.csv"),
    usecols=["GUID", area_type, "Population", "Neighbours", "County", "Area", "Perimeter", "Constituency"],
    converters={"Neighbours": eval})
area_df = full_df[full_df[area_type].isin(area_list)].reset_index(drop=True)
intersect = set(area_df.GUID.values)
area_df.loc[:, "Neighbours"] = np.array([neighbours & intersect for neighbours in area_df.Neighbours.values],
                                        dtype=object)
area_df.loc[:, "Neighbours"] = np.array(
    [area_df.index[area_df["GUID"].isin(neighbours)].tolist() for neighbours in area_df.Neighbours.values],
    dtype=object)
area_df.replace({"County": {county: c for c, county in enumerate(area_df.County.unique())}}, inplace=True)


# Saving .txt files
area_dir = os.path.join(data_dir, area_name)
os.makedirs(area_dir, exist_ok=True)
files = [open(os.path.join(area_dir, f"{column}.txt"), "w")
         for column in ["GUID", "Population", "Neighbours", "County"]]
for guid, population, neighbours, county in zip(area_df.GUID.values,
                                                area_df.Population.values,
                                                area_df.Neighbours.values,
                                                area_df.County.values):
    files[0].write(f"{guid}\n")
    files[1].write(f"{population}\n")
    for i in neighbours:
        files[2].write(f"{i} ")
    files[2].write("\n")
    files[3].write(f"{county}\n")
for file in files:
    file.close()


# Making csv for actual configuration
constituency_list = set(area_df.Constituency.values)
constituency_df = pd.read_csv(os.path.join(data_dir, "Constituency_data.csv"))
constituency_df = constituency_df[constituency_df["Constituency"].isin(constituency_list)]
constituency_df.sort_values("Seats", inplace=True)
constituency_df.reset_index(drop=True, inplace=True)
constituency_list, seat_list = constituency_df.Constituency, constituency_df.Seats
area_df["Configuration"] = -1
for q, constituency in enumerate(constituency_list):
    area_df.loc[area_df.Constituency==constituency, "Configuration"] = q
with open(os.path.join(area_dir, "actual.csv"), "w") as f:
    f.write(f"Q,{','.join([str(seat) for seat in seat_list])}\n")
    f.write(f"{','.join([str(q) for q in area_df['Configuration']])}\n")


# Comparing distributions of ED population, area, perimeter, and neighbours between area of consideration and Ireland
colours = ["#004488", "#BB5566", "#DDAA33"]
names = ["Ireland", area_name]
for column in ["Population", "Area", "Perimeter"]:
    fig, ax = plt.subplots()
    axes = [ax, ax.twinx()]
    for d, (data, a) in enumerate(zip([full_df[column].values, area_df[column].values], axes)):
        hist, bins = np.histogram(data, bins=np.geomspace(min(data), max(data),
                                                          num=int(np.ceil(np.sqrt(len(data))))))
        a.hist(data, bins=bins, color=colours[d], alpha=.75, label=names[d])
    ax.set_xscale("log")
    fig.legend(bbox_to_anchor=(1,1), bbox_transform=ax.transAxes)
    ax.set_title(column)
    fig.savefig(os.path.join(area_dir, f"{column}.pdf"), bbox_inches="tight")
    plt.close(fig)
    del fig, ax

fig, ax = plt.subplots()
nei_lens = [[len(neighbours) for neighbours in df.Neighbours.values] for df in [full_df, area_df]]
bins = np.arange(1, max(nei_lens[0])+2, 1)
for d, (data, a) in enumerate(zip(nei_lens, [ax, ax.twinx()])):
    a.hist(data, bins=bins, color=colours[d], alpha=.75, label=names[d])
fig.legend(bbox_to_anchor=(1,1), bbox_transform=ax.transAxes)
ax.set_title("Neighbours")
fig.savefig(os.path.join(area_dir, "Neighbours.pdf"), bbox_inches="tight")
plt.close("all")
del fig, ax
