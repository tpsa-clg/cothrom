import pandas as pd
import geopandas as gpd
from libpysal.weights import Queen
from glob import glob
import requests
import os

# Map resolution
resolution = "100m"


# Setting data directory
data_dir = os.path.join(*[os.path.dirname(os.path.realpath(__file__)), os.pardir, "data"])
os.makedirs(data_dir, exist_ok=True)

# Downloading Central Statistics Office population data if not in data directory
pop_file = glob(os.path.join(data_dir, "F1060*.csv"))
if pop_file:
    pop_file = pop_file[0]
else:
    webpage = "https://data.cso.ie/table/F1060"
    print(f"CSO ED populations not in data directory. Downloading from {webpage}...")
    r = requests.get(
        r"https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.PxAPIv1/en/76/C2022P1/F1060?query=%7B%22query%22:%5B%7B%22code%22:%22STATISTIC%22,%22selection%22:%7B%22filter%22:%22item%22,%22values%22:%5B%22F1060C01%22%5D%7D%7D,%7B%22code%22:%22C02199V02655%22,%22selection%22:%7B%22filter%22:%22item%22,%22values%22:%5B%22-%22%5D%7D%7D%5D,%22response%22:%7B%22format%22:%22csv%22,%22pivot%22:null,%22codes%22:true%7D%7D"
        )
    r.close()
    r.raise_for_status()
    pop_file = os.path.join(data_dir, "F1060.csv")
    with open(pop_file, "wb") as f:
        f.write(r.content)
    del r
    print("CSO ED populations downloaded.")

# Downloading Tailte Éireann geographical data if not in data directory
available_resolutions = ["100m", "50m", "20m", "Ungeneralised"]
map_dict = {available_resolution: {
    "webpage": f"https://data.gov.ie/dataset/cso-electoral-divisions-national-statistical-boundaries-2022-{webpage_suffix}1",
    "download": f"https://data-osi.opendata.arcgis.com/api/download/v1/items/{download_suffix}"
    } for available_resolution, webpage_suffix, download_suffix in zip(
        available_resolutions, ["generalised-100m", "generalised-50m", "generalised-20m", "ungeneralised"],
        [
            "a55332e0d15148688e06893086cb023b/geojson?layers=1",
            "5e0536e5c6804b0087b14a5d929c429a/geojson?layers=4",
            "ed3d7b317e244a32b8eeba4d2bd9b9df/geojson?layers=5",
            "deba50580cc24e4eb9cf50eb3cfebf69/geojson?layers=1"
            ])}
geo_file = glob(os.path.join(data_dir, f"*{resolution}*.geojson"))
if geo_file:
    geo_file = geo_file[0]
else:
    print(f"Tailte Éireann {resolution} ED geography not in data directory. Downloading from {map_dict[resolution]['webpage']}...")
    r = requests.get(map_dict[resolution]["download"])
    r.close()
    r.raise_for_status()
    geo_file = os.path.join(data_dir, f"{resolution}.geojson")
    with open(geo_file, "wb") as f:
        f.write(r.content)
    del r
    print(f"Tailte Éireann {resolution} ED geography downloaded.")

# Downloading county data if not in data directory
counties_file = glob(os.path.join(data_dir, "Counties*.geojson"))
if not counties_file:
    print(
        "Tailte Éireann county geography not in data directory. Downloading from "
        "https://data.gov.ie/dataset/counties-national-statutory-boundaries-2019-generalised-20m1..."
        )
    try:
        r = requests.get(
            "https://data-osi.opendata.arcgis.com/api/download/v1/items/7ef9c5102d61424295e98505a00251ea/geojson?layers=0"
            )
        r.close()
        r.raise_for_status()
        with open(os.path.join(data_dir, f"Counties.geojson"), "wb") as f:
            f.write(r.content)
        del r
        print("Tailte Éireann county geography downloaded.")
    except Exception as e:
        print(
            "Tailte Éireann county geography not downloaded. "
            "This is not used in this execution, but is required for plotting configurations."
            )
        print("Error message:", e)


# Reading population data
pop_df = pd.read_csv(pop_file, usecols=["C04167V04938", "VALUE"])
pop_df.rename(columns={"C04167V04938": "GUID", "VALUE": "Population"}, inplace=True)

# Reading geographical data (name, county, LEA, geometry)
geo_df = gpd.read_file(geo_file)
geo_df = geo_df[["ED_GUID", "ED_ENGLISH", "COUNTY_ENGLISH", "CSO_LEA", "geometry"]]
geo_df.rename(columns={"ED_GUID": "GUID",
                       "ED_ENGLISH": "Name",
                       "COUNTY_ENGLISH": "Administrative Region",
                       "CSO_LEA": "LEA"}, inplace=True)

# Merging datasets
important_data = geo_df.merge(pop_df, how="left", on="GUID")
del geo_df, pop_df
important_data.sort_values("GUID", inplace=True)
important_data.reset_index(drop=True, inplace=True)
print("CSO & Tailte Éireann data merged.")


# Obtaining areas and perimeters (in km² and km)
important_data["Area"], important_data["Perimeter"] = important_data.area/(1000.**2.), important_data.length/(1000.)
print("Area and perimeter data added.")

# Finding all neighbours
weights = Queen.from_dataframe(important_data, ids="GUID", use_index=False, silence_warnings=True)
neighbour_dict = weights.neighbors
important_data["Neighbours"] = [set(neighbour_dict[GUID]) for GUID in important_data.GUID.values]
del weights, neighbour_dict

# Manually adding neighbours to neighbourless EDs
important_data.loc[important_data.Name=="DOOEGA", "Neighbours"].values[0].add("2ae19629-196e-13a3-e055-000000000001")
important_data.loc[important_data.GUID=="2ae19629-196e-13a3-e055-000000000001", "Neighbours"].values[0].add(important_data[important_data.Name=="DOOEGA"].GUID.values[0])
important_data.loc[important_data.Name=="CLARE ISLAND", "Neighbours"] = {"2ae19629-18e7-13a3-e055-000000000001"}
important_data.loc[important_data.GUID=="2ae19629-18e7-13a3-e055-000000000001", "Neighbours"].values[0].add(important_data[important_data.Name=="CLARE ISLAND"].GUID.values[0])
important_data.loc[important_data.Name=="BEAR", "Neighbours"] = [{"2ae19629-1f7c-13a3-e055-000000000001", "2ae19629-219c-13a3-e055-000000000001"}]
important_data.loc[important_data.GUID=="2ae19629-1f7c-13a3-e055-000000000001", "Neighbours"].values[0].add(important_data[important_data.Name=="BEAR"].GUID.values[0])
important_data.loc[important_data.GUID=="2ae19629-219c-13a3-e055-000000000001", "Neighbours"].values[0].add(important_data[important_data.Name=="BEAR"].GUID.values[0])
important_data.loc[important_data.Name=="ARAN", "Neighbours"] = {"2ae19629-20a2-13a3-e055-000000000001"}
important_data.loc[important_data.GUID=="2ae19629-20a2-13a3-e055-000000000001", "Neighbours"].values[0].add(important_data[important_data.Name=="ARAN"].GUID.values[0])
important_data.loc[important_data.Name=="VALENCIA", "Neighbours"] = {"2ae19629-2297-13a3-e055-000000000001"}
important_data.loc[important_data.GUID=="2ae19629-2297-13a3-e055-000000000001", "Neighbours"].values[0].add(important_data[important_data.Name=="VALENCIA"].GUID.values[0])
important_data.loc[important_data.Name=="GORUMNA", "Neighbours"] = {"2ae19629-236d-13a3-e055-000000000001"}
important_data.loc[important_data.GUID=="2ae19629-236d-13a3-e055-000000000001", "Neighbours"].values[0].add(important_data[important_data.Name=="GORUMNA"].GUID.values[0])
important_data.loc[important_data.Name=="INISHBOFIN", "Neighbours"] = {"2ae19629-20f4-13a3-e055-000000000001"}
important_data.loc[important_data.GUID=="2ae19629-20f4-13a3-e055-000000000001", "Neighbours"].values[0].add(important_data[important_data.Name=="INISHBOFIN"].GUID.values[0])
important_data.loc[important_data.Name=="INISHMORE", "Neighbours"] = [{"2ae19629-1fc0-13a3-e055-000000000001", "2ae19629-23a5-13a3-e055-000000000001"}]
important_data.loc[important_data.GUID=="2ae19629-1fc0-13a3-e055-000000000001", "Neighbours"].values[0].add(important_data[important_data.Name=="INISHMORE"].GUID.values[0])
important_data.loc[important_data.GUID=="2ae19629-23a5-13a3-e055-000000000001", "Neighbours"].values[0].add(important_data[important_data.Name=="INISHMORE"].GUID.values[0])
print("Neighbours data added.")

