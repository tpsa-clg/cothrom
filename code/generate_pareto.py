import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List
import csv
import os
from datetime import datetime
import pandas as pd

# datetime object containing current date and time
now = datetime.now()
dt_string = now.strftime("%d.%m.%Y_%H.%M")
dt_short = now.strftime("%d.%m..%H.%M")
max_workers = max(1, os.cpu_count()-1)

def prepare_actual_configuration(area_name: str, county_list: List[str]):
    subprocess.run([
        "python3",
        "code/txt_for_MCMC.py",
        "County",
        ",".join(county_list),
        area_name,
    ], check=True)

def write_actual_configs_csv(
    area_dir: str,
    seat_list: list[int],
    ed_data_csv: str,
):

    # Load GUID ordering
    guid_path = os.path.join(area_dir, "GUID.txt")
    guids = [g.strip() for g in open(guid_path)]
    guid_index = {g: i for i, g in enumerate(guids)}

    # Load ED data

    df = pd.read_csv(ed_data_csv)
    df = df[df["GUID"].isin(guid_index)]

    # Group EDs by constituency
    groups = {}
    for _, r in df.iterrows():
        groups.setdefault(r["Constituency"], []).append(r["GUID"])

    if len(groups) != len(seat_list):
        raise RuntimeError(
            f"{len(groups)} constituencies but {len(seat_list)} seat counts"
        )

    # Population lookup
    pop_by_guid = dict(zip(df["GUID"], df["Population"]))

    const_stats = []
    for cname, eds in groups.items():
        total_pop = sum(pop_by_guid[g] for g in eds)
        const_stats.append((cname, total_pop))

    # smallest population -> index 0 -> smallest seat count
    const_stats.sort(key=lambda x: x[1])

    if len(const_stats) != len(seat_list):
        raise RuntimeError(
            f"{len(const_stats)} constituencies but {len(seat_list)} seat counts"
        )

    constituency_index = {
        cname: i for i, (cname, _) in enumerate(const_stats)
    }

    assignments = [None] * len(guids)
    for cname, eds in groups.items():
        idx = constituency_index[cname]
        for g in eds:
            assignments[guid_index[g]] = idx

    if any(a is None for a in assignments):
        raise RuntimeError("Unassigned EDs in actual configuration")

    # Write minimal configs.csv for actual config

    cfg_path = os.path.join(area_dir, "configs.csv")
    with open(cfg_path, "w", encoding="utf-8") as f:
        f.write("Q," + ",".join(map(str, seat_list)) + "\n")
        f.write("N,0,0\n")
        f.write("J,0,0,0,0\n")
        f.write("Z,0,0,0\n")
        f.write("initial\n")
        f.write(",".join(map(str, assignments)) + "\n")
        f.write("optimals\n")
        f.write(",".join(map(str, assignments)) + "\n")

    print(f"Wrote ACTUAL configs.csv to {cfg_path}")

from typing import List

def seat_counts(seats: List[int]) -> str: # Return string of counts of 3-,4-,5-seaters
    return "{}-{}-{}".format(
        seats.count(3),
        seats.count(4),
        seats.count(5),
    )


def run_all_MCMC_SA(
    county_list: List[str],
    recorded: int,
    discarded: int,
    seat_config: List[int],
    d_min: float,
    d_max: float,
    n_runs: int,
    k: float,
):


    # Construct d_i values
    if n_runs < 1:
        raise ValueError("n_runs must be >= 1")

    if n_runs == 1:
        d_vals = [d_min]
    else:
        d_vals = [
            d_min + i * (d_max - d_min) / (n_runs - 1)
            for i in range(n_runs)
        ]

    # Convert county list to comma-separated string
    county_str = ",".join(county_list)


    def run_single(d_i: float): # Run single MCMC_SA instance and plot maps, return run_name
        seat_string = ",".join(map(str, seat_config))
        seat_counts_string = seat_counts(seat_config)

        try:
            Jc = k * (1.0 + d_i) / (1.0 - k)
            Jd = d_i
            Jb = 0.0

            coupling_str = f"{Jc},{Jd},{Jb}"

            # Construct run name
            run_name = f"@{dt_short}_{county_str}_d_{d_i:.3f}_k_{k:.3f}_R_{recorded}_D_{discarded}_s_{seat_counts_string}"

            cmd_txt = [
                "python3",
                "code/txt_for_MCMC.py",
                "County",
                county_str,
                run_name,
            ]

            subprocess.run(cmd_txt, check=True)

            cmd_mcmc = [
                "code/MCMC_SA",
                run_name,
                seat_string,
                coupling_str,
                f"{recorded},{discarded}",
            ]

            subprocess.run(cmd_mcmc, check=True)

            cmd_plot = [
                "python3",
                "code/plot.py",
                run_name,
            ]

            subprocess.run(cmd_plot, check=True)

            cmd_map = [
                "python3",
                "code/map_plot.py",
                run_name,
            ]

            subprocess.run(cmd_map, check=True)

            return run_name
        
        except subprocess.CalledProcessError as e:
            print(f"Run {run_name} failed: {e}")
            return None

    
    run_names = []

    with ThreadPoolExecutor(max_workers) as executor: # Run in parallel
        futures = [executor.submit(run_single, d_i) for d_i in d_vals]

        for future in as_completed(futures):
            run_name = future.result()
            run_names.append(run_name)
            print(f"Completed run: {run_name}")

    return run_names



