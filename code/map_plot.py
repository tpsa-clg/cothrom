from typing import List, Tuple
import sys
import os
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib.patches as mpatches
from collections import Counter



def get_paths(area_name: str) -> Tuple[str, str]: # Returns data_dir, area_dir
    repo_data_dir = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        os.pardir,
        "data"
    )
    data_dir = os.path.abspath(repo_data_dir)
    area_dir = os.path.join(data_dir, area_name)

    if not os.path.isdir(area_dir):
        raise FileNotFoundError(f"Area directory not found: {area_dir}")

    return data_dir, area_dir


def read_guid_list(area_dir: str, geo_path: str) -> Tuple[gpd.GeoDataFrame, List[str]]: # Reads the geojson (via geo_path) and the GUID.txt list in area_dir, filters and reindexes the GeoDataFrame so rows follow the GUID ordering. Returns GeoDataFrame of GUIDs in order, list of GUID strings
    geo = (
        gpd.read_file(geo_path)[["ED_GUID", "geometry"]]
        .rename(columns={"ED_GUID": "GUID"})
    )

    guid_fp = os.path.join(area_dir, "GUID.txt")
    if not os.path.exists(guid_fp):
        raise FileNotFoundError(f"GUID.txt missing in {area_dir}")

    guids = np.loadtxt(guid_fp, dtype=str).tolist()

    geo = (
        geo[geo.GUID.isin(guids)]
        .set_index("GUID")
        .reindex(guids)
        .reset_index()
    )

    return geo, guids


def load_configs(area_dir: str): # Loads configs.csv, returns (DataFrame, raw_lines) when header starting with 'T,' is found, otherwise returns (None, lines). Parses file lines for later header extraction 
    cfg_path = os.path.join(area_dir, "configs.csv")

    with open(cfg_path, encoding="utf-8") as f:
        lines = [ln.rstrip() for ln in f if ln.strip()]

    header_idx = next(
        (i for i, ln in enumerate(lines) if ln.startswith("T,")),
        None
    )

    if header_idx is None:
        return None, lines

    df = pd.read_csv(cfg_path, skiprows=header_idx)
    return df, lines


def parse_config_header(lines: List[str], prefix: str) -> List[str]: # Extracts header values from configs.csv lines. Finds the first line that starts with `prefix,` and returns the following values as a list of strings.
    ln = next(
        (l for l in lines if l.lower().startswith(prefix.lower() + ",")),
        None
    )
    return [] if ln is None else [s.strip() for s in ln.split(",")[1:]]


def read_initial_and_final_assignments(area_dir: str): # Parses configs.csv to extract initial assignment and a list of final assignments. Scans lines for the literal markers 'initial' and 'optimals', reads following CSV lines as integer lists. 
    cfg = os.path.join(area_dir, "configs.csv")
    lines = [ln.strip() for ln in open(cfg) if ln.strip()]

    initial = None
    optimals = []

    i = 0
    while i < len(lines):
        ln = lines[i]

        if ln == "initial":
            i += 1
            initial = list(map(int, lines[i].split(",")))

        elif ln == "optimals":
            i += 1
            while i < len(lines) and not lines[i][0].isalpha():
                optimals.append(list(map(int, lines[i].split(","))))
                i += 1

        i += 1

    if initial is None or not optimals:
        raise RuntimeError("Invalid configs.csv: missing initial or optimals")

    return initial, optimals


def load_gdf(data_dir: str) -> gpd.GeoDataFrame: # Loads the base GeoDataFrame from `100m.geojson` in data_dir and normalises the GUID column name
    gdf = gpd.read_file(os.path.join(data_dir, "100m.geojson"))
    if "ED_GUID" in gdf.columns and "GUID" not in gdf.columns:
        gdf = gdf.rename(columns={"ED_GUID": "GUID"})
    return gdf

# Geometry helpers

