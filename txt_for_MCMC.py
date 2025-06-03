import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import sys


# Area from command line
area_type = sys.argv[1]
area_list = sys.argv[2].split(",")
area_name = sys.argv[3]


# Reading required data
area_df = gpd.read_file("ED_data.geojson")
area_df = area_df[area_df[area_type].isin(area_list)].reset_index(drop=True)


# Saving .txt files
GUID = area_df.GUID.values
population = area_df.Population.values
neighbours = [[j for j, touch in enumerate(area_df.geometry.touches(area_df.geometry[i])) if touch] for i in range(len(area_df))]
GUID_file = open("%s GUIDs.txt" % area_name, "w")
population_file = open("%s populations.txt" % area_name, "w")
neighbours_file = open("%s neighbours.txt" % area_name, "w")
for pop, nei, guid in zip(population, neighbours, GUID):
  GUID_file.write("%s\n" % guid)
  population_file.write("%s\n" % pop)
  for x in nei:
    neighbours_file.write("%s " % x)
  neighbours_file.write("\n")
GUID_file.close()
population_file.close()
neighbours_file.close()
