import csv
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import sys
import re
import string
import os
from itertools import cycle


labels = False  # Set to True to enable point labelling, to help with identifying points
translucents = True # Set to True to make noncontiguous points translucent, False for invisible

def extract_d(run_name: str) -> float:
    m = re.search(r"_d_([0-9]*\.?[0-9]+)", run_name)
    if m is None:
        return float(-1.0)
    return float(m.group(1))


def extract_s_sequence(run_name: str) -> str: # Extract seating arrangement, if no _s_ conclude actual config
    m = re.search(r"_s_([0-9\-]+)", run_name)
    if m is None:
        return "Actual Configuration"
    return m.group(1)


def plot_HP_vs_HD_labeled(csv_path: str):
    rows = []

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "run_name": row["run_name"],
                "d": extract_d(row["run_name"]),
                "s_seq": extract_s_sequence(row["run_name"]),
                "HP": float(row["HP"]),
                "HD": float(row["HD"]),
                "HC": float(row["HC"]),
            })

    # Assign colours per unique _s_ sequence
    unique_sequences = sorted({r["s_seq"] for r in rows}) # A
    colour_cycle = cycle(plt.rcParams["axes.prop_cycle"].by_key()["color"])
    seq_to_colour = {seq: next(colour_cycle) for seq in unique_sequences}


    plt.figure()
    labelled_points = set()
    label_idx = 0

    for r in rows:
        color = seq_to_colour[r["s_seq"]]
        alpha = 1.0 if abs(r["HC"]) < 1e-12 else 0.2 if translucents else 0.0

        plt.scatter(
            r["HP"],
            r["HD"],
            c=color,
            alpha=alpha,
        )

        if labels == True:
            key = (round(r["HP"], 8), round(r["HD"], 8))

            plt.text(
                r["HP"],
                r["HD"],
                label_idx,
                fontsize=5,
                ha="left",
                va="bottom",
            )

            labelled_points.add(key)
            label_idx += 1

    
    legend_handles = []

    for seq, color in seq_to_colour.items():
        legend_handles.append(
            Line2D(
                [0],
                [0],
                marker="o",
                linestyle="None",
                markerfacecolor=color,
                markeredgecolor=color,
                markersize=8,
                label=seq,
            )
        )

    plt.legend(
        handles=legend_handles,
        title="SA solutions by #3-#4-#5 seaters",
        loc="upper right",
        frameon=True,
    )


    plt.xlabel("HP")
    plt.ylabel("HD")
    plt.title("Pareto plot: HP vs HD")
    plt.grid(False)
    plt.tight_layout()

    pdf_path = os.path.splitext(csv_path)[0] + "_HP_vs_HD.pdf"
    plt.savefig(pdf_path)
    plt.close()

    print(f"Saved plot to {pdf_path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python plot_pareto.py data/@<datetime>MCDA_input.csv")
        sys.exit(1)

    plot_HP_vs_HD_labeled(sys.argv[1])