#  Compute and collect H-vectors for a list of MCMC_SA runs.

def collect_H_vectors(
    runs: List[str],
    seat_config: List[int],
    data_dir: str = "data",
    output_file: str = f"@{dt_short}_MCDA_input.csv",
):

    output_path = os.path.join(data_dir, output_file)
    rows = []

    for run_name in runs:
        cfg_path = os.path.join(data_dir, run_name, "configs.csv")
        area_dir = os.path.join(data_dir, run_name)
        
        if not os.path.exists(cfg_path):
            print(f"Missing configs.csv for run {run_name}, skipping")
            continue

        # Run compute_H
        compute_exe = os.path.join("code", "compute_H.exe")
        if not os.path.exists(compute_exe):
            compute_exe = os.path.join("code", "compute_H")

        seat_string = ",".join(map(str, seat_config))
        cmd = [
            compute_exe,
            run_name,          # pass the run folder name (area) so compute_H looks under data/<run_name>/
            seat_string, 
        ]

        # Check that area files exist before invoking compute_H
        pop_fp = os.path.join(area_dir, "Population.txt")
        nei_fp = os.path.join(area_dir, "Neighbours.txt")
        cou_fp = os.path.join(area_dir, "County.txt")
        if not (os.path.exists(pop_fp) and os.path.exists(nei_fp) and os.path.exists(cou_fp)):
            print(f"Missing area files for run {run_name}: {pop_fp}, {nei_fp}, {cou_fp}")
            continue
        
        print("About to run compute_H with:")
        print("area_dir/run_name:", run_name)
        print("seat_config:", seat_string)
        print("cfg_path:", cfg_path)


        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
            )
            print("compute_H stdout:", result.stdout)
            print("compute_H stderr:", result.stderr)

            if result.stderr:
                print(result.stderr)


        except subprocess.CalledProcessError as e:
            print(f"compute_H failed for {run_name}")
            print(e.stderr)
            continue

        # Parse output
        H_vals = {"run_name": run_name}

        for line in result.stdout.strip().splitlines():
            if "," not in line:
                continue
            key, val = line.split(",", 1)
            H_vals[key.strip()] = float(val)

        # Ensure all components exist
        if not all(k in H_vals for k in ("HP", "HC", "HD", "HB")):
            print(f"Incomplete H vector for {run_name}, skipping")
            continue

        rows.append(H_vals)

    # Write CSV
    if not rows:
        print("No valid H vectors collected")
        return

    fieldnames = ["run_name", "HP", "HC", "HD", "HB"]

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} H vectors to {output_path}")

#------------------------------------------------------------
# CONFIGURE INDIVIDUAL RUN DETAILS IN THE BLOCK BELOW
# Guide:
# - Set the variables below to configure the set of MCMC_SA runs
# - Ensure that l_max+k <1.0
# - k around 0.45 works well, but it would be good to experiment with how low we can go
# - In order to run for different seat configurations, simply rerun with a different seat_config list. The output H_summary.csv files will be distinct, but can easily be manually combined to produce combined plots. Remember that it is only sensible to compare runs with the same len(seat_config).
# - All of the below lines marked with "---ACTUAL" relate to preparing and plotting the actual configuration, and need only be run once per area.
#------------------------------------------------------------   

ed_data = r"data\ED_data.csv"
area_str= ["DUBLIN"] # Allcaps county name(s)
recorded= 1000
discarded=600
seat_config= [3,3,3,4,4,4,4,4,5,5,5,5] # The seat config to be used for the MCMC_SA runs
actual_seat_config = [3,3,3,4,4,4,4,4,5,5,5,5]  # This is [3,3,4,5,5] for Cork and [3,3,3,4,4,4,4,4,5,5,5,5] for Dublin  # ---ACTUAL
l_min=0.0 # Relative strength of compactness coupling. Thus l+k<1, and 1-(l+k) is the relative strength of population coupling.
l_max=0.4
n_runs= 3
k=0.45 # Relative strength of contiguity coupling

#------------------------------------------------------------

d_min= l_min*(1+ (k/(1+k)))*(1/(1-l_min*(1+ k/(1-k)))) # Strength of compactness coupling
d_max= l_max*(1+ (k/(1+k)))*(1/(1-l_max*(1+ k/(1-k))))
county_str = ",".join(area_str)
actual_name = (f"@{dt_short}_"+f"{county_str}_actual")  # ---ACTUAL
actual_dir = os.path.join("data", actual_name)  # ---ACTUAL



ac_map_cmd = ["python3","code/map_plot.py",actual_name]  # ---ACTUAL
prepare_actual_configuration(actual_name, area_str)  # ---ACTUAL
write_actual_configs_csv(actual_dir, actual_seat_config, ed_data)  # ---ACTUAL
subprocess.run(ac_map_cmd, check=True)  # ---ACTUAL

run_names= run_all_MCMC_SA(area_str, recorded, discarded, seat_config, d_min, d_max, n_runs, k)
run_names = [r for r in run_names if r is not None]

run_names.insert(0, actual_name)  # ---ACTUAL
collect_H_vectors(run_names, seat_config)
