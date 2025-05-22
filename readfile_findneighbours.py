import numpy as np
import pandas as pd
import geopandas as geop
import matplotlib.pyplot as plt


district_data = pd.read_csv("FP009.csv").pivot_table(
    values="VALUE", index=["ED_ID"], columns="Statistic").reset_index().rename(
        columns={"Population - 2022": "population"}).astype("int32")[
            ["ED_ID", "population"]]
district_geography = geop.read_file(
    "Electoral_Divisions_-_National_Statutory_Boundaries_-_2019_-_Generalised_20m.geojson"
    ).astype({"ED_ID": "int32"})[["ED_ID", "ENGLISH", "COUNTY", "geometry"]]


constituency_str = "Carlow-Kilkenny"
constituency_df = district_geography[(district_geography.COUNTY == "CARLOW") |
                                     (district_geography.COUNTY == "KILKENNY")]
constituency_df = constituency_df[(constituency_df.ENGLISH != "BALLYBEAGH") &
                                  (constituency_df.ENGLISH != "FRESHFORD") &
                                  (constituency_df.ENGLISH != "RATHEALY") &
                                  (constituency_df.ENGLISH != "TULLAROAN") &
                                  (constituency_df.ENGLISH != "BALLEEN") &
                                  (constituency_df.ENGLISH != "BAUNMORE") &
                                  (constituency_df.ENGLISH != "CLOMANTAGH") &
                                  (constituency_df.ENGLISH != "GALMOY") &
                                  (constituency_df.ENGLISH != "GLASHARE") &
                                  (constituency_df.ED_ID != 97053) &
                                  (constituency_df.ENGLISH != "LISDOWNEY") &
                                  (constituency_df.ENGLISH != "TUBBRIDBRITTAIN") &
                                  (constituency_df.ENGLISH != "URLINGFORD")]

constituency_df = constituency_df.merge(district_data, on="ED_ID")
population = constituency_df.population.values
neighbours = np.array([
    [j for j, touch in enumerate(constituency_df.geometry.touches(
        constituency_df.geometry[i])) if touch] for i in
    range(len(constituency_df))], dtype=object)
ED = constituency_df.ED_ID.values
pop_file = open("%s populations.txt" % constituency_str, "w")
nei_file = open("%s neighbours.txt" % constituency_str, "w")
ED_file = open("%s EDs.txt" % constituency_str, "w")
for pop, nei, ed in zip(population, neighbours, ED):
    pop_file.write("%s\n" % pop)
    for x in nei:
        nei_file.write("%s " % x)
    nei_file.write("\n")
    ED_file.write("%s\n" % ed)
pop_file.close()
nei_file.close()
ED_file.close()
constituency_df.plot()
plt.title(constituency_str)
plt.show()


constituency_str = "Donegal"
constituency_df = district_geography[district_geography.COUNTY == "DONEGAL"]
constituency_df = constituency_df[(constituency_df.ENGLISH != "BALLINTRA") &
                                  (constituency_df.ENGLISH != "BALLYSHANNON RURAL") &
                                  (constituency_df.ENGLISH != "BALLYSHANNON URBAN") &
                                  (constituency_df.ENGLISH != "BUNDORAN RURAL") &
                                  (constituency_df.ENGLISH != "CARRICKBOY") &
                                  (constituency_df.ENGLISH != "CAVANGARDEN") &
                                  (constituency_df.ENGLISH != "CLIFF") &
                                  (constituency_df.ENGLISH != "BUNDORAN URBAN")]

constituency_df = constituency_df.merge(district_data, on="ED_ID")
population = constituency_df.population.values
neighbours = np.array([
    [j for j, touch in enumerate(constituency_df.geometry.touches(
        constituency_df.geometry[i])) if touch] for i in
    range(len(constituency_df))], dtype=object)
ED = constituency_df.ED_ID.values
pop_file = open("%s populations.txt" % constituency_str, "w")
nei_file = open("%s neighbours.txt" % constituency_str, "w")
ED_file = open("%s EDs.txt" % constituency_str, "w")
for pop, nei, ed in zip(population, neighbours, ED):
    pop_file.write("%s\n" % pop)
    for x in nei:
        nei_file.write("%s " % x)
    nei_file.write("\n")
    ED_file.write("%s\n" % ed)
