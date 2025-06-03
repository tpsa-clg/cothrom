import numpy as np
import pandas as pd
import geopandas as geop
import matplotlib.pyplot as plt

# constituency_str = "Carlow-Kilkenny"
# constituency_df = constituency_df.merge(district_data, on="ED_ID")
# population = constituency_df.population.values
# neighbours = np.array([
#     [j for j, touch in enumerate(constituency_df.geometry.touches(
#         constituency_df.geometry[i])) if touch] for i in
#     range(len(constituency_df))], dtype=object)
# ED = constituency_df.ED_ID.values
# pop_file = open("%s populations.txt" % constituency_str, "w")
# nei_file = open("%s neighbours.txt" % constituency_str, "w")
# ED_file = open("%s EDs.txt" % constituency_str, "w")
# for pop, nei, ed in zip(population, neighbours, ED):
#     pop_file.write("%s\n" % pop)
#     for x in nei:
#         nei_file.write("%s " % x)
#     nei_file.write("\n")
#     ED_file.write("%s\n" % ed)
# pop_file.close()
# nei_file.close()
# ED_file.close()
# constituency_df.plot()
# plt.title(constituency_str)
# plt.show()

# important_data["Neighbours"] = np.array([[important_data.GUID[j] for j, touch in enumerate(important_data.geometry.touches(important_data.geometry[i])) if touch] for i in range(len(important_data))], dtype=object)
