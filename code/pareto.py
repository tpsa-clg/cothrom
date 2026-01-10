import subprocess
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List
import csv
import os
from datetime import datetime

# datetime object containing current date and time
now = datetime.now()
dt_string = now.strftime("%d.%m.%Y_%H.%M")


def run_all_MCMC_SA(
    county_list: List[str],
    recorded: int,
    discarded: int,
    seat_config: str,
    d_min: float,
    d_max: float,
    n_runs: int,
    k: float,
):
    """
    Run multiple MCMC_SA instances in parallel, parameterised by d_i.

    Parameters
    ----------
    county_list : list[str]
        List of county names (e.g. ["Cork", "Kerry"])
    recorded : int
        Number of recorded MCMC steps
    discarded : int
        Number of discarded (thermalisation) steps
    seat_config : str
        Seat configuration, e.g. "3,3,4,5,5"
    d_min : float
        Minimum value of d
    d_max : float
        Maximum value of d
    n_runs : int
        Number of runs (number of d_i values)
    k : float
        Universal coupling parameter capturing relative contiguity coupling.
    """

    # ------------------------------------------------------------
    # Construct d_i values
    # ------------------------------------------------------------
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

    # ------------------------------------------------------------
    # Function that runs ONE MCMC_SA instance
    # ------------------------------------------------------------
    def run_single(d_i: float):
        """
        Run txt_for_MCMC.py followed by MCMC_SA for a single d_i.
        """

        try:
            Jc = k * (1.0 + d_i) / (1.0 - k)
            Jd = d_i
            Jb = 0.0

            coupling_str = f"{Jc},{Jd},{Jb}"

            # Construct run name
            run_name = (
                f"{county_str}"
                f"_d_{d_i:.3f}"
                f"_k_{k:.3f}"
                f"_R_{recorded}"
                f"_D_{discarded}"
                f"_s_{seat_config.replace(',', '-')}"
            )

            # --------------------------------------------------------
            # 1) Generate txt files for MCMC
            # --------------------------------------------------------
            cmd_txt = [
                "python3",
                "code/txt_for_MCMC.py",
                "County",
                county_str,
                run_name,
            ]

            subprocess.run(cmd_txt, check=True)

            # --------------------------------------------------------
            # 2) Run MCMC_SA
            # --------------------------------------------------------
            cmd_mcmc = [
                "code/MCMC_SA",
                run_name,
                seat_config,
                coupling_str,
                f"{recorded},{discarded}",
            ]

            subprocess.run(cmd_mcmc, check=True)

            return run_name
        
        except subprocess.CalledProcessError as e:
            print(f"Run {run_name} failed: {e}")
            return None

    # ------------------------------------------------------------
    # Run everything in parallel
    # ------------------------------------------------------------
    run_names = []

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(run_single, d_i) for d_i in d_vals]

        for future in as_completed(futures):
            run_name = future.result()
            run_names.append(run_name)
            print(f"Completed run: {run_name}")

    return run_names




def collect_H_vectors(
    runs: List[str],
    seat_config: str,
    data_dir: str = "data",
    output_file: str = "H_summary_" +dt_string+".csv",
):
    """
    Compute and collect H-vectors for a list of MCMC_SA runs.

    Parameters
    ----------
    runs : list[str]
        Names of run directories (produced by MCMC_SA)
    seat_config : str
        Seat configuration, e.g. "3,3,4,5,5"
    data_dir : str
        Path to data directory
    output_file : str
        Name of CSV file to write inside data_dir
    """

    output_path = os.path.join(data_dir, output_file)
    rows = []

    for run_name in runs:
        cfg_path = os.path.join(data_dir, run_name, "configs.csv")
        area_dir = os.path.join(data_dir, run_name)
        
        if not os.path.exists(cfg_path):
            print(f"Missing configs.csv for run {run_name}, skipping")
            continue

        # --------------------------------------------------------
        # Run compute_H
        # --------------------------------------------------------
        # Prefer explicit Windows executable name to avoid ambiguous resolution
        compute_exe = os.path.join("code", "compute_H.exe")
        if not os.path.exists(compute_exe):
            compute_exe = os.path.join("code", "compute_H")

        # Extract the configuration line from configs.csv and pass it inline to compute_H
        cfg_arg_to_pass = None
        try:
            with open(cfg_path, 'r', encoding='utf-8') as cf:
                lines = [ln.strip() for ln in cf.readlines()]
            # prefer 'optimals' block
            cfg_line = None
            for i, l in enumerate(lines):
                if l == 'optimals':
                    j = i + 1
                    while j < len(lines) and lines[j] == '':
                        j += 1
                    if j < len(lines):
                        cfg_line = lines[j]
                        break
            if cfg_line is None:
                for l in lines:
                    if l:
                        cfg_line = l
                        break
            if cfg_line:
                cfg_arg_to_pass = cfg_line
        except Exception as e:
            print(f"Failed to read configs.csv for run {run_name}: {e}")

        # Log executable info for debugging silent runs
        try:
            exe_stat = os.stat(compute_exe)
            print(f"Invoking compute_H executable: {compute_exe} (size={exe_stat.st_size})")
        except Exception:
            print(f"Invoking compute_H executable: {compute_exe} (stat failed)")

        # # If we successfully extracted the config line, pass it inline (compute_H will parse comma-list fallback)
        third_arg = cfg_arg_to_pass if cfg_arg_to_pass is not None else cfg_path

        cmd = [
            compute_exe,
            run_name,          # pass the run folder name (area) so compute_H looks under data/<run_name>/
            seat_config,
            third_arg,         # either inline comma list or path
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
        print("seat_config:", seat_config)
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

        # --------------------------------------------------------
        # Parse output
        # --------------------------------------------------------
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

    # ------------------------------------------------------------
    # Write CSV
    # ------------------------------------------------------------
    if not rows:
        print("No valid H vectors collected")
        return

    fieldnames = ["run_name", "HP", "HC", "HD", "HB"]

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} H vectors to {output_path}")

area_str= ["CORK"]
recorded= 100
discarded=10
seat_config= "3,3,4,5,5"
l_min=0.1 # Relative strength of compactness coupling
l_max=0.7
k=0.2 # Relative strength of contiguity coupling
d_min= l_min*(1+ (k/(1+k)))*(1/(1-l_min*(1- k/(1-k)))) # Strength of compactness coupling
d_max= l_max*(1+ (k/(1+k)))*(1/(1-l_max*(1- k/(1-k))))
n_runs= 7

run_names= run_all_MCMC_SA(area_str, recorded, discarded, seat_config, d_min, d_max, n_runs, k)
run_names = [r for r in run_names if r is not None]
#collect_H_vectors(["CORK_d_0.700_k_0.500_R_100_D_10_s_3-3-4-5-5"], seat_config)
collect_H_vectors(run_names, seat_config)