pop_file.close()
nei_file.close()
ED_file.close()
constituency_df.plot()
plt.title(constituency_str)
plt.show()


constituency_str = "Louth"
constituency_df = district_geography[(district_geography.COUNTY == "LOUTH") |
                                     (district_geography.ED_ID == 167082)]

constituency_df = constituency_df.merge(district_data, on="ED_ID")
population = constituency_df.population.values
neighbours = np.array([
    [j for j, touch in enumerate(constituency_df.geometry.touches(
        constituency_df.geometry[i])) if touch] for i in
    range(len(constituency_df))], dtype=object)
ED = constituency_df.ED_ID.values
pop_file = open("%s populations.txt" % constituency_str, "w")
nei_file = open("%s neighbours.txt" % constituency_str, "w")
ED_file = open("%s EDs.txt" % constituency_str, "w")
for pop, nei, ed in zip(population, neighbours, ED):
    pop_file.write("%s\n" % pop)
    for x in nei:
        nei_file.write("%s " % x)
    nei_file.write("\n")
    ED_file.write("%s\n" % ed)
pop_file.close()
nei_file.close()
ED_file.close()
constituency_df.plot()
plt.title(constituency_str)
plt.show()


constituency_str = "Kildare North"
constituency_df = district_geography[district_geography.COUNTY == "KILDARE"]
constituency_df = constituency_df[(constituency_df.ENGLISH == "BALRAHEEN") |
                                  (constituency_df.ENGLISH == "CELBRIDGE") |
                                  (constituency_df.ED_ID == 87026) |
                                  (constituency_df.ENGLISH == "DONADEA") |
                                  (constituency_df.ENGLISH == "DONAGHCUMPER") |
                                  (constituency_df.ENGLISH == "KILCOCK") |
                                  (constituency_df.ENGLISH == "LEIXLIP") |
                                  (constituency_df.ENGLISH == "MAYNOOTH") |
                                  (constituency_df.ENGLISH == "STRAFFAN") |
                                  (constituency_df.ENGLISH == "BALLYNADRUMNY") |
                                  (constituency_df.ENGLISH == "CADAMSTOWN") |
                                  (constituency_df.ENGLISH == "DUNFIERTH") |
                                  (constituency_df.ENGLISH == "BODENSTOWN") |
                                  (constituency_df.ENGLISH == "CLANE") |
                                  (constituency_df.ENGLISH == "CARRAGH") |
                                  (constituency_df.ENGLISH == "DONORE") |
                                  (constituency_df.ENGLISH == "DOWNINGS") |
                                  (constituency_df.ENGLISH == "KILL") |
                                  (constituency_df.ENGLISH == "KILLASHEE") |
                                  (constituency_df.ENGLISH == "KILTEEL") |
                                  (constituency_df.ENGLISH == "LADYTOWN") |
                                  (constituency_df.ENGLISH == "NAAS RURAL") |
                                  (constituency_df.ENGLISH == "NEWTOWN") |
                                  (constituency_df.ENGLISH == "OUGHTERARD") |
                                  (constituency_df.ENGLISH == "RATHMORE") |
                                  (constituency_df.ENGLISH == "TIMAHOE NORTH") |
                                  (constituency_df.ENGLISH == "NAAS URBAN")]

constituency_df = constituency_df.merge(district_data, on="ED_ID")
population = constituency_df.population.values
neighbours = np.array([
    [j for j, touch in enumerate(constituency_df.geometry.touches(
        constituency_df.geometry[i])) if touch] for i in
    range(len(constituency_df))], dtype=object)
ED = constituency_df.ED_ID.values
pop_file = open("%s populations.txt" % constituency_str, "w")
nei_file = open("%s neighbours.txt" % constituency_str, "w")
ED_file = open("%s EDs.txt" % constituency_str, "w")
for pop, nei, ed in zip(population, neighbours, ED):
    pop_file.write("%s\n" % pop)
    for x in nei:
        nei_file.write("%s " % x)
    nei_file.write("\n")
    ED_file.write("%s\n" % ed)
pop_file.close()
nei_file.close()
ED_file.close()
constituency_df.plot()
plt.title(constituency_str)
plt.show()


