from typing import Tuple, List, Dict 
import sys
import os
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib.patches as mpatches
from collections import Counter
from shapely.ops import unary_union

def get_paths(area_name: str) -> Tuple[str, str]: # Returns i. data directory and ii. area directories
    repo_data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir, "data")
    data_dir = os.path.abspath(repo_data_dir)
    area_dir = os.path.join(data_dir, area_name)
    if not os.path.isdir(area_dir):
        raise FileNotFoundError(f"Area directory not found: {area_dir}")
    return data_dir, area_dir

def read_guid_list(area_dir: str, global_geo_path: str) -> Tuple[pd.DataFrame, List[str]]: #Returns i. GeoDataFrame restricted to area's EDs and ii. ordered GUID list
    geo = gpd.read_file(global_geo_path)[["ED_GUID", "geometry"]].rename(columns={"ED_GUID": "GUID"})
    guid_txt = os.path.join(area_dir, "GUID.txt")
    if not os.path.exists(guid_txt):
        raise FileNotFoundError(f"GUID.txt missing in {area_dir}")
    guids = np.loadtxt(guid_txt, dtype=str).tolist()
    # subset and reindex to preserve C++ ordering
    geo = geo[geo.GUID.isin(guids)].set_index("GUID").reindex(index=guids).reset_index()
    return geo, guids

def load_configs(area_dir: str) -> Tuple[pd.DataFrame, List[str]]: #Returns i. DataFrame of MCMC time series data and ii. list of header lines (Q,N,J,initial,optimals, etc.)
    cfg_path = os.path.join(area_dir, "configs.csv")
    if not os.path.exists(cfg_path):
        raise FileNotFoundError(f"{cfg_path} not found")
    with open(cfg_path, "r", encoding="utf-8") as f:
        lines = [ln.rstrip("\n") for ln in f if ln.strip()]
    # Data starts after the header line that starts with "T,"
    data_df = None
    header_idx = next(i for i, ln in enumerate(lines) if ln.strip().startswith("T,"))
    data_df = pd.read_csv(cfg_path, skiprows=header_idx)
    return data_df, lines

def parse_config_header(lines: List[str], prefix: str) -> List[str]: # Find line beginning with given prefix and return comma-separated values after 
    ln = next((l for l in lines if l.strip().lower().startswith(prefix.lower() + ",")), None)
    return [] if ln is None else [s.strip() for s in ln.split(",")[1:]]

def read_initial_and_final_assignments(area_dir: str): #Returns i. initial assignments list and ii. final assignments list from configs.csv
    cfg_path = os.path.join(area_dir, "configs.csv")

    initial = None
    optimals = None

    with open(cfg_path, "r", encoding="utf-8") as f:
        lines = iter(f)
        for line in lines:
            line = line.strip()

            if line == "initial":
                initial = [int(x) for x in next(lines).strip().split(",")]

            elif line == "optimals":
                optimals = [int(x) for x in next(lines).strip().split(",")]

            elif line.startswith("T,"):
                break  # stop when MCMC table begins

    if initial is None:
        raise RuntimeError("No 'initial' block found in configs.csv")
    if optimals is None:
        raise RuntimeError("No 'optimals' block found in configs.csv")

    return initial, optimals

def load_gdf_for_area(data_dir: str) -> gpd.GeoDataFrame: #Loads GeoDataFrame for area from 100m.geojson and renames ED_GUID to GUID
    gdf = gpd.read_file(os.path.join(data_dir, "100m.geojson"))
    # normalize GUID field
    if "ED_GUID" in gdf.columns and "GUID" not in gdf.columns:
        gdf = gdf.rename(columns={"ED_GUID": "GUID"})
    return gdf