# Getting "actual" county names
important_data["County"] = important_data["Administrative Region"]
important_data.loc[important_data.County=="CORK CITY", "County"] = "CORK"
important_data.loc[important_data.County.isin(["DUBLIN CITY", "DUN LAOGHAIRE/RATHDOWN", "FINGAL", "SOUTH DUBLIN"]), "County"] = "DUBLIN"
important_data.loc[important_data.County=="GALWAY CITY", "County"] = "GALWAY"
important_data.loc[important_data.County=="LIMERICK CITY", "County"] = "LIMERICK"
important_data.loc[important_data.County.isin(["NORTH TIPPERARY", "SOUTH TIPPERARY"]), "County"] = "TIPPERARY"
important_data.loc[important_data.County=="WATERFORD CITY", "County"] = "WATERFORD"
print("County data added.")


# Obtaining 2023 constituency data
important_data["Constituency"] = ""

# Whole counties
important_data.loc[important_data["Administrative Region"].isin(["CAVAN", "MONAGHAN"]), "Constituency"] = "CAVAN-MONAGHAN"
important_data.loc[important_data["Administrative Region"]=="CLARE", "Constituency"] = "CLARE"
important_data.loc[important_data["Administrative Region"]=="KERRY", "Constituency"] = "KERRY"
important_data.loc[important_data["Administrative Region"]=="LAOIS", "Constituency"] = "LAOIS"
important_data.loc[important_data["Administrative Region"].isin(["LONGFORD", "WESTMEATH"]), "Constituency"] = "LONGFORD-WESTMEATH"
important_data.loc[important_data["Administrative Region"]=="MAYO", "Constituency"] = "MAYO"
important_data.loc[important_data["Administrative Region"]=="OFFALY", "Constituency"] = "OFFALY"
important_data.loc[important_data["Administrative Region"].isin(["WATERFORD", "WATERFORD CITY"]), "Constituency"] = "WATERFORD"
print("Whole-county constituency data added.")

# Manual entries
important_data.loc[(important_data["Administrative Region"]=="CORK") & ((important_data.Name.isin([
    "COBH RURAL",
    "KNOCKRAHA",
    "AGHERN",
    "BALLYHOOLY",
    "BALLYNOE",
    "CASTLECOOKE",
    "CASTLE HYDE",
    "CASTLELYONS",
    "CASTLETOWNROCHE",
    "COOLE",
    "CURRAGLASS",
    "FERMOY RURAL",
    "GLANWORTH EAST",
    "GLANWORTH WEST",
    "GORTNASKEHY",
    "GORTROE",
    "KILCOR",
    "KILCUMMER",
    "KILLATHY",
    "KILWORTH",
    "KNOCKMOURNE",
    "LEITRIM",
    "RATHCORMACK",
    # multiple Carrig EDs in Cork - added via GUID below
    "CLENOR",
    "MONANIMY",
    "SHANBALLYMORE",
    "SKAHANAGH",
    "WALLSTOWN",
    "BALLINTEMPLE",
    "BALLYCOTTIN",
    "BALLYSPILLANE",
    "CARRIGTOHILL",
    "CASTLEMARTYR",
    "CLONMULT",
    "CLOYNE",
    "CORKBEG",
    "DANGAN",
    "DUNGOURNEY",
    "GARRYVOE",
    "IGHTERMURRAGH",
    "INCH",
    "LISGOOLD",
    "MIDLETON RURAL",
    "MOGEELY",
    "ROSTELLAN",
    "TEMPLEBODAN",
    "TEMPLENACARRIGA",
    "BALLYARTHUR",
    "DERRYVILLANE",
    "FARAHY",
    "KILDORRERY",
    "KILGULLANE",
    "KILPHELAN",
    "MARSHALSTOWN",
    "MITCHELSTOWN",
    "TEMPLEMOLAGA",
    "ARDAGH",
    "CLONPRIEST",
    "KILCRONAT",
    # multiple Killeagh EDs in Cork - added via GUID below
    "KILMACDONOGH",
    "YOUGHAL RURAL",
    "COBH URBAN",
    "FERMOY URBAN",
    "MIDLETON URBAN",
    "YOUGHAL URBAN"
    ])) | (important_data.GUID.isin([
    "2ae19629-1f3d-13a3-e055-000000000001", # Carrig
    "2ae19629-219e-13a3-e055-000000000001" # Killeagh
    ]))), "Constituency"] = "CORK EAST"