constituency_str = "Kildare South"
constituency_df = constituency_df.drop(columns=["population"])
constituency_df = pd.concat(
    [district_geography[district_geography.COUNTY == "KILDARE"],
     constituency_df]).drop_duplicates(subset="ED_ID", keep=False)

constituency_df = constituency_df.merge(district_data, on="ED_ID")
population = constituency_df.population.values
neighbours = np.array([
    [j for j, touch in enumerate(constituency_df.geometry.touches(
        constituency_df.geometry[i])) if touch] for i in
    range(len(constituency_df))], dtype=object)
ED = constituency_df.ED_ID.values
pop_file = open("%s populations.txt" % constituency_str, "w")
nei_file = open("%s neighbours.txt" % constituency_str, "w")
ED_file = open("%s EDs.txt" % constituency_str, "w")
for pop, nei, ed in zip(population, neighbours, ED):
    pop_file.write("%s\n" % pop)
    for x in nei:
        nei_file.write("%s " % x)
    nei_file.write("\n")
    ED_file.write("%s\n" % ed)
pop_file.close()
nei_file.close()
ED_file.close()
constituency_df.plot()
plt.title(constituency_str)
plt.show()


constituency_str = "Limerick City"
constituency_df = district_geography[district_geography.COUNTY == "LIMERICK"]
constituency_df = constituency_df[(constituency_df.ENGLISH == "ABBEY A") |
                                  (constituency_df.ENGLISH == "ABBEY B") |
                                  (constituency_df.ENGLISH == "ABBEY C") |
                                  (constituency_df.ENGLISH == "ABBEY D") |
                                  (constituency_df.ENGLISH == "BALLINACURRA A") |
                                  (constituency_df.ENGLISH == "BALLINACURRA B") |
                                  (constituency_df.ENGLISH == "BALLYNANTY") |
                                  (constituency_df.ENGLISH == "CASTLE A") |
                                  (constituency_df.ENGLISH == "CASTLE B") |
                                  (constituency_df.ENGLISH == "CASTLE C") |
                                  (constituency_df.ENGLISH == "CASTLE D") |
                                  (constituency_df.ENGLISH == "COOLRAINE") |
                                  (constituency_df.ENGLISH == "CUSTOM HOUSE") |
                                  (constituency_df.ENGLISH == "DOCK A") |
                                  (constituency_df.ENGLISH == "DOCK B") |
                                  (constituency_df.ENGLISH == "DOCK C") |
                                  (constituency_df.ENGLISH == "DOCK D") |
                                  (constituency_df.ENGLISH == "FARRANSHONE") |
                                  (constituency_df.ENGLISH == "GALVONE A") |
                                  (constituency_df.ENGLISH == "GALVONE B") |
                                  (constituency_df.ENGLISH == "GLENTWORTH A") |
                                  (constituency_df.ENGLISH == "GLENTWORTH B") |
                                  (constituency_df.ENGLISH == "GLENTWORTH C") |
                                  (constituency_df.ENGLISH == "JOHN'S A") |
                                  (constituency_df.ENGLISH == "JOHN'S B") |
                                  (constituency_df.ENGLISH == "JOHN'S C") |
                                  (constituency_df.ENGLISH == "KILLEELY A") |
                                  (constituency_df.ENGLISH == "KILLEELY B") |
                                  (constituency_df.ENGLISH == "MARKET") |
                                  (constituency_df.ENGLISH == "PROSPECT A") |
                                  (constituency_df.ENGLISH == "PROSPECT B") |
                                  (constituency_df.ENGLISH == "RATHBANE") |
                                  (constituency_df.ENGLISH == "SHANNON A") |
                                  (constituency_df.ENGLISH == "SHANNON B") |
                                  (constituency_df.ENGLISH == "SINGLAND A") |
                                  (constituency_df.ENGLISH == "SINGLAND B") |
                                  (constituency_df.ENGLISH == "St. LAURENCE") |
                                  (constituency_df.ENGLISH == "ABINGTON") |
                                  (constituency_df.ENGLISH == "BALLYBRICKEN") |
                                  (constituency_df.ENGLISH == "BALLYCUMMIN") |
                                  (constituency_df.ENGLISH == "BALLYSIMON") |
                                  (constituency_df.ENGLISH == "BALLYVARRA") |
                                  (constituency_df.ENGLISH == "CAHERCONLISH EAST") |
                                  (constituency_df.ENGLISH == "CAHERCONLISH WEST") |
                                  (constituency_df.ENGLISH == "CASTLECONNELL") |
                                  (constituency_df.ENGLISH == "CLONKEEN") |
                                  (constituency_df.ENGLISH == "GLENSTAL") |
                                  (constituency_df.ENGLISH == "LIMERICK NORTH RURAL") |
                                  (constituency_df.ENGLISH == "LIMERICK SOUTH RURAL") |
                                  (constituency_df.ENGLISH == "ROXBOROUGH")]

