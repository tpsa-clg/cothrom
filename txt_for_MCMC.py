import numpy as np
import pandas as pd
import sys


# Area from command line
area_type = sys.argv[1]
area_list = sys.argv[2].split(",")
area_name = sys.argv[3]


# Reading required data
area_df = pd.read_csv("ED_data.csv", usecols=["GUID", area_type, "Population", "Neighbours"])
area_df = area_df[area_df[area_type].isin(area_list)].sort_values(by="GUID").reset_index(drop=True)
intersect = set(area_df.GUID.values)
area_df.loc[:, "Neighbours"] = np.array([eval(i) & intersect for i in area_df.Neighbours.values], dtype=object)
area_df.loc[:, "Neighbours"] = np.array([area_df.index[area_df["GUID"].isin(i)].tolist() for i in area_df.Neighbours.values], dtype=object)


# Saving .txt files
files = [open("%s %s.txt" % (area_name, column), "w") for column in ["GUID", "Population", "Neighbours"]]
for g, p, n in zip(area_df.GUID.values, area_df.Population.values, area_df.Neighbours.values):
  files[0].write("%s\n" % g)
  files[1].write("%s\n" % p)
  for i in n:
    files[2].write("%s " % i)
  files[2].write("\n")
for file in files:
  file.close()