important_data.loc[((important_data["Administrative Region"]=="CORK CITY") & (important_data.Name.isin([
    "BLACKPOOL A",
    "BLACKPOOL B",
    "CHURCHFIELD",
    "COMMONS",
    "FAIR HILL A",
    "FAIR HILL B",
    "FAIR HILL C",
    "FARRANFERRIS A",
    "FARRANFERRIS B",
    "FARRANFERRIS C",
    "GURRANEBRAHER A",
    "GURRANEBRAHER B",
    "GURRANEBRAHER C",
    "GURRANEBRAHER D",
    "GURRANEBRAHER E",
    "KNOCKNAHEENY",
    "MAYFIELD",
    "MONTENOTTE A",
    "MONTENOTTE B",
    "St. MARY'S (EAST)", "St. MARY'S (WEST)", # St. Mary's listed as two EDs in CSO data
    "St. PATRICK'S A",
    "St. PATRICK'S B",
    "St. PATRICK'S C",
    "SHANAKIEL",
    "SHANDON A",
    "SHANDON B",
    "SUNDAY'S WELL A",
    "SUNDAY'S WELL B",
    "THE GLEN A",
    "THE GLEN B",
    "TIVOLI A",
    "TIVOLI B",
    "BALLINCOLLIG",
    "BLARNEY",
    "CAHERLAG",
    "CARRIGROHANEBEG",
    "MATEHY",
    "RATHCOONEY",
    "RIVERSTOWN",
    "WHITECHURCH"
    ]))) | ((important_data["Administrative Region"]=="CORK") & ((important_data.Name.isin([
    "BALLYNAGLOGH",
    "BLACKPOOL",
    "CARRIGNAVAR",
    "FIRMOUNT",
    "GLENVILLE",
    "GREENFORT",
    # multiple Killeagh EDs in Cork - added via GUID below
    "KNOCKANTOTA",
    "BALLINCOLLIG",
    "BLARNEY",
    "CAHERLAG",
    "CARRIGROHANEBEG",
    "MATEHY",
    "RATHCOONEY",
    "RIVERSTOWN",
    "WHITECHURCH",
    # multiple Carrig EDs in Cork - added via GUID below
    "KILDINAN",
    "WATERGRASSHILL",
    "BALLYNAMONA",
    "MALLOW RURAL",
    "RAHAN",
    "MALLOW NORTH URBAN",
    "MALLOW SOUTH URBAN"
    ])) | (important_data.GUID.isin([
    "2ae19629-21b8-13a3-e055-000000000001", # Killeagh
    "2ae19629-1f47-13a3-e055-000000000001" # Carrig
    ])))), "Constituency"] = "CORK NORTH-CENTRAL"
important_data.loc[((important_data["Administrative Region"]=="CORK") & ((important_data.Name.isin([
    "BALLYGROMAN",
    "BALLYMURPHY",
    "BENGOUR",
    "BRINNY",
    "KILBONANE",
    "KNOCKAVILLY",
    "MOVIDDY",
    "MURRAGH",
    "TEADIES",
    "TEMPLEMARTIN",
    "DRIPSEY",
    "OVENS",
    "AULTAGH",
    "BEALOCK",
    "BEALANAGEARY",
    "CARRIGBOY",
    "CASTLETOWN",
    "COOLMOUNTAIN",
    "GARROWN",
    "KINNEIGH",
    "MANCH",
    "TEERELTON",
    "ALLOW",
    "BALLYHOOLAHAN",
    "BANTEER",
    "BARLEYHILL",
    "BARNACURRA",
    "BAWNCROSS",
    "BOHERBOY",
    "CASTLECOR",
    "CASTLEMAGNER",
    "CLONFERT EAST",
    "CLONFERT WEST",
    "CLONMEEN",
    "COOLCLOGH",
    "DROMINA",
    "GLENLARA",
    "GORTMORE",
    "GREENANE",
    "KANTURK",
    "KILBRIN",
    "KILMEEN",
    "KNOCKATOOAN",
    "KNOCKTEMPLE",
    "MEENS",
    "MILFORD",
    "NAD",
    "NEWMARKET",
    "NEWTOWN",
    "ROSKEEN",
    "ROSNALEE",
    "ROWLS",
    "TINCOORA",
    "TULLYLEASE",
    "WILLIAMSTOWN",
    "AGHINAGH",
    "AGLISH",
    "SLIEVEREAGH",
    # Béal Átha an Ghaorthaidh ED already included
    "CANNAWAY",
    "CANDROMA",
    "KILNAMARTERY",
    "CLEANRATH",
    "CLONDROHID",
    "CLONMOYLE",
    "DERRYFINEEN",
    "GORTNATUBBRID",
    "GOWLANE",
    "GREENVILLE",
    "INCHIGEELAGH",
    "KILBERRIHERT",
    "KILCULLEN",
    "MACLONEIGH",
    "MAGOURNEY",
    "MASHANAGLASS",
    "MOUNTRIVERS",
    "ULLANES",
    "RAHALISK",
    "WARRENSCOURT",
    "ARDSKEAGH",
    "BALLYCLOGH",
    "BUTTEVANT",
    "CAHERDUGGAN",
    "CHURCHTOWN",
    "DONERAILE",
    "DROMORE",
    "IMPHRICK",
    "KILMACLENINE",
    "KILSHANNIG",
    "LISCARROLL",
    "MILLTOWN",
    "RATHLUIRC",
    "SPRINGFORT",
    "STREAMHILL",
    "TEMPLEMARY",
    "CAHERBARNAGH",
    "COOMLOGANE",
    "CRINNALOO",
    # multiple Cullen EDs in Cork - added via GUID below
    "DERRAGH",
    "DOONASLEEN",
    "DRISHANE",
    "KEALE",
    "KILCORNEY",
    "KNOCKNAGREE",
    "RATHCOOL",
    "SKAGH",
    "MACROOM URBAN"
    ])) | (important_data.GUID=="2ae19629-1f7a-13a3-e055-000000000001"))) | ((important_data["Administrative Region"]=="CORK CITY") & (important_data.Name=="OVENS")), "Constituency"] = "CORK NORTH-WEST"
important_data.loc[((important_data["Administrative Region"]=="CORK CITY") & ~(important_data.Constituency.isin(["CORK NORTH-CENTRAL", "CORK NORTH-WEST"]))) | ((important_data["Administrative Region"]=="CORK") & (important_data.Name.isin([
    "CARRIGALINE",
    "MONKSTOWN URBAN",
    "BALLYGARVAN",
    "DOUGLAS",
    "INISHKENNY",
    "MONKSTOWN RURAL",
    # Carrigaline EDs already included
    "KILPATRICK",
    "LISCLEARY",
    "TEMPLEBREEDY"
    ]))), "Constituency"] = "CORK SOUTH-CENTRAL"
important_data.loc[((important_data["Administrative Region"]=="DUBLIN CITY") & (important_data.Name.isin([
    "AYRFIELD",
    "BEAUMONT C",
    "BEAUMONT D",
    "BEAUMONT E",
    "CLONTARF EAST A",
    "CLONTARF EAST B",
    "CLONTARF EAST C",
    "CLONTARF EAST D",
    "CLONTARF EAST E",
    "CLONTARF WEST A",
    "CLONTARF WEST B",
    "CLONTARF WEST C",
    "CLONTARF WEST D",
    "CLONTARF WEST E",
    "EDENMORE",
    "GRACE PARK",
    "GRANGE A",
    "GRANGE B",
    "GRANGE C",
    "GRANGE D",
    "GRANGE E",
    "HARMONSTOWN A",
    "HARMONSTOWN B",
    "KILMORE B",
    "KILMORE C",
    "KILMORE D",
    "PRIORSWOOD A",
    "PRIORSWOOD B",
    "PRIORSWOOD C",
    "PRIORSWOOD D",
    "PRIORSWOOD E",
    "RAHENY-FOXFIELD",
    "RAHENY-GREENDALE",
    "RAHENY-St. ASSAM"
    ]))) | ((important_data["Administrative Region"]=="FINGAL") & (important_data.Name.isin([
    "BALDOYLE",
    "BALGRIFFIN",
    "HOWTH",
    "SUTTON"
    ]))), "Constituency"] = "DUBLIN BAY NORTH"