constituency_df = constituency_df.merge(district_data, on="ED_ID")
population = constituency_df.population.values
neighbours = np.array([
    [j for j, touch in enumerate(constituency_df.geometry.touches(
        constituency_df.geometry[i])) if touch] for i in
    range(len(constituency_df))], dtype=object)
ED = constituency_df.ED_ID.values
pop_file = open("%s populations.txt" % constituency_str, "w")
nei_file = open("%s neighbours.txt" % constituency_str, "w")
ED_file = open("%s EDs.txt" % constituency_str, "w")
for pop, nei, ed in zip(population, neighbours, ED):
    pop_file.write("%s\n" % pop)
    for x in nei:
        nei_file.write("%s " % x)
    nei_file.write("\n")
    ED_file.write("%s\n" % ed)
pop_file.close()
nei_file.close()
ED_file.close()
constituency_df.plot()
plt.title(constituency_str)
plt.show()


constituency_str = "Limerick County"
constituency_df = constituency_df.drop(columns=["population"])
constituency_df = pd.concat(
    [district_geography[district_geography.COUNTY == "LIMERICK"],
     constituency_df]).drop_duplicates(subset="ED_ID", keep=False)

constituency_df = constituency_df.merge(district_data, on="ED_ID")
population = constituency_df.population.values
neighbours = np.array([
    [j for j, touch in enumerate(constituency_df.geometry.touches(
        constituency_df.geometry[i])) if touch] for i in
    range(len(constituency_df))], dtype=object)
ED = constituency_df.ED_ID.values
pop_file = open("%s populations.txt" % constituency_str, "w")
nei_file = open("%s neighbours.txt" % constituency_str, "w")
ED_file = open("%s EDs.txt" % constituency_str, "w")
for pop, nei, ed in zip(population, neighbours, ED):
    pop_file.write("%s\n" % pop)
    for x in nei:
        nei_file.write("%s " % x)
    nei_file.write("\n")
    ED_file.write("%s\n" % ed)
pop_file.close()
nei_file.close()
ED_file.close()
constituency_df.plot()
plt.title(constituency_str)
plt.show()


constituency_str = "Wicklow-Wexford"
constituency_df = district_geography[(district_geography.COUNTY == "WICKLOW") |
                                     (district_geography.COUNTY == "WEXFORD")]
