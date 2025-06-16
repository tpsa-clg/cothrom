import numpy as np
import pandas as pd
import sys
import os


# Area from command line
area_type = sys.argv[1]
area_list = sys.argv[2].split(",")
area_name = sys.argv[3]


# Reading required data
data_dir = os.path.join(*[os.path.dirname(os.path.realpath(__file__)), os.pardir, "data"])
area_df = pd.read_csv(os.path.join(data_dir, "ED_data.csv"), usecols=["GUID", area_type, "Population", "Neighbours"])
area_df = area_df[area_df[area_type].isin(area_list)].sort_values(by="GUID").reset_index(drop=True)
intersect = set(area_df.GUID.values)
area_df.loc[:, "Neighbours"] = np.array([eval(i) & intersect for i in area_df.Neighbours.values], dtype=object)
area_df.loc[:, "Neighbours"] = np.array([area_df.index[area_df["GUID"].isin(i)].tolist() for i in area_df.Neighbours.values], dtype=object)


# Saving .txt files
file_dir = os.path.join(data_dir, area_name)
os.makedirs(file_dir, exist_ok=True)
files = [open(os.path.join(file_dir, f"{column}.txt"), "w") for column in ["GUID", "Population", "Neighbours"]]
for g, p, n in zip(area_df.GUID.values, area_df.Population.values, area_df.Neighbours.values):
  files[0].write(f"{g}\n")
  files[1].write(f"{p}\n")
  for i in n:
    files[2].write(f"{i} ")
  files[2].write("\n")
for file in files:
  file.close()