important_data.loc[(important_data["Administrative Region"]=="DUBLIN CITY") & (important_data.Name.isin([
    "MANSION HOUSE A",
    "MANSION HOUSE B",
    "PEMBROKE EAST A",
    "PEMBROKE EAST B",
    "PEMBROKE EAST C",
    "PEMBROKE EAST D",
    "PEMBROKE EAST E",
    "PEMBROKE WEST A",
    "PEMBROKE WEST B",
    "PEMBROKE WEST C",
    "RATHFARNHAM",
    "RATHMINES EAST A",
    "RATHMINES EAST B",
    "RATHMINES EAST C",
    "RATHMINES EAST D",
    "RATHMINES WEST A",
    "RATHMINES WEST B",
    "RATHMINES WEST C",
    "RATHMINES WEST D",
    "RATHMINES WEST E",
    "RATHMINES WEST F",
    "ROYAL EXCHANGE A",
    "ROYAL EXCHANGE B",
    "SAINT KEVIN'S",
    "SOUTH DOCK",
    "TERENURE A",
    "TERENURE B",
    "TERENURE C",
    "TERENURE D",
    "WOOD QUAY A",
    "WOOD QUAY B"
    ])), "Constituency"] = "DUBLIN BAY SOUTH"
important_data.loc[(important_data["Administrative Region"]=="DUBLIN CITY") & (important_data.Name.isin([
    "ARRAN QUAY A",
    "ARRAN QUAY B",
    "ARRAN QUAY C",
    "ARRAN QUAY D",
    "ARRAN QUAY E",
    "BALLYBOUGH A",
    "BALLYBOUGH B",
    "BOTANIC A",
    "BOTANIC B",
    "BOTANIC C",
    "CABRA EAST A",
    "CABRA EAST B",
    "CABRA EAST C",
    "CABRA WEST A",
    "CABRA WEST B",
    "CABRA WEST C",
    "CABRA WEST D",
    "DRUMCONDRA SOUTH A",
    "DRUMCONDRA SOUTH B",
    "DRUMCONDRA SOUTH C",
    "INNS QUAY A",
    "INNS QUAY B",
    "INNS QUAY C",
    "MOUNTJOY A",
    "MOUNTJOY B",
    "NORTH CITY",
    "NORTH DOCK A",
    "NORTH DOCK B",
    "NORTH DOCK C",
    "ROTUNDA A",
    "ROTUNDA B"
    ])), "Constituency"] = "DUBLIN CENTRAL"
important_data.loc[(important_data["Administrative Region"]=="FINGAL") & (important_data.Name.isin([
    "DONABATE",
    "KINSALEY",
    "MALAHIDE EAST",
    "MALAHIDE WEST",
    "PORTMARNOCK NORTH",
    "PORTMARNOCK SOUTH",
    "SWORDS-FORREST",
    "SWORDS-GLASMORE",
    "SWORDS-LISSENHALL",
    "SWORDS-SEATOWN",
    "SWORDS VILLAGE"
    ])), "Constituency"] = "DUBLIN FINGAL EAST"
important_data.loc[(important_data["Administrative Region"]=="FINGAL") & (important_data.Name.isin([
    "AIRPORT",
    "BALBRIGGAN RURAL",
    "BALBRIGGAN URBAN",
    "BALLYBOGHIL",
    "BALSCADDEN",
    "CLONMETHAN",
    "DUBBER",
    "GARRISTOWN",
    "HOLLYWOOD",
    "HOLMPATRICK",
    "KILSALLAGHAN",
    "LUSK",
    "RUSH",
    "SKERRIES",
    "TURNAPIN"
    ])), "Constituency"] = "DUBLIN FINGAL WEST"
important_data.loc[(important_data["Administrative Region"]=="SOUTH DUBLIN") & (important_data.Name.isin([
    "CLONDALKIN-CAPPAGHMORE",
    "CLONDALKIN-DUNAWLEY",
    "CLONDALKIN-MONASTERY",
    "CLONDALKIN-MOORFIELD",
    "CLONDALKIN-ROWLAGH",
    "CLONDALKIN VILLAGE",
    "LUCAN-ESKER",
    "LUCAN HEIGHTS",
    "LUCAN-St. HELENS",
    "NEWCASTLE",
    "PALMERSTON VILLAGE",
    "PALMERSTON WEST",
    "RATHCOOLE",
    "SAGGART",
    "TALLAGHT-FETTERCAIRN"
    ])), "Constituency"] = "DUBLIN MID-WEST"
important_data.loc[(important_data["Administrative Region"]=="DUBLIN CITY") & (important_data.Name.isin([
    "BALLYGALL A",
    "BALLYGALL B",
    "BALLYGALL C",
    "BALLYGALL D",
    "BALLYMUN A",
    "BALLYMUN B",
    "BALLYMUN C",
    "BALLYMUN D",
    "BALLYMUN E",
    "BALLYMUN F",
    "BEAUMONT A",
    "BEAUMONT B",
    "BEAUMONT F",
    "FINGLAS NORTH A",
    "FINGLAS NORTH B",
    "FINGLAS NORTH C",
    "FINGLAS SOUTH A",
    "FINGLAS SOUTH B",
    "FINGLAS SOUTH C",
    "FINGLAS SOUTH D",
    "KILMORE A",
    "WHITEHALL A",
    "WHITEHALL B",
    "WHITEHALL C",
    "WHITEHALL D"
    ])), "Constituency"] = "DUBLIN NORTH-WEST"
important_data.loc[(important_data["Administrative Region"]=="DUN LAOGHAIRE/RATHDOWN") & (important_data.Name.isin([
    "BALLINTEER-BROADFORD",
    "BALLINTEER-LUDFORD",
    "BALLINTEER-MARLEY",
    "BALLINTEER-MEADOWBROADS",
    "BALLINTEER-MEADOWMOUNT",
    "BALLINTEER-WOODPARK",
    "CHURCHTOWN-CASTLE",
    "CHURCHTOWN-LANDSCAPE",
    "CHURCHTOWN-NUTGROVE",
    "CHURCHTOWN-ORWELL",
    "CHURCHTOWN-WOODLAWN",
    "CLONSKEAGH-BELFIELD",
    "CLONSKEAGH-FARRANBOLEY",
    "CLONSKEAGH-MILLTOWN",
    "CLONSKEAGH-ROEBUCK",
    "CLONSKEAGH-WINDY ARBOUR",
    "DUNDRUM-BALALLY",
    "DUNDRUM-KILMACUD",
    "DUNDRUM-SANDYFORD",
    "DUNDRUM-SWEETMOUNT",
    "DUNDRUM-TANEY",
    "FOXROCK-CARRICKMINES",
    "FOXROCK-TORQUAY",
    "GLENCULLEN",
    "STILLORGAN-DEERPARK",
    "STILLORGAN-KILMACUD",
    "STILLORGAN-LEOPARDSTOWN",
    "STILLORGAN-MERVILLE",
    "STILLORGAN-MOUNT MERRION",
    "TIBRADDEN"
    ])), "Constituency"] = "DUBLIN RATHDOWN"