constituency_df = constituency_df[(constituency_df.ENGLISH == "BALLINDAGGAN") |
                                  (constituency_df.ENGLISH == "BALLYCARNEY") |
                                  (constituency_df.ENGLISH == "BALLYMORE") |
                                  (constituency_df.ENGLISH == "CASTLEDOCKRELL") |
                                  (constituency_df.ENGLISH == "FERNS") |
                                  (constituency_df.ENGLISH == "KILBORA") |
                                  (constituency_df.ENGLISH == "KILCORMICK") |
                                  (constituency_df.ENGLISH == "KILRUSH") |
                                  (constituency_df.ENGLISH == "MOYACOMB") |
                                  (constituency_df.ENGLISH == "NEWTOWNBARRY") |
                                  (constituency_df.ENGLISH == "ROSSARD") |
                                  (constituency_df.ENGLISH == "St. MARY'S") |
                                  (constituency_df.ENGLISH == "THE HARROW") |
                                  (constituency_df.ENGLISH == "TINNACROSS") |
                                  (constituency_df.ENGLISH == "TOMBRACK") |
                                  (constituency_df.ENGLISH == "ARDAMINE") |
                                  (constituency_df.ENGLISH == "BALLOUGHTER") |
                                  (constituency_df.ENGLISH == "BALLYBEG") |
                                  (constituency_df.ENGLISH == "BALLYCANEW") |
                                  (constituency_df.ENGLISH == "BALLYELLIS") |
                                  (constituency_df.ENGLISH == "BALLYGARRETT") |
                                  (constituency_df.ENGLISH == "BALLYLARKIN") |
                                  (constituency_df.ENGLISH == "BALLYNESTRAGH") |
                                  (constituency_df.ENGLISH == "CAHORE") |
                                  (constituency_df.ENGLISH == "COOLGREANY") |
                                  (constituency_df.ENGLISH == "COURTOWN") |
                                  (constituency_df.ENGLISH == "FORD") |
                                  (constituency_df.ENGLISH == "GOREY RURAL") |
                                  (constituency_df.ENGLISH == "GOREY URBAN") |
                                  (constituency_df.ENGLISH == "HUNTINGTOWN") |
                                  (constituency_df.ENGLISH == "KILCOMB") |
                                  (constituency_df.ENGLISH == "KILGORMAN") |
                                  (constituency_df.ENGLISH == "KILLENAGH") |
                                  (constituency_df.ENGLISH == "KILLINCOOLY") |
                                  (constituency_df.ENGLISH == "KILNAHUE") |
                                  (constituency_df.ENGLISH == "LIMERICK") |
                                  (constituency_df.ENGLISH == "MONAMOLIN") |
                                  (constituency_df.ENGLISH == "MONASEED") |
                                  (constituency_df.ENGLISH == "ROSSMINOGE") |
                                  (constituency_df.ENGLISH == "WELLS") |
                                  (constituency_df.ENGLISH == "WINGFIELD") |
                                  (constituency_df.ENGLISH == "ARKLOW RURAL") |
                                  (constituency_df.ENGLISH == "AUGHRIM") |
                                  (constituency_df.ENGLISH == "BALLINACLASH") |
                                  (constituency_df.ENGLISH == "BALLINACOR") |
                                  (constituency_df.ENGLISH == "BALLINDERRY") |
                                  (constituency_df.ENGLISH == "BALLYARTHUR") |
                                  (constituency_df.ENGLISH == "CRONEBANE") |
                                  (constituency_df.ENGLISH == "DUNGANSTOWN EAST") |
                                  (constituency_df.ENGLISH == "DUNGANSTOWN SOUTH") |
                                  (constituency_df.ENGLISH == "DUNGANSTOWN WEST") |
                                  (constituency_df.ENGLISH == "ENNEREILLY") |
                                  (constituency_df.ED_ID == 257047) |
                                  (constituency_df.ENGLISH == "OVOCA") |
                                  (constituency_df.ENGLISH == "RATHDRUM") |
                                  (constituency_df.ENGLISH == "AGHOWLE") |
                                  (constituency_df.ENGLISH == "BALLINGATE") |
                                  (constituency_df.ENGLISH == "BALLINGLEN") |
                                  (constituency_df.ENGLISH == "CARNEW") |
                                  (constituency_df.ENGLISH == "COOLATTIN") |
                                  (constituency_df.ENGLISH == "COOLBOY") |
                                  (constituency_df.ENGLISH == "CRONELEA") |
                                  (constituency_df.ENGLISH == "KILBALLYOWEN") |
                                  (constituency_df.ENGLISH == "KILLINURE") |
                                  (constituency_df.ENGLISH == "KILPIPE") |
                                  (constituency_df.ENGLISH == "MONEY") |
                                  (constituency_df.ENGLISH == "RATH") |
                                  (constituency_df.ENGLISH == "SHILLELAGH") |
                                  (constituency_df.ENGLISH == "TINAHELY") |
                                  (constituency_df.ENGLISH == "SHILLELAGH") |
                                  (constituency_df.ENGLISH == "ARKLOW No. 1 URBAN") |
                                  (constituency_df.ENGLISH == "ARKLOW No. 2 URBAN")]

constituency_df = constituency_df.merge(district_data, on="ED_ID")
population = constituency_df.population.values
neighbours = np.array([
    [j for j, touch in enumerate(constituency_df.geometry.touches(
        constituency_df.geometry[i])) if touch] for i in
    range(len(constituency_df))], dtype=object)