def prepare_assignment_gdf(
    gdf: gpd.GeoDataFrame,
    guid_order: List[str],
    assignments: List[int],
): # Prepares two GeoDataFrames, included (EDs assigned to districts) and surround (unassigned EDs). Aligns GUID order with assignments, validates lengths, merges assignments into `gdf` and splits rows by whether `district` is set
    guid_list = list(map(str, guid_order))

    if len(guid_list) > len(assignments):
        guid_list = guid_list[:len(assignments)]
    elif len(guid_list) < len(assignments):
        raise ValueError("GUID list shorter than assignments")

    assign_df = pd.DataFrame({
        "GUID": guid_list,
        "district": assignments
    })

    gdf_assigned = gdf.merge(assign_df, on="GUID", how="left")
    included = gdf_assigned[gdf_assigned["district"].notna()].copy()
    surround = gdf_assigned[gdf_assigned["district"].isna()].copy()

    return included, surround


def dissolve_counties(
    gdf: gpd.GeoDataFrame,
    area_dir: str,
    guid_order: List[str],
) -> gpd.GeoDataFrame: # Reads `County.txt` for County IDs per GUID, merges with `gdf`, dissolves geometries by county and returns a GeoDataFrame of county polygons
    county_fp = os.path.join(area_dir, "County.txt")
    county_vals = np.loadtxt(county_fp, dtype=int)

    county_df = pd.DataFrame({
        "GUID": guid_order[:len(county_vals)],
        "CountyID": county_vals
    })

    merged = gdf.merge(county_df, on="GUID", how="left")

    counties = (
        merged
        .dropna(subset=["CountyID"])
        .dissolve(by="CountyID")
        .geometry
        .buffer(0)
        .reset_index(drop=True)
    )

    return gpd.GeoDataFrame(geometry=counties, crs=gdf.crs)



def constituency_variances(pops, assignments, seats): # Computes relative population variance per constituency
    pops = np.asarray(pops)
    assignments = np.asarray(assignments)
    seats = np.asarray(seats)

    total_population = pops.sum()
    population_per_seat = total_population / seats.sum()

    constituency_pops = np.bincount(assignments, weights=pops)
    ideal = seats * population_per_seat

    return (constituency_pops - ideal) / ideal


def build_legend(Q_vals, info_label, cvars=None, mean_var=None, max_var=None):
    handles = [Line2D([0], [0], color="none", label=info_label)]

    if Q_vals:
        qc = Counter(Q_vals)
        qtxt = "\n".join(f"{s}-seaters: {c}" for s, c in sorted(qc.items()))
        handles.append(Line2D([0], [0], color="none",
                              label= qtxt))

    if mean_var is not None:
        handles.append(Line2D([0], [0], color="none",
                              label=f"\nMean |pop.var.|: {mean_var*100:.2f}%"))
    if max_var is not None:
        handles.append(Line2D([0], [0], color="none",
                              label=f"Max  |pop.var.|: {max_var*100:.2f}%\n"))

    return handles



def plot_final_map(
    i: int,
    area_dir: str,
    gdf: gpd.GeoDataFrame,
    guid_order: List[str],
    assignments: List[int],
    Q_vals: List[int],
    info_label: str,
    cvars=None,
    mean_var=None,
    max_var=None,
):
    # Merges `assignments` into `gdf` -> included/surround geodataframes -> compute county boundaries -> plot districts with colors and legend
    included, surround = prepare_assignment_gdf(gdf, guid_order, assignments)
    counties = dissolve_counties(gdf, area_dir, guid_order)

    fig, ax = plt.subplots(figsize=(10, 12))

    if len(surround):
        surround.boundary.plot(ax=ax, color="lightgrey", lw=0.6, zorder=0)

    cmap = plt.get_cmap("tab20")
    ds = sorted(included["district"].astype(int).unique())
    norm = plt.Normalize(min(ds), max(ds))

    district_patches = []
    for d in ds:
        sel = included[included["district"] == d]
        color = cmap(norm(d))
        sel.plot(ax=ax, facecolor=color, edgecolor="black",
                 lw=0.7, alpha=0.35, zorder=2)

        label = f"C{d}: {Q_vals[d]} seats, {len(sel)} EDs"
        if cvars is not None:
            label += f", {cvars[d]*100:+.2f}%"

        district_patches.append(
            mpatches.Patch(facecolor=color, edgecolor="black",
                           alpha=0.35, label=label)
        )

    counties.boundary.plot(ax=ax, color="black", lw=2.8, zorder=4)

    legend_handles = build_legend(Q_vals, info_label, cvars, mean_var, max_var)
    legend_handles += district_patches
    ax.legend(handles=legend_handles, loc="lower left", fontsize="small")

    minx, miny, maxx, maxy = included.total_bounds
    pad_x = (maxx - minx) * 0.18
    pad_y = (maxy - miny) * 0.08
    ax.set_xlim(minx - pad_x, maxx + pad_x)
    ax.set_ylim(miny - pad_y, maxy + pad_y)

    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout()

    out = os.path.join(area_dir, f"final_map_{i}.pdf")
    plt.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Wrote {out}")