important_data.loc[(important_data["Administrative Region"]=="DUBLIN CITY") & (important_data.Name.isin([
    "CARNA",
    "CHAPELIZOD",
    "CHERRY ORCHARD A",
    "CHERRY ORCHARD C",
    "CRUMLIN A",
    "CRUMLIN B",
    "CRUMLIN C",
    "CRUMLIN D",
    "CRUMLIN E",
    "CRUMLIN F",
    "DECIES",
    "DRUMFINN",
    "INCHICORE A",
    "INCHICORE B",
    "KILMAINHAM A",
    "KILMAINHAM B",
    "KILMAINHAM C",
    "KIMMAGE A",
    "KIMMAGE B",
    "KIMMAGE C",
    "KIMMAGE D",
    "KIMMAGE E",
    "KYLEMORE",
    "MERCHANTS QUAY A",
    "MERCHANTS QUAY B",
    "MERCHANTS QUAY C",
    "MERCHANTS QUAY D",
    "MERCHANTS QUAY E",
    "MERCHANTS QUAY F",
    "USHERS A",
    "USHERS B",
    "USHERS C",
    "USHERS D",
    "USHERS E",
    "USHERS F",
    "WALKINSTOWN A",
    "WALKINSTOWN B",
    "WALKINSTOWN C"
    # EC report & government map seemingly has all of Phoenix Park ED in Dublin West Constituency?
    ])), "Constituency"] = "DUBLIN SOUTH-CENTRAL"
important_data.loc[(important_data["Administrative Region"]=="SOUTH DUBLIN") & (important_data.Name.isin([
    "BALLINASCORNEY",
    "BALLYBODEN",
    "BOHERNABREENA",
    "CLONDALKIN-BALLYMOUNT",
    "EDMONDSTOWN",
    "FIRHOUSE-BALLYCULLEN",
    "FIRHOUSE-KNOCKLYON",
    "FIRHOUSE VILLAGE",
    "RATHFARNHAM-BALLYROAN",
    "RATHFARNHAM-BUTTERFIELD",
    "RATHFARNHAM-HERMITAGE",
    "RATHFARNHAM-St. ENDA'S",
    "RATHFARNHAM VILLAGE",
    "TALLAGHT-AVONBEG",
    "TALLAGHT-BELGARD",
    "TALLAGHT-GLENVIEW",
    "TALLAGHT-JOBSTOWN",
    "TALLAGHT-KILLINARDAN",
    "TALLAGHT-KILNAMANAGH",
    "TALLAGHT-KILTIPPER",
    "TALLAGHT-KINGSWOOD",
    "TALLAGHT-MILLBROOK",
    "TALLAGHT-OLDBAWN",
    "TALLAGHT-SPRINGFIELD",
    "TALLAGHT-TYMON",
    "TEMPLEOGUE-CYPRESS",
    "TEMPLEOGUE-KIMMAGE MANOR",
    "TEMPLEOGUE-LIMEKILN",
    "TEMPLEOGUE-ORWELL",
    "TEMPLEOGUE-OSPREY",
    "TEMPLEOGUE VILLAGE",
    "TERENURE-CHERRYFIELD",
    "TERENURE-GREENTREES",
    "TERENURE-St. JAMES"
    ])), "Constituency"] = "DUBLIN SOUTH-WEST"
important_data.loc[((important_data["Administrative Region"]=="FINGAL") & (important_data.Name.isin([
    "BLANCHARDSTOWN-ABBOTSTOWN",
    "BLANCHARDSTOWN-BLAKESTOWN",
    "BLANCHARDSTOWN-COOLMINE",
    "BLANCHARDSTOWN-CORDUFF",
    "BLANCHARDSTOWN-DELWOOD",
    "BLANCHARDSTOWN-MULHUDDART",
    "BLANCHARDSTOWN-ROSELAWN",
    "BLANCHARDSTOWN-TYRRELSTOWN",
    "CASTLEKNOCK-KNOCKMAROON",
    "CASTLEKNOCK-PARK",
    "LUCAN NORTH",
    "THE WARD"
    ]))) | ((important_data["Administrative Region"]=="DUBLIN CITY") & (important_data.Name.isin([
    "ASHTOWN A",
    "ASHTOWN B",
    "PHOENIX PARK" # EC report & government map seemingly has all of Phoenix Park ED in Dublin West Constituency?
    ]))), "Constituency"] = "DUBLIN WEST"
important_data.loc[(important_data["Administrative Region"]=="DUN LAOGHAIRE/RATHDOWN") & (important_data.Name.isin([
    "BALLYBRACK",
    "BLACKROCK-BOOTERSTOWN",
    "BLACKROCK-CARYSFORT",
    "BLACKROCK-CENTRAL",
    "BLACKROCK-GLENOMENA",
    "BLACKROCK-MONKSTOWN",
    "BLACKROCK-NEWPARK",
    "BLACKROCK-SEAPOINT",
    "BLACKROCK-STRADBROOK",
    "BLACKROCK-TEMPLEHILL",
    "BLACKROCK-WILLIAMSTOWN",
    "CABINTEELY-GRANITEFIELD",
    "CABINTEELY-KILBOGGET",
    "CABINTEELY-LOUGHLINSTOWN",
    "CABINTEELY-POTTERY",
    "DALKEY-AVONDALE",
    "DALKEY-BULLOCK",
    "DALKEY-COLIEMORE",
    "DALKEY HILL",
    "DALKEY UPPER",
    "DUN LAOGHAIRE-EAST CENTRAL",
    "DUN LAOGHAIRE-GLASTHULE",
    "DUN LAOGHAIRE-GLENAGEARY",
    "DUN LAOGHAIRE-MONKSTOWN FARM",
    "DUN LAOGHAIRE-MOUNT TOWN",
    "DUN LAOGHAIRE SALLYNOGGIN EAST",
    "DUN LAOGHAIRE SALLYNOGGIN SOUTH",
    "DUN LAOGHAIRE-SALLYNOGGIN WEST",
    "DUN LAOGHAIRE-SALTHILL",
    "DUN LAOGHAIRE-SANDYCOVE",
    "DUN LAOGHAIRE-WEST CENTRAL",
    "FOXROCK-BEECHPARK",
    "FOXROCK-DEANSGRANGE",
    "KILLINEY NORTH",
    "KILLINEY SOUTH",
    "SHANKILL-RATHMICHAEL",
    "SHANKILL-RATHSALLAGH",
    "SHANKILL-SHANGANAGH",
    "STILLORGAN-PRIORY"
    ])), "Constituency"] = "DÚN LAOGHAIRE"