def plot_final_map(area_dir: str, gdf: gpd.GeoDataFrame, guid_order: List[str], final_assignments: List[int], # Original
                   Q_vals: List[int], info_label: str, constituency_vars: np.ndarray = None,
                   mean_abs_var: float = None, max_abs_var: float = None):

    guid_list = [str(g) for g in guid_order] # Check that GUID list length matches final assignments
    if len(guid_list) > len(final_assignments):
        guid_list = guid_list[: len(final_assignments)]
    elif len(guid_list) < len(final_assignments):
        raise ValueError("GUID list shorter than final assignments — region mismatch")

    assign_df = pd.DataFrame({"GUID": guid_list, "district": final_assignments}) # Attach district
    gdf_assigned = gdf.merge(assign_df, on="GUID", how="left") # Original
    included = gdf_assigned[gdf_assigned["district"].notna()].copy()
    surround = gdf_assigned[gdf_assigned["district"].isna()].copy()

    print(f"Included EDs: {len(included)}; Surrounding EDs: {len(surround)}")

    # Load County.txt and dissolve EDs into county polygons
    county_fp = os.path.join(area_dir, "County.txt")
    county_vals = np.loadtxt(county_fp, dtype=int)
    if county_vals.size != len(guid_list):
        raise RuntimeError("County.txt length doesn't match GUID list")
    county_df = pd.DataFrame({"GUID": guid_list, "CountyID": county_vals})
    merged_cnt = gdf.merge(county_df, on="GUID", how="left")
    county_geoms = []
    county_names = []
    for cid, group in merged_cnt.groupby("CountyID"):
        geom = unary_union(group.geometry).buffer(0)
        county_geoms.append(geom)
        county_names.append(str(int(cid)))
    counties = gpd.GeoDataFrame({"County": county_names, "geometry": county_geoms}, crs=gdf.crs)

    fig, ax = plt.subplots(figsize=(10, 12))
    if len(surround):
        surround.boundary.plot(ax=ax, color="lightgrey", linewidth=0.6, alpha=0.9, zorder=0)

    cmap = plt.get_cmap("tab20")
    unique_ds = sorted(included["district"].astype(int).unique().tolist()) if len(included) else []
    norm = plt.Normalize(vmin=min(unique_ds) if unique_ds else 0, vmax=max(unique_ds) if unique_ds else 0)

    legend_handles = []
    q_counts = Counter(Q_vals) if Q_vals else {}
    q_parts = [f"{seat}-seaters: {cnt} " for seat, cnt in sorted(q_counts.items())]
    legend_handles.append(Line2D([0], [0], color="none", label=info_label))
    legend_handles.append(Line2D([0], [0], color="none", label="Seats composition: \n" + ("\n".join(q_parts) if q_parts else "n/a")))

    district_patches = []
    for d in unique_ds:
        sel = included[included["district"].astype(int) == d]
        color = cmap(norm(d))
        sel.plot(ax=ax, facecolor=color, edgecolor="black", linewidth=0.7, alpha=0.35, zorder=2)
        seat_label = f"{Q_vals[d]} seats" if d < len(Q_vals) else "seats:?"
        # include constituency variance if available
        var_label = ""
        if constituency_vars is not None and d < len(constituency_vars):
            var_label = f"{constituency_vars[d]*100:+.2f}% Pop. |var.|"
        lab = f"Constituency {d}: {seat_label}, {len(sel)} EDs, {var_label}"
        p = mpatches.Patch(facecolor=color, edgecolor="black", alpha=0.35, label=lab)
        district_patches.append(p)

    if len(counties):
        if counties.crs != gdf.crs:
            counties = counties.to_crs(gdf.crs)
        counties.boundary.plot(ax=ax, color="black", linewidth=2.8, zorder=4)
        legend_handles.append(Line2D([0], [0], color="black", lw=3, label="County boundaries"))

    # Add mean and max absolute variance to legend if available
    if mean_abs_var is not None and max_abs_var is not None:
        legend_handles.append(Line2D([0], [0], color="none", label=f"Mean population |variance|: {mean_abs_var*100:.2f}%"))
        legend_handles.append(Line2D([0], [0], color="none", label=f"Max population |variance| : {max_abs_var*100:.2f}%"))

    legend_handles.extend(district_patches)
    ax.legend(handles=legend_handles, title="Map info", loc="lower left", fontsize="small", frameon=True)

    if len(included) and included.geometry.notnull().any():
        minx, miny, maxx, maxy = included.total_bounds
        pad_x = (maxx - minx) * 0.08 if (maxx - minx) > 0 else 0.001
        pad_y = (maxy - miny) * 0.08 if (maxy - miny) > 0 else 0.001
        ax.set_xlim(minx - pad_x, maxx + pad_x)
        ax.set_ylim(miny - pad_y, maxy + pad_y)
    else:
        minx, miny, maxx, maxy = gdf.total_bounds
        ax.set_xlim(minx, maxx)
        ax.set_ylim(miny, maxy)

    ax.set_aspect("equal")
    ax.set_title("Final Constituency Configuration", fontsize=14)
    ax.axis("off")
    plt.tight_layout()
    out_path = os.path.join(area_dir, "final_map.pdf")
    plt.savefig(out_path, dpi=300, bbox_inches="tight", format="pdf")
    plt.close(fig)
    print(f"Wrote {out_path}")