def plot_final_map_simple(
    i: int,
    area_dir: str,
    gdf: gpd.GeoDataFrame,
    guid_order: List[str],
    assignments: List[int],
): # No legend, no surround

    included, _ = prepare_assignment_gdf(gdf, guid_order, assignments)
    counties = dissolve_counties(gdf, area_dir, guid_order)

    fig, ax = plt.subplots(figsize=(10, 12))
    cmap = plt.get_cmap("tab20")

    ds = sorted(included["district"].astype(int).unique())
    norm = plt.Normalize(min(ds), max(ds))

    for d in ds:
        included[included["district"] == d].plot(
            ax=ax,
            facecolor=cmap(norm(d)),
            edgecolor="black",
            lw=0.7,
            alpha=0.35
        )

    counties.boundary.plot(ax=ax, color="black", lw=2.8)
    minx, miny, maxx, maxy = included.total_bounds
    pad = 0.08
    ax.set_xlim(minx - pad*(maxx-minx), maxx + pad*(maxx-minx))
    ax.set_ylim(miny - pad*(maxy-miny), maxy + pad*(maxy-miny))

    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout()

    out = os.path.join(area_dir, f"final_map_simple_{i}.pdf")
    plt.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Wrote {out}")




def main(area_name: str):
    data_dir, area_dir = get_paths(area_name)
    gdf_geo, guid_order = read_guid_list(
        area_dir, os.path.join(data_dir, "100m.geojson")
    )

    _, header_lines = load_configs(area_dir)

    Q_vals = [int(x) for x in parse_config_header(header_lines, "Q")]
    N_vals = parse_config_header(header_lines, "N")
    J_vals = parse_config_header(header_lines, "J")

    recorded = N_vals[0] if len(N_vals) > 0 else "?"
    discarded = N_vals[1] if len(N_vals) > 1 else "?"

    info_label = (
        f"Discarded sweeps = {discarded}\n"
        f"Recorded sweeps = {recorded}\n \n"
        f"J_P = {J_vals[0]}\n"
        f"J_C = {J_vals[1]}\n"
        f"J_D = {J_vals[2]}\n"
        f"J_B = {J_vals[3]}\n"
    )

    _, final_assignments = read_initial_and_final_assignments(area_dir)
    pops = np.loadtxt(os.path.join(area_dir, "Population.txt"))

    gdf_full = load_gdf(data_dir)

    for i, cfg in enumerate(final_assignments):
        cvars = constituency_variances(pops, cfg, Q_vals)
        plot_final_map(
            i, area_dir, gdf_full, guid_order, cfg,
            Q_vals, info_label,
            cvars,
            float(np.abs(cvars).mean()),
            float(np.abs(cvars).max())
        )
        plot_final_map_simple(i, area_dir, gdf_full, guid_order, cfg)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python map_plot.py <area_name>")
        sys.exit(1)

    main(sys.argv[1])