important_data.loc[(important_data["Administrative Region"]=="GALWAY") & ((important_data.Name.isin([
    "ABBEYGORMACAN",
    "AUGHRIM",
    "BALLYMACWARD",
    "CLONFERT",
    "CLONTUSKERT",
    "KILCONNELL",
    "KILLAAN",
    "KILLALLAGHTAN",
    "KILLORAN",
    "KILMACSHANE",
    "KILTORMER",
    "LAURENCETOWN",
    "OATFIELD",
    # Aughrim EDs already included
    "BELLEVILLE",
    "DEERPARK",
    "STRADBALLY",
    "ARDAMULLIVAN",
    "ARDRAHAN",
    "BALLYCAHALAN",
    "BEAGH",
    "CAHERMORE",
    "CAPPARD",
    "CASTLETAYLOR",
    "DOORUS",
    "DRUMACOO",
    "GORT",
    "KILBEACANTY",
    "KILLEELY",
    "KILLEENAVARRA",
    "KILLINNY",
    "KILTARTAN",
    "KILTHOMAS",
    "KINVARRA",
    "RAHASANE",
    "SKEHANAGH",
    "BALLINASTACK",
    "BOYOUNAGH",
    "CURRAGHMORE",
    "GLENNAMADDY",
    "KILTULLAGH",
    "RAHEEN",
    "SCREGG",
    "SHANKILL",
    "TEMPLETOGHER",
    "AILLE",
    "ATHENRY",
    "BALLYNAGAR",
    "BRACKLAGH",
    "BULLAUN",
    "CAPPALUSK",
    "CASTLEBOY",
    "CLOONKEEN",
    "COLMANSTOWN",
    "CRAUGHWELL",
    "DERRYLAUR",
    "DRUMKEARY",
    "GRAIGABBEY",
    "GRANGE",
    "GREETHILL",
    "KILCHREEST",
    "KILCONICKNY",
    "KILCONIERIN",
    "KILLIMOR",
    "KILLOGILLEEN",
    "KILMEEN",
    "KILREEKILL",
    "KILTESKILL",
    # Kiltullagh EDs already included
    "LACKALEA",
    "LEITRIM",
    "LOUGHATORICK/COOS/MARBLEHILL", # amalgated ED in CSO data
    "LOUGHREA RURAL",
    "LOUGHREA URBAN",
    # Marblehill ED already included
    "MOUNTAIN",
    "MOYODE",
    "RAFORD",
    "TIAQUIN",
    "WOODFORD",
    "ANNAGH",
    # multiple Ballynakills in Galway - added via GUID below
    "CALTRA",
    "CASTLEBLAKENEY",
    "CLONBROCK",
    # Cloonkeen EDs already included
    "COOLOO",
    "DERRYGLASSAUN",
    "KILLIAN",
    "MOUNT BELLEW",
    "MOUNTHAZEL",
    "ABBEYVILLE",
    "BALLYGLASS",
    # Coos ED already included
    "DERREW",
    "DRUMMIN",
    "EYRECOURT",
    # Killimor EDs already included
    "KILMALINOGE",
    "KILQUAIN",
    "MEELICK",
    "MOAT",
    "PALLAS",
    "PORTUMNA",
    "TIRANASCRAGH",
    "TYNAGH",
    "ABBEY EAST",
    "ABBEY WEST",
    "ADDERGOOLE",
    # multiple Annaghdowns in Galway - added via GUID below
    "BALLINDERRY",
    "BALLINDUFF",
    "BALLYNAPARK",
    "BEAGHMORE",
    "BELCLARE",
    "CARROWNAGUR",
    "CARROWREVAGH",
    "CLARETUAM",
    "CLONBERN",
    # Cloonkeen EDs already included
    "CUMMER",
    "DONAGHPATRICK",
    "DOONBALLY",
    "DUNMORE NORTH",
    "DUNMORE SOUTH",
    "FOXHALL",
    "HEADFORD",
    "HILLSBROOK",
    "KILBENNAN",
    "KILCOONA",
    "KILLEANY",
    "KILLEEN",
    "KILLERERIN",
    "KILLOWER",
    "KILLURSA",
    "KILMOYLAN",
    "KILSHANVY",
    "LEVALLY",
    "MILLTOWN",
    "MONIVEA",
    "MOYNE",
    "RYEHILL",
    "TOBERADOSH",
    "TUAM RURAL",
    "TUAM URBAN"
    ])) | (important_data.GUID.isin([
    "2ae19629-208b-13a3-e055-000000000001", # Ballynakill
    "2ae19629-2059-13a3-e055-000000000001" # Annaghdown
    ]))), "Constituency"] = "GALWAY EAST"
important_data.loc[(important_data["Administrative Region"]=="GALWAY CITY") | ((important_data["Administrative Region"]=="GALWAY") & ((important_data.Name.isin([
    "OWENGOWLA",
    "KNOCKBOY",
    "ILLION",
    # multiple Ballynakills in Galway - added via GUID below
    "BENCORR",
    "BUNOWEN",
    "CLEGGAN",
    "CLIFDEN",
    "ROUNDSTONE",
    "Crump Island", # Cuskillary seemingly called Crump Island in CSO data?
    "DERRYLEA/DERRYCUNLAGH", # amalgated ED in CSO data
    "DOONLOUGHAN",
    "ERRISLANNAN",
    "INISHBOFIN",
    "MOYRUS",
    "RINVYLE",
    "SKANNIVE",
    "SILLERNA",
    "CARNMORE",
    "SPIDDLE",
    "INISHMORE",
    "CLAREGALWAY",
    "BALLINTEMPLE",
    "BALLYNACOURTY",
    "BARNA",
    "CARROWBROWNE",
    "KILLANNIN",
    "CLARINBRIDGE",
    # multiple Annaghdowns in Galway - added via GUID below
    "GALWAY RURAL",
    "KILCUMMIN",
    "LACKAGHBEG",
    "LISCANANAUN",
    "LISHEENAVALLA",
    "MOYCULLEN",
    "FURBOGH",
    "ORANMORE",
    "SELERNA", "SILLERNA",
    "SLIEVEANEENA",
    "TULLOKYNE",
    "CUR",
    "CRUMPAUN",
    "CLOONBUR",
    "CONG/ROSS", # amalgated ED in CSO data
    "TURLOUGH",
    "CAMUS",
    # Kilcummin EDs already included
    # Conga ED already included
    "GORUMNA",
    "LETTERBRICKAUN",
    "LETTERMORE",
    "LETTERFORE",
    "OUGHTERARD",
    "WORMHOLE"
    ])) | (important_data.GUID.isin([
    "2ae19629-208c-13a3-e055-000000000001", # Ballynakill
    "2ae19629-204f-13a3-e055-000000000001" # Annaghdown
    ])))), "Constituency"] = "GALWAY WEST" # TODO FIND CUSHKILLARY, SILERNA/SILLERNA
important_data.loc[(important_data["Administrative Region"]=="KILDARE") & ((important_data.Name.isin([
    "BALRAHEEN",
    "CELBRIDGE",
    # multiple Cloncurries in Kildare - added via GUID below
    "DONADEA",
    "DONAGHCUMPER",
    "KILCOCK",
    "LEIXLIP",
    "MAYNOOTH",
    "STRAFFAN",
    "BALLYNADRUMNY",
    "CADAMSTOWN",
    "DUNFIERTH",
    "BODENSTOWN",
    "CLANE",
    "CARRAGH",
    "DONORE",
    "DOWNINGS",
    "KILL",
    "KILLASHEE",
    "KILTEEL",
    "LADYTOWN",
    "NAAS RURAL",
    "NEWTOWN",
    "OUGHTERARD",
    "RATHMORE",
    "TIMAHOE NORTH",
    "NAAS URBAN"
    ])) | (important_data.GUID=="2ae19629-229a-13a3-e055-000000000001")), "Constituency"] = "KILDARE NORTH"