ED = constituency_df.ED_ID.values
pop_file = open("%s populations.txt" % constituency_str, "w")
nei_file = open("%s neighbours.txt" % constituency_str, "w")
ED_file = open("%s EDs.txt" % constituency_str, "w")
for pop, nei, ed in zip(population, neighbours, ED):
    pop_file.write("%s\n" % pop)
    for x in nei:
        nei_file.write("%s " % x)
    nei_file.write("\n")
    ED_file.write("%s\n" % ed)
pop_file.close()
nei_file.close()
ED_file.close()
constituency_df.plot()
plt.title(constituency_str)
plt.show()


constituency_str = "Wicklow"
constituency_df1 = constituency_df.drop(columns=["population"])
constituency_df = pd.concat(
    [district_geography[district_geography.COUNTY == "WICKLOW"],
     constituency_df1[constituency_df1.COUNTY == "WICKLOW"]]).drop_duplicates(
         subset="ED_ID", keep=False)

constituency_df = constituency_df.merge(district_data, on="ED_ID")
population = constituency_df.population.values
neighbours = np.array([
    [j for j, touch in enumerate(constituency_df.geometry.touches(
        constituency_df.geometry[i])) if touch] for i in
    range(len(constituency_df))], dtype=object)
ED = constituency_df.ED_ID.values
pop_file = open("%s populations.txt" % constituency_str, "w")
nei_file = open("%s neighbours.txt" % constituency_str, "w")
ED_file = open("%s EDs.txt" % constituency_str, "w")
for pop, nei, ed in zip(population, neighbours, ED):
    pop_file.write("%s\n" % pop)
    for x in nei:
        nei_file.write("%s " % x)
    nei_file.write("\n")
    ED_file.write("%s\n" % ed)
pop_file.close()
nei_file.close()
ED_file.close()
constituency_df.plot()
plt.title(constituency_str)
plt.show()


constituency_str = "Wexford"
constituency_df = pd.concat(
    [district_geography[district_geography.COUNTY == "WEXFORD"],
     constituency_df1[constituency_df1.COUNTY == "WEXFORD"]]).drop_duplicates(
         subset="ED_ID", keep=False)
del constituency_df1

constituency_df = constituency_df.merge(district_data, on="ED_ID")
population = constituency_df.population.values
neighbours = np.array([
    [j for j, touch in enumerate(constituency_df.geometry.touches(
        constituency_df.geometry[i])) if touch] for i in
    range(len(constituency_df))], dtype=object)
ED = constituency_df.ED_ID.values
pop_file = open("%s populations.txt" % constituency_str, "w")
nei_file = open("%s neighbours.txt" % constituency_str, "w")
ED_file = open("%s EDs.txt" % constituency_str, "w")
for pop, nei, ed in zip(population, neighbours, ED):
    pop_file.write("%s\n" % pop)
    for x in nei:
        nei_file.write("%s " % x)
    nei_file.write("\n")
    ED_file.write("%s\n" % ed)
pop_file.close()
nei_file.close()
ED_file.close()
constituency_df.plot()
plt.title(constituency_str)
plt.show()