def constituency_variances(ED_population_list, ED_constituency_list, constituency_seat_list):
    # ED_population_list: list of population for each ED.
    # len(ED_population_list) = number of EDs
    # this can be read from Populations.txt

    # ED_constituency_list: list of constituencies that each ED is assigned to.
    # len(ED_constituency_list) = number of EDs
    # can take values 0, 1, ..., number of constituencies
    # for optimal configs, this can be copy-pasted from configs.csv

    # constituency_seat_list: list of number of seats for each constituency.
    # len(constituency_seat_list) = number of constituencies
    # this is the first set of numbers fed into the MCMC_SA executable, e.g. 2,3,3,3 for Midland counties

    # constituency_vars (what this function returns): the variance of each constituency's population from the ideal representation
    # the ideal representation = (number of seats in constituency) * (total population of all EDs) / (total seats of all constituencies)
    # if population = ideal representation then variance = 0
    # a side note: this isn't variance in the statistical sense, i.e. it has nothing to do with sum of squares
    # in this case variance is the percentage difference from the ideal representation
    # i.e. variance = (actual constituency population - ideal constituency population) / (ideal constituency population)

    # getting total population, total number of seats, and total number of EDs
    total_population = np.sum(ED_population_list)
    total_seats = np.sum(constituency_seat_list)
    # number_of_EDs = len(ED_population_list) #Old
    number_of_EDs = len(ED_constituency_list) #fix?


    # getting the population in each constituency
    constituency_population_list = np.zeros(len(constituency_seat_list))
    for i in range(number_of_EDs):
        # constituency of ED i
        ED_constituency = ED_constituency_list[i]
        # add the population of ED i to its constituency
        constituency_population_list[ED_constituency] += ED_population_list[i]
    
    # getting the ideal population for each constituency
    population_per_seat = total_population / total_seats
    ideal_population_list = np.array(constituency_seat_list) * population_per_seat

    # getting the population variance of each constituency
    constituency_vars = (constituency_population_list - ideal_population_list) / ideal_population_list

    return constituency_vars


# ---------- Main ----------

def main(area_name: str):
    data_dir, area_dir = get_paths(area_name)
    # read geo and GUIDs
    global_geo = os.path.join(data_dir, "100m.geojson")
    gdf_geo, guid_order = read_guid_list(area_dir, global_geo)

    # load configs.csv (data and header lines)
    mcmc_df, header_lines = load_configs(area_dir)
    # mcmc_df = compute_beta(mcmc_df)

    # parse Q,N,J from header
    Q_vals = [int(x) for x in parse_config_header(header_lines, "Q")] if parse_config_header(header_lines, "Q") else []
    N_vals = parse_config_header(header_lines, "N")
    J_vals = parse_config_header(header_lines, "J")
    recorded = int(N_vals[0]) if len(N_vals) >= 1 else "n/a"
    discarded = int(N_vals[1]) if len(N_vals) >= 2 else "n/a"
    def safe_float(s): 
        try: return float(s)
        except: return None
    J_nums = [safe_float(v) for v in J_vals]
    J_P, J_C, J_D, J_B = tuple(J_nums[i] if i < len(J_nums) else None for i in range(4))
    info_label = f"Recorded/Discarded = {recorded}/{discarded}\nJ (P,C,D,B) = ({J_P},{J_C},{J_D},{J_B})"

    # read final assignments and base gdf
    _, final_assignments = read_initial_and_final_assignments(area_dir)
    gdf_full = load_gdf_for_area(data_dir)

    # read populations and compute constituency variances
    pops_fp = os.path.join(area_dir, "Population.txt")
    if not os.path.exists(pops_fp):
        raise FileNotFoundError(f"Population.txt not found in {area_dir}")
    pops = np.loadtxt(pops_fp, dtype=float)
    if len(pops) != len(guid_order):
        raise RuntimeError("Population.txt length doesn't match GUID ordering")
    if not Q_vals:
        raise RuntimeError("No Q (seats) found in configs.csv; cannot compute variances")
    constituency_vars = constituency_variances(pops, final_assignments, Q_vals)
    mean_abs_var = float(np.abs(constituency_vars).mean())
    max_abs_var = float(np.abs(constituency_vars).max())

    # H vs beta normalized
    # cols = ["H", "HP", "HC", "HD", "HB"]
    # betas, series_means, Ts = mean_series_by_beta(mcmc_df, cols)
    # plot_H_vs_beta_normalized(area_dir, betas, series_means, info_label)

    # # heat capacity (using mean H and Ts)
    # if "H" in series_means:
    #     mean_H = series_means["H"]
    #     C = compute_heat_capacity_from_means(mean_H, Ts)
    #     plot_heat_capacity(area_dir, betas, C, info_label)
    # else:
    #     print("No mean H series to compute heat capacity from.")

    # # autocorr plots
    # plot_autocorrs(area_dir, mcmc_df, info_label)
    # plot_smoothed_autocorr(area_dir, mcmc_df, info_label)

    # final map
    plot_final_map(area_dir, gdf_full, guid_order, final_assignments, Q_vals, info_label,
                   constituency_vars, mean_abs_var, max_abs_var)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python plot_mcmc_results.py <area_name>")
        sys.exit(1)
    area = sys.argv[1]
    main(area)