important_data.loc[(important_data["Administrative Region"].isin(["LIMERICK", "LIMERICK CITY"])) & (important_data.Name.isin([
    "ABBEY A",
    "ABBEY B",
    "ABBEY C",
    "ABBEY D",
    "BALLINACURRA A",
    "BALLINACURRA B",
    "BALLYNANTY",
    "CASTLE A",
    "CASTLE B",
    "CASTLE C",
    "CASTLE D",
    "COOLRAINE",
    "CUSTOM HOUSE",
    "DOCK A",
    "DOCK B",
    "DOCK C",
    "DOCK D",
    "FARRANSHONE",
    "GALVONE A",
    "GALVONE B",
    "GLENTWORTH A",
    "GLENTWORTH B",
    "GLENTWORTH C",
    "JOHN'S A",
    "JOHN'S B",
    "JOHN'S C",
    "KILLEELY A",
    "KILLEELY B",
    "MARKET",
    "PROSPECT A",
    "PROSPECT B",
    "RATHBANE",
    "SHANNON A",
    "SHANNON B",
    "SINGLAND A",
    "SINGLAND B",
    "St. LAURENCE",
    "ABINGTON",
    "BALLYBRICKEN",
    "BALLYCUMMIN",
    "BALLYSIMON",
    "BALLYVARRA",
    "CAHERCONLISH EAST",
    "CAHERCONLISH WEST",
    "CASTLECONNELL",
    "CLONKEEN",
    "GLENSTAL",
    "LIMERICK NORTH RURAL",
    "LIMERICK SOUTH RURAL",
    "ROXBOROUGH"
    ])), "Constituency"] = "LIMERICK CITY"
important_data.loc[(important_data["Administrative Region"]=="LOUTH") | ((important_data["Administrative Region"]=="MEATH") & (important_data.Name=="St. MARY'S")), "Constituency"] = "LOUTH" # St. Mary's (part) listed in County Louth in CSO data, St. Mary's also seemingly in actual Louth constituency but not mentioned in the Act?
important_data.loc[(important_data["Administrative Region"]=="MEATH") & (important_data.Name.isin([
    "DRUMCONDRA",
    "GRANGEGEETH",
    "KILLARY",
    "CULMULLIN",
    "DONAGHMORE",
    "DUNBOYNE",
    "DUNSHAUGHLIN",
    "KILBREW",
    "KILLEEN",
    "KILMORE",
    "RATHFEIGH",
    "RATOATH",
    "RODANSTOWN",
    "SKREEN",
    "ARDAGH",
    "CARRICKLECK",
    "CEANANNAS MÓR RURAL",
    "CRUICETOWN",
    "KILMAINHAM",
    "MAPERATH",
    "MOYBOLGUE",
    "MOYNALTY",
    "NEWCASTLE",
    "NEWTOWN",
    "NOBBER",
    "POSSECKSTOWN",
    "STAHOLMOG",
    "TROHANNY",
    "ARDCATH",
    "DULEEK",
    "JULIANSTOWN",
    "MELLIFONT",
    "STAMULLIN",
    "ARDMULCHAN",
    "CASTLETOWN",
    "DONAGHPATRICK",
    "KENTSTOWN",
    "PAINESTOWN",
    "RATHKENNY",
    "SLANE",
    "STACKALLAN",
    "TARA",
    "CEANANNAS MÓR URBAN" # typo in Act
    ])), "Constituency"] = "MEATH EAST"
important_data.loc[(important_data["Administrative Region"].isin(["SLIGO", "LEITRIM"])) | ((important_data["Administrative Region"]=="DONEGAL") & (important_data.Name.isin([
    "BALLINTRA",
    "BALLYSHANNON RURAL",
    "BALLYSHANNON URBAN",
    "BUNDORAN RURAL",
    "CARRICKBOY",
    "CAVANGARDEN",
    "CLIFF",
    # Ballintra EDs already included
    "BUNDORAN URBAN"
    ]))), "Constituency"] = "SLIGO-LEITRIM"
important_data.loc[((important_data["Administrative Region"]=="NORTH TIPPERARY") & (important_data.Name.isin([
    "AGLISHCLOGHANE",
    "BALLINGARRY",
    "BALLYLUSKY",
    "BORRISOKANE",
    "CARRIG",
    "CLOGHJORDAN",
    "CLOGHPRIOR",
    "CLOHASKIN",
    "FINNOE",
    "GRAIGUE",
    "KILBARRON",
    "LORRHA EAST",
    "LORRHA WEST",
    "MERTONHALL",
    "RATHCABBAN",
    "REDWOOD",
    "RIVERSTOWN",
    "TERRYGLASS",
    "USKANE",
    "ABINGTON",
    "AGHNAMEADLE",
    "ARDCRONY",
    "BALLINA",
    "BALLYGIBBON",
    "BALLYMACKEY",
    "BALLYNACLOGH",
    "BIRDHILL",
    "BURGESBEG",
    "CARRIGATOGHER",
    "CASTLETOWN",
    "DERRYCASTLE",
    "DOLLA",
    "KILCOMENTY",
    "KILKEARY",
    "KILLOSCULLY",
    "KILMORE",
    "KILNANEAVE",
    "KILNARATH",
    "KNIGH",
    "LACKAGH/GREENHALL", # amalgated ED in CSO data, Greenhall seemingly in actual Tipperary North constituency but not mentioned in the Act?
    "LATTERAGH",
    "MONSEA",
    "NENAGH RURAL",
    "NEWPORT",
    "TEMPLEDERRY",
    "YOUGHALARRA",
    "BORRISNAFARNEY",
    "BORRISNOE",
    "BOURNEY EAST",
    "BOURNEY WEST",
    "KILLAVINOGE",
    "KILLEA",
    "RATHNAVEOGE",
    "ROSCREA",
    "TIMONEY",
    "BALLYCAHILL",
    "BORRISOLEIGH",
    "DROM",
    "FOILNAMAN",
    "GLENKEEN",
    "GORTKELLY",
    "HOLYCROSS",
    "INCH",
    "KILRUSH",
    "LITTLETON",
    "LONGFORDPASS",
    "LOUGHMORE",
    "MOYALIFF",
    "MOYCARKY",
    "MOYNE",
    "RAHELTY",
    "TEMPLETOUHY",
    "THURLES RURAL",
    "TWO-MILE-BORRIS",
    "UPPERCHURCH",
    "NENAGH EAST URBAN",
    "NENAGH WEST URBAN",
    "TEMPLEMORE",
    "THURLES URBAN"
    ]))) | ((important_data["Administrative Region"]=="SOUTH TIPPERARY") & (important_data.Name.isin([
    "CLOGHER",
    "CLONOULTY EAST",
    "CLONOULTY WEST",
    "GAILE",
    "BUOLICK",
    "FENNOR",
    "KILCOOLY",
    "CAPPAGH",
    "CURRAHEEN",
    "DONOHILL",
    "GLENGAR"
    ]))) | ((important_data["Administrative Region"]=="KILKENNY") & (important_data.Name.isin([
    "BALLYBEAGH",
    "FRESHFORD",
    "RATHEALY",
    "TULLAROAN",
    "BALLEEN",
    "BAUNMORE",
    "CLOMANTAGH",
    "GALMOY",
    "GLASHARE",
    "JOHNSTOWN",
    "LISDOWNEY",
    "TUBBRIDBRITTAIN",
    "URLINGFORD"
    ]))), "Constituency"] = "TIPPERARY NORTH" # need to specify North/South Tipperary county - mixture of North/South Tipperary counties in Tipperary South/North constituencies, EDs with same name in North/South Tipperary counties