constituency_str = "Meath East"
constituency_df = district_geography[district_geography.COUNTY == "MEATH"]
constituency_df = constituency_df[(constituency_df.ENGLISH == "DRUMCONDRA") |
                                  (constituency_df.ENGLISH == "GRANGEGEETH") |
                                  (constituency_df.ENGLISH == "KILLARY") |
                                  (constituency_df.ENGLISH == "CULMULLIN") |
                                  (constituency_df.ENGLISH == "DONAGHMORE") |
                                  (constituency_df.ENGLISH == "DUNBOYNE") |
                                  (constituency_df.ENGLISH == "DUNSHAUGHLIN") |
                                  (constituency_df.ENGLISH == "KILBREW") |
                                  (constituency_df.ENGLISH == "KILLEEN") |
                                  (constituency_df.ENGLISH == "KILMORE") |
                                  (constituency_df.ENGLISH == "RATHFEIGH") |
                                  (constituency_df.ENGLISH == "RATOATH") |
                                  (constituency_df.ENGLISH == "RODANSTOWN") |
                                  (constituency_df.ENGLISH == "SKREEN") |
                                  (constituency_df.ENGLISH == "ARDAGH") |
                                  (constituency_df.ENGLISH == "CARRICKLECK") |
                                  (constituency_df.ENGLISH == "CEANANNAS MÓR RURAL") |
                                  (constituency_df.ENGLISH == "CRUICETOWN") |
                                  (constituency_df.ENGLISH == "KILMAINHAM") |
                                  (constituency_df.ENGLISH == "MAPERATH") |
                                  (constituency_df.ENGLISH == "MOYBOLGUE") |
                                  (constituency_df.ENGLISH == "MOYNALTY") |
                                  (constituency_df.ENGLISH == "NEWCASTLE") |
                                  (constituency_df.ENGLISH == "NEWTOWN") |
                                  (constituency_df.ENGLISH == "NOBBER") |
                                  (constituency_df.ENGLISH == "POSSECKSTOWN") |
                                  (constituency_df.ENGLISH == "STAHOLMOG") |
                                  (constituency_df.ENGLISH == "TROHANNY") |
                                  (constituency_df.ENGLISH == "ARDCATH") |
                                  (constituency_df.ENGLISH == "DULEEK") |
                                  (constituency_df.ENGLISH == "JULIANSTOWN") |
                                  (constituency_df.ENGLISH == "MELLIFONT") |
                                  (constituency_df.ENGLISH == "STAMULLIN") |
                                  (constituency_df.ENGLISH == "ARDMULCHAN") |
                                  (constituency_df.ENGLISH == "CASTLETOWN") |
                                  (constituency_df.ENGLISH == "DONAGHPATRICK") |
                                  (constituency_df.ENGLISH == "KENTSTOWN") |
                                  (constituency_df.ENGLISH == "PAINESTOWN") |
                                  (constituency_df.ENGLISH == "RATHKENNY") |
                                  (constituency_df.ENGLISH == "SLANE") |
                                  (constituency_df.ENGLISH == "STACKALLAN") |
                                  (constituency_df.ENGLISH == "TARA") |
                                  (constituency_df.ENGLISH == "CEANANNAS MÓR URBAN")]

constituency_df = constituency_df.merge(district_data, on="ED_ID")
population = constituency_df.population.values
neighbours = np.array([
    [j for j, touch in enumerate(constituency_df.geometry.touches(
        constituency_df.geometry[i])) if touch] for i in
    range(len(constituency_df))], dtype=object)
ED = constituency_df.ED_ID.values
pop_file = open("%s populations.txt" % constituency_str, "w")
nei_file = open("%s neighbours.txt" % constituency_str, "w")
ED_file = open("%s EDs.txt" % constituency_str, "w")
for pop, nei, ed in zip(population, neighbours, ED):
    pop_file.write("%s\n" % pop)
    for x in nei:
        nei_file.write("%s " % x)
    nei_file.write("\n")
    ED_file.write("%s\n" % ed)
pop_file.close()
nei_file.close()
ED_file.close()
constituency_df.plot()
plt.title(constituency_str)
plt.show()


constituency_str = "Meath West"
constituency_df = constituency_df.drop(columns=["population"])
constituency_df = pd.concat(
    [district_geography[(district_geography.COUNTY == "MEATH") &
                        (district_geography.ED_ID != 167082)],
     constituency_df]).drop_duplicates(subset="ED_ID", keep=False)

constituency_df = constituency_df.merge(district_data, on="ED_ID")
population = constituency_df.population.values
neighbours = np.array([
    [j for j, touch in enumerate(constituency_df.geometry.touches(
        constituency_df.geometry[i])) if touch] for i in
    range(len(constituency_df))], dtype=object)
ED = constituency_df.ED_ID.values
pop_file = open("%s populations.txt" % constituency_str, "w")
nei_file = open("%s neighbours.txt" % constituency_str, "w")
ED_file = open("%s EDs.txt" % constituency_str, "w")
for pop, nei, ed in zip(population, neighbours, ED):
    pop_file.write("%s\n" % pop)
    for x in nei:
        nei_file.write("%s " % x)
    nei_file.write("\n")
    ED_file.write("%s\n" % ed)
pop_file.close()
nei_file.close()
ED_file.close()
constituency_df.plot()
plt.title(constituency_str)
plt.show()