important_data.loc[((important_data["Administrative Region"]=="WEXFORD") & (important_data.Name.isin([
    "BALLINDAGGAN",
    "BALLYCARNEY",
    "BALLYMORE",
    "CASTLEDOCKRELL",
    "FERNS",
    "KILBORA",
    "KILCORMICK",
    "KILRUSH",
    "MOYACOMB",
    "NEWTOWNBARRY",
    "ROSSARD",
    "St. MARY'S",
    "THE HARROW",
    "TINNACROSS",
    "TOMBRACK",
    "ARDAMINE",
    "BALLOUGHTER",
    "BALLYBEG",
    "BALLYCANEW",
    "BALLYELLIS",
    "BALLYGARRETT",
    "BALLYLARKIN",
    "BALLYNESTRAGH",
    "CAHORE",
    "COOLGREANY",
    "COURTOWN",
    "FORD",
    "GOREY RURAL",
    "GOREY URBAN",
    "HUNTINGTOWN",
    "KILCOMB",
    "KILGORMAN",
    "KILLENAGH",
    "KILLINCOOLY",
    "KILNAHUE",
    "LIMERICK",
    "MONAMOLIN",
    "MONASEED",
    "ROSSMINOGE",
    "WELLS",
    "WINGFIELD"
    ]))) | ((important_data["Administrative Region"]=="WICKLOW") & ((important_data.Name.isin([
    "ARKLOW RURAL",
    "AUGHRIM",
    "BALLINACLASH",
    "BALLINACOR",
    "BALLINDERRY",
    "BALLYARTHUR",
    "CRONEBANE",
    "DUNGANSTOWN EAST",
    "DUNGANSTOWN SOUTH",
    "DUNGANSTOWN WEST",
    "ENNEREILLY",
    # multiple Kilbrides in Wicklow - added via GUID below
    "OVOCA",
    "RATHDRUM",
    "AGHOWLE",
    "BALLINGATE",
    "BALLINGLEN",
    "BALLYBEG",
    "CARNEW",
    "COOLATTIN",
    "COOLBOY",
    "CRONELEA",
    "KILBALLYOWEN",
    "KILLINURE",
    "KILPIPE",
    "MONEY",
    "RATH",
    "SHILLELAGH",
    "TINAHELY",
    "ARKLOW No. 1 URBAN",
    "ARKLOW No. 2 URBAN"
    ])) | (important_data.GUID=="2ae19629-1e60-13a3-e055-000000000001"))), "Constituency"] = "WICKLOW-WEXFORD"
print("Manual-entry constituency data added.")

# Complements
important_data.loc[(important_data["Administrative Region"]=="CARLOW") | ((important_data["Administrative Region"]=="KILKENNY") & (important_data.Constituency!="TIPPERARY NORTH")), "Constituency"] = "CARLOW-KILKENNY"
important_data.loc[(important_data["Administrative Region"]=="CORK") & ~(important_data.Constituency.isin(["CORK EAST", "CORK NORTH-CENTRAL", "CORK NORTH-WEST", "CORK SOUTH-CENTRAL"])), "Constituency"] = "CORK SOUTH-WEST"
important_data.loc[(important_data["Administrative Region"]=="DONEGAL") & (important_data.Constituency!="SLIGO-LEITRIM"), "Constituency"] = "DONEGAL"
important_data.loc[(important_data["Administrative Region"]=="KILDARE") & (important_data.Constituency!="KILDARE NORTH"), "Constituency"] = "KILDARE SOUTH"
important_data.loc[(important_data["Administrative Region"].isin(["LIMERICK", "LIMERICK CITY"])) & (important_data.Constituency!="LIMERICK CITY"), "Constituency"] = "LIMERICK COUNTY"
important_data.loc[(important_data["Administrative Region"]=="MEATH") & ~(important_data.Constituency.isin(["LOUTH", "MEATH EAST"])), "Constituency"] = "MEATH WEST"
important_data.loc[(important_data["Administrative Region"]=="ROSCOMMON") | ((important_data["Administrative Region"]=="GALWAY") & ~(important_data.Constituency.isin(["GALWAY EAST", "GALWAY WEST"]))), "Constituency"] = "ROSCOMMON-GALWAY"
important_data.loc[(important_data["Administrative Region"].isin(["NORTH TIPPERARY", "SOUTH TIPPERARY"])) & (important_data.Constituency!="TIPPERARY NORTH"), "Constituency"] = "TIPPERARY SOUTH"
important_data.loc[(important_data["Administrative Region"]=="WEXFORD") & (important_data.Constituency!="WICKLOW-WEXFORD"), "Constituency"] = "WEXFORD"
important_data.loc[(important_data["Administrative Region"]=="WICKLOW") & (important_data.Constituency!="WICKLOW-WEXFORD"), "Constituency"] = "WICKLOW"
print("Complement constituency data added.")

# Saving to .csv
important_data.to_csv(os.path.join(data_dir, "ED_data.csv"), columns=["GUID", "Name", "County", "Administrative Region", "Constituency", "LEA", "Population", "Area", "Perimeter", "Neighbours"], index=False)
print("Data saved to ED_data.csv.")


# Making and saving dataframe for constituency data (seats per constituency)
# TODO extend this further - get geojson for constituency boundaries and repeat above
constituency_data = pd.DataFrame([
    ("CARLOW-KILKENNY", 5),
    ("CAVAN-MONAGHAN", 5),
    ("CLARE", 4),
    ("CORK EAST", 4),
    ("CORK NORTH-CENTRAL", 5),
    ("CORK NORTH-WEST", 3),
    ("CORK SOUTH-CENTRAL", 5),
    ("CORK SOUTH-WEST", 3),
    ("DONEGAL", 5),
    ("DUBLIN BAY NORTH", 5),
    ("DUBLIN BAY SOUTH", 4),
    ("DUBLIN CENTRAL", 4),
    ("DUBLIN FINGAL EAST", 3),
    ("DUBLIN FINGAL WEST", 3),
    ("DUBLIN MID-WEST", 5),
    ("DUBLIN NORTH-WEST", 3),
    ("DUBLIN RATHDOWN", 4),
    ("DUBLIN SOUTH-CENTRAL", 4),
    ("DUBLIN SOUTH-WEST", 5),
    ("DUBLIN WEST", 5),
    ("DÚN LAOGHAIRE", 4),
    ("GALWAY EAST", 4),
    ("GALWAY WEST", 5),
    ("KERRY", 5),
    ("KILDARE NORTH", 5),
    ("KILDARE SOUTH", 4),
    ("LAOIS", 3),
    ("LIMERICK CITY", 4),
    ("LIMERICK COUNTY", 3),
    ("LONGFORD-WESTMEATH", 5),
    ("LOUTH", 5),
    ("MAYO", 5),
    ("MEATH EAST", 4),
    ("MEATH WEST", 3),
    ("OFFALY", 3),
    ("ROSCOMMON-GALWAY", 3),
    ("SLIGO-LEITRIM", 4),
    ("TIPPERARY NORTH", 3),
    ("TIPPERARY SOUTH", 3),
    ("WATERFORD", 4),
    ("WEXFORD", 4),
    ("WICKLOW", 4),
    ("WICKLOW-WEXFORD", 3)
    ], columns=["Constituency", "Seats"])

constituency_data.to_csv(os.path.join(data_dir, "Constituency_data.csv"), index=False)
print("Data saved to Constituency_data.csv.")